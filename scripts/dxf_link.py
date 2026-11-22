"""Link viewer items to the DXF piece they came from.

The Chone Fit Lab (viewer/chone-fit-lab.html) keeps, for every item, which DXF piece it is and how it was laid out,
plus the piece's outline as a chain of cubic Béziers (so the Edit pattern tab can reshape it and save it back):

  source = { file: "dxf/<name>.dxf" (from the repo root), handle, unit (inches per drawing unit),
             mirror, rot (radians), ox, oy }   DXF point * unit -> (mirror x) -> turned by rot -> moved by (ox, oy)
  path   = { anch: false, segs: [{ kind: "orig", bz: chain, corner: false }], base: chain }
           chain = [[p0, c1, c2, p3], ...] in the item's own frame, counter-clockwise

A DXF SPLINE splits exactly into cubic Béziers, so the chain is the DXF curve itself. find_source() works out which
piece an item's outline is (and the mirror / turn / shift) by laying each same-size DXF piece onto it.
"""
import math
from pathlib import Path

import ezdxf
import numpy as np
from ezdxf import path as ezpath
from scipy.optimize import minimize
from scipy.spatial import cKDTree
from shapely.geometry import Polygon

REPO = Path(__file__).resolve().parent.parent
INCH = {0: 1, 1: 1, 2: 12, 4: 1 / 25.4, 5: 10 / 25.4, 6: 1000 / 25.4}  # $INSUNITS -> inches per drawing unit


def unit_of(doc):
    return INCH.get(doc.header.get("$INSUNITS", 1), 1)


def flat(e, unit):
    return np.array([(p.x * unit, p.y * unit) for p in ezpath.make_path(e).flattening(0.005)])


def entity_chain(e, unit):
    """The piece's outline as cubic Béziers in inches (exact for non-rational splines and straight lines)."""
    chain = []
    if e.dxftype() == "SPLINE":
        bs = e.construction_tool()
        if not bs.is_rational and bs.degree <= 3:
            for s in bs.bezier_decomposition():
                p = [(v.x * unit, v.y * unit) for v in s]
                if bs.degree == 3:
                    chain.append(p)
                elif bs.degree == 2:
                    chain.append([p[0], lerp(p[0], p[1], 2 / 3), lerp(p[2], p[1], 2 / 3), p[2]])
                else:
                    chain.append(line(p[0], p[1]))
    if not chain:  # polylines, arcs, circles: ezdxf's path (straight lines and cubic curves; arcs as cubics)
        pth, at = ezpath.make_path(e), None
        at = (pth.start.x * unit, pth.start.y * unit)
        for c in pth.commands():
            end = (c.end.x * unit, c.end.y * unit)
            if c.type == ezpath.Command.LINE_TO:
                chain.append(line(at, end))
            elif c.type == ezpath.Command.CURVE4_TO:
                chain.append([at, (c.ctrl1.x * unit, c.ctrl1.y * unit), (c.ctrl2.x * unit, c.ctrl2.y * unit), end])
            elif c.type == ezpath.Command.CURVE3_TO:
                q = (c.ctrl.x * unit, c.ctrl.y * unit)
                chain.append([at, lerp(at, q, 2 / 3), lerp(end, q, 2 / 3), end])
            at = end
        if np.hypot(at[0] - chain[0][0][0], at[1] - chain[0][0][1]) > 1e-7:
            chain.append(line(at, chain[0][0]))  # closed polyline: the closing side
    if not chain:  # anything else: its traced points joined by straight lines
        pts = flat(e, unit)
        chain = [line(pts[k], pts[(k + 1) % len(pts)]) for k in range(len(pts))]
    chain = [b for b in chain if np.ptp(np.array(b), axis=0).max() > 1e-7]
    chain[-1][3] = chain[0][0]
    return chain


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def line(a, b):
    return [tuple(a), lerp(a, b, 1 / 3), lerp(a, b, 2 / 3), tuple(b)]


def xf(m, pts):
    """DXF inches -> the item's frame."""
    pts = np.asarray(pts, float)
    x = -pts[..., 0] if m["mirror"] else pts[..., 0]
    c, s = math.cos(m["rot"]), math.sin(m["rot"])
    return np.stack([x * c - pts[..., 1] * s + m["ox"], x * s + pts[..., 1] * c + m["oy"]], -1)


def placed_path(chain, m):
    ch = xf(m, np.array(chain))
    pts = np.concatenate([b[:3] for b in ch])
    if Polygon(pts).exterior.is_ccw is False:
        ch = ch[::-1, ::-1]
    ch = [[[round(float(x), 6), round(float(y), 6)] for x, y in b] for b in ch]
    return {"anch": False, "segs": [{"kind": "orig", "bz": ch, "corner": False}], "base": ch}


def fit(ring, Q, mirror, allow_turn):
    """Best mirror/turn/shift laying DXF points Q onto the item outline `ring`: (m, largest leftover distance)."""
    R = np.asarray(ring, float)
    Qd = np.array(Polygon(Q).exterior.segmentize(0.01).coords)
    rc = np.array(Polygon(R).centroid.coords[0])
    best = None
    for r0 in (range(-30, 31, 3) if allow_turn else [0]):
        def place(p):
            m = {"mirror": mirror, "rot": p[0], "ox": 0.0, "oy": 0.0}
            P = xf(m, Qd)
            c = np.array(Polygon(P).centroid.coords[0])
            m["ox"], m["oy"] = rc[0] - c[0] + p[1], rc[1] - c[1] + p[2]
            return m
        def cost(p):
            m = place(p)
            return cKDTree(xf(m, Qd)).query(R)[0].mean()
        x0 = [math.radians(r0), 0, 0]
        res = minimize(cost, x0, method="Nelder-Mead", options={"xatol": 1e-9, "fatol": 1e-10, "maxiter": 2000}) if allow_turn else \
            minimize(lambda p: cost([0, p[0], p[1]]), [0, 0], method="Nelder-Mead", options={"xatol": 1e-9, "fatol": 1e-10})
        p = res.x if allow_turn else [0, *res.x]
        if best is None or res.fun < best[1]:
            best = (p, res.fun)
    m = place(best[0])
    err = cKDTree(xf(m, Qd)).query(R)[0].max()
    m = {"mirror": bool(m["mirror"]), "rot": float(m["rot"]), "ox": float(m["ox"]), "oy": float(m["oy"])}
    return m, err


def find_source(ring, files, allow_turn=False, tol=0.01):
    """The first of `files` (DXF paths, repo-relative) holding a piece that is exactly the item's outline.
    Returns (source, path) or None."""
    A = Polygon(ring).area
    for f in files:
        doc = ezdxf.readfile(REPO / f)
        unit = unit_of(doc)
        for e in doc.modelspace():
            if e.dxftype() not in ("SPLINE", "LWPOLYLINE", "POLYLINE", "CIRCLE"):
                continue
            try:
                Q = flat(e, unit)
                if len(Q) < 8 or abs(Polygon(Q).area - A) > 0.02 * A:
                    continue
            except Exception:
                continue
            for mirror in (False, True):
                m, err = fit(ring, Q, mirror, allow_turn)
                if err <= tol:
                    src = {"file": str(f), "handle": e.dxf.handle, "unit": unit, **m}
                    return src, placed_path(entity_chain(e, unit), src)
    return None
