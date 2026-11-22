"""Export the Chone and the foam moulds as flat triangle meshes for the 3D viewer.

Everything is in inches, in the Chone's frame: x across, y from the wrist to the
fingertips, origin at the middle of the Chone stitch line's bottom (wrist) edge.
Mould 1 is flipped and placed inside the Chone where the gap is most even;
Mould 2 is placed inside Mould 1 the same way.

Usage: uv run --with ezdxf --with shapely --with scipy python scripts/export_3d.py \
       "dxf/Laces Boxing 14OZ (1).dxf" viewer/glove-data.js
"""
import json, math, sys
import ezdxf, numpy as np, shapely
from shapely.geometry import Polygon, MultiPoint, Point
from shapely import affinity
from shapely.geometry.polygon import orient
from scipy.optimize import minimize
from render_pieces import poly
from join_chone_cuff import horizontal_edge

doc = ezdxf.readfile(sys.argv[1]); db = doc.entitydb
P = lambda h: Polygon(poly(db[h]))
co, ci = P("95"), P("96")
bx0, bx1, by = horizontal_edge(db["96"], "bottom")
ORIGIN = ((bx0 + bx1) / 2, by)
m1 = affinity.scale(P("320"), -1, 1, origin="centroid")
m2f = affinity.scale(P("2FE"), -1, 1, origin="centroid")
m2u = P("2FE")

def samples(g, n): return [g.exterior.interpolate(t, normalized=True) for t in np.linspace(0, 1, n, endpoint=False)]

def fit(outer, m, turns):
    pts = samples(outer, 300)
    def place(p):
        g = affinity.rotate(m, p[0], origin="centroid")
        return affinity.translate(g, outer.centroid.x - m.centroid.x + p[1], outer.centroid.y - m.centroid.y + p[2])
    def cost(p):
        g = place(p)
        return np.std([g.exterior.distance(q) * (-1 if g.contains(q) else 1) for q in pts])
    best = min((minimize(cost, [r, 0, 0], method="Nelder-Mead") for r in turns), key=lambda r: r.fun)
    return place(best.x), best.fun, best.x

g1, _, x1 = fit(ci, m1, range(-20, 25, 5))
g2, _, x2, m2 = min((fit(g1, c, range(-180, 180, 20)) + (c,) for c in (m2f, m2u)), key=lambda r: r[1])

# How each piece was laid out, as the viewer's item link (dxf_link.py): DXF point -> (mirror x) -> turned -> moved.
def link(h, mirrored, outer=None, m=None, x=None):
    if outer is None: return dict(mirror=False, rot=0.0, ox=-ORIGIN[0], oy=-ORIGIN[1])  # the Chone: only moved
    a = np.radians(x[0]); R = np.array([[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]])
    mc = np.array(m.centroid.coords[0]); tr = np.array([outer.centroid.x - m.centroid.x + x[1], outer.centroid.y - m.centroid.y + x[2]])
    f0 = np.array([2 * P(h).centroid.x, 0.0]) if mirrored else np.zeros(2)  # mirrored about the piece's own centre
    o = R @ (f0 - mc) + mc + tr - np.array(ORIGIN)
    return dict(mirror=mirrored, rot=float(a), ox=float(o[0]), oy=float(o[1]))
LINKS = {"chone": ("95", link("95", False)), "mould1": ("320", link("320", True, ci, m1, x1)),
         "mould2": ("2FE", link("2FE", m2 is m2f, g1, m2, x2))}

def to_frame(g): return affinity.translate(g, -ORIGIN[0], -ORIGIN[1])

def ring(g, step):
    g = orient(g)  # counter-clockwise
    L = g.exterior.length; n = int(L / step)
    return [g.exterior.interpolate(t, normalized=True).coords[0] for t in np.linspace(0, 1, n, endpoint=False)]

def mesh(g, step=0.12, grid=0.2):
    b = ring(g, step)
    inner = g.buffer(-grid * 0.45)
    x0, y0, x1, y1 = g.bounds
    gp = [(x, y) for x in np.arange(x0, x1, grid) for y in np.arange(y0, y1, grid) if inner.contains(Point(x, y))]
    pts = b + gp
    index = {p: i for i, p in enumerate(pts)}
    tris = []
    tol = g.buffer(1e-4)
    for t in shapely.delaunay_triangles(MultiPoint(pts)).geoms:
        if t.area < 1e-6 or not tol.contains(t): continue
        c = list(t.exterior.coords)[:3]
        ids = [index.get(p) for p in c]
        if None in ids: continue
        # counter-clockwise
        (ax, ay), (bx, by_), (cx, cy) = c
        if (bx - ax) * (cy - ay) - (by_ - ay) * (cx - ax) < 0: ids = [ids[0], ids[2], ids[1]]
        tris.append(ids)
    r = lambda v: round(v, 4)
    return dict(verts=[[r(x), r(y)] for x, y in pts], tris=tris, nBoundary=len(b))

out = dict(
    units="inch",
    chone=mesh(to_frame(co)) | dict(stitch=[[round(x, 4), round(y, 4)] for x, y in ring(to_frame(ci), 0.1)]),
    mould1=mesh(to_frame(g1)),
    mould2=mesh(to_frame(g2)),
)
# Thumb notch tip on the Chone cut line (rightmost point of the notch)
ro = np.array(ring(to_frame(co), 0.02))
sel = ro[(ro[:, 1] > 4.6) & (ro[:, 1] < 5.8) & (ro[:, 0] > -4.6) & (ro[:, 0] < -3.2)]
out["landmarks"] = dict(thumbNotch=[round(float(v), 4) for v in sel[sel[:, 0].argmax()]])
print("thumb notch", out["landmarks"])
for k in ("chone", "mould1", "mould2"):
    v = np.array(out[k]["verts"]); print(k, len(v), "verts", len(out[k]["tris"]), "tris", "bounds", v.min(0).round(2), v.max(0).round(2))
ch = to_frame(ci); 
print("chone stitch bounds", np.round(ch.bounds, 2))
# Each piece's DXF link and its outline as Béziers, for the viewer's Edit pattern tab (see dxf_link.py)
from pathlib import Path
from dxf_link import REPO, entity_chain, flat, placed_path, unit_of, xf
rel = str(Path(sys.argv[1]).resolve().relative_to(REPO)); unit = unit_of(doc)
for k, (h, m) in LINKS.items():
    src = {"file": rel, "handle": h, "unit": unit, **m}
    curve = Polygon(xf(src, flat(db[h], unit))).exterior  # the viewer's outline points must lie on the linked DXF curve
    err = max(curve.distance(Point(q)) for q in out[k]["verts"][:out[k]["nBoundary"]])
    if err > 0.01: sys.exit(f"{k}: the link doesn't reproduce the piece (off by {err:.3f} in)")
    out[k]["source"], out[k]["path"] = src, placed_path(entity_chain(db[h], unit), src)
    print(k, "is piece", h, "mirrored" if m["mirror"] else "as drawn", f"turned {math.degrees(m['rot']):.3f} deg; link reproduces it within {err:.4f} in")
open(sys.argv[2], "w").write("window.GLOVE_DATA = " + json.dumps(out, separators=(",", ":")) + ";\n")
