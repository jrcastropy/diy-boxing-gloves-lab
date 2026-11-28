"""Build a cutting-machine DXF of the leather pieces (Silhouette Cameo 4 Plus).

Step 1 (clean): keep only the five leather pieces, and from each only its outer
cut line and its real holes. Inner lines, the palm's dash marks and the
outlined letters are removed. Pieces stay where they are on the sheet. Each
piece (outline and holes) is put on its own layer, named after the piece.

Step 2 (split-chone): the Chone (12.20" x 15.37") fits neither mat, so it is cut
along a straight line from the thumb notch to the corner where the bottom edge
starts. Both parts get a 5 mm strip added along the cut for the join. At each
end of the cut the piece's own edge is carried on straight to the strip's
outer line if it meets the cut steeply (the body's bottom edge), else the strip
has a square end. Layers: chone-body (keeps the Chone's hole) and chone-thumb. The parts are
written as closed polylines; everything else is copied unchanged.

Usage:
  python scripts/leather_cut.py clean dxf/latest.dxf "dxf/<new name>.dxf"
  python scripts/leather_cut.py split-chone "dxf/<step 1>.dxf" "dxf/<new name>.dxf"
  python scripts/leather_cut.py render "dxf/<leather cut>.dxf" renders/<folder>
    (one PNG per layer, i.e. per piece)
Both refuse to overwrite.
"""
import sys
from pathlib import Path

import ezdxf
from ezdxf import bbox

from render_pieces import PIECES, center, inside, poly

LEATHER = ["front-palm", "chone", "chone-cuff", "thumb", "thumb-panel"]
# Outer cut line of each leather piece (PIECES also lists the palm's inner line).
OUTER = {"front-palm": "2EE", "chone": "95", "chone-cuff": "310", "thumb": "32E", "thumb-panel": "367"}
# Holes are drawn as small round 13-point splines about 0.115" across.
HOLE_SIZE = (0.10, 0.13)
MM = 1 / 25.4
SPLIT_ALLOWANCE = 5 * MM
# A strip end carries the piece's edge on only if that takes at most this many
# allowances (edge meets the cut at 53 degrees or more); otherwise square end.
MAX_EXTEND = 1.25


def is_hole(e):
    if e.dxftype() != "SPLINE" or not e.closed or len(e.control_points) != 13:
        return False
    b = bbox.extents([e])
    w, h = b.extmax.x - b.extmin.x, b.extmax.y - b.extmin.y
    return all(HOLE_SIZE[0] <= s <= HOLE_SIZE[1] for s in (w, h))


def clean(src, dst):
    if Path(dst).exists():
        sys.exit(f"{dst} exists, not overwriting")
    doc = ezdxf.readfile(src)
    msp = doc.modelspace()
    keep, report = set(), {}
    for name in LEATHER:
        outlines = [poly(doc.entitydb[h]) for h in PIECES[name]]
        holes = [e.dxf.handle for e in msp
                 if is_hole(e) and any(inside(center(e)[0], o) for o in outlines)]
        doc.layers.add(name)
        for h in (OUTER[name], *holes):
            doc.entitydb[h].dxf.layer = name
        keep |= {OUTER[name], *holes}
        report[name] = len(holes)
    for e in list(msp):
        if e.dxf.handle not in keep:
            msp.delete_entity(e)
    doc.saveas(dst)
    for name, n in report.items():
        print(f"{name}: outer line + {n} holes")


def dist(p, q):
    return ((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2) ** 0.5


def split_chone(src, dst):
    from shapely.geometry import LineString, Point, Polygon
    from shapely.ops import split

    if Path(dst).exists():
        sys.exit(f"{dst} exists, not overwriting")
    doc = ezdxf.readfile(src)
    msp = doc.modelspace()
    ents = [e for e in msp if e.dxf.layer == "chone"]
    outline = next(e for e in ents if not is_hole(e))
    holes = [e for e in ents if is_hole(e)]
    pts = poly(outline)
    x0 = min(x for x, _ in pts)
    y0 = min(y for _, y in pts)
    # Corner where the bottom edge starts: leftmost point on the bottom edge.
    corner = min((q for q in pts if q[1] < y0 + 0.01), key=lambda q: q[0])
    # Thumb notch: the furthest-right point of the thumb's upper edge, i.e. the
    # inside corner between thumb and body (4-7" up, left of the bottom edge).
    notch = max((q for q in pts if 4 < q[1] - y0 < 7 and q[0] < corner[0]), key=lambda q: q[0])
    dx, dy = corner[0] - notch[0], corner[1] - notch[1]
    length = (dx * dx + dy * dy) ** 0.5
    ux, uy = dx / length, dy / length
    nx, ny = -uy, ux  # unit normal, pointing to the body side
    cut = LineString([(notch[0] - ux * .2, notch[1] - uy * .2), (corner[0] + ux * .2, corner[1] + uy * .2)])
    thumb, body = sorted(split(Polygon(pts).buffer(0), cut).geoms, key=lambda g: g.area)

    a = SPLIT_ALLOWANCE

    def off_cut(q):
        """How far q is from the cut line (+ on the body side)."""
        return (q[0] - notch[0]) * nx + (q[1] - notch[1]) * ny

    def strip_end(part, end, s):
        """Where the 5 mm strip ends, at one end of the cut, for a part whose
        strip goes to side s (+1 body side, -1 thumb side).

        The part's own edge arriving at this end is carried on in a straight
        line until it meets the strip's outer line, so the outline runs on with
        no step. If that edge points away from the strip, or would need more
        than MAX_EXTEND x the allowance to get there, the strip gets a square end."""
        square = (end[0] + nx * a * s, end[1] + ny * a * s)
        ring = list(part.exterior.coords)[:-1]
        i = min(range(len(ring)), key=lambda k: dist(ring[k], end))
        # Walk away from `end` along the part's outline, on the side that
        # isn't the cut, to the first point 0.1" away: the edge's direction.
        for step in (1, -1):
            nxt = ring[(i + step) % len(ring)]
            if abs(off_cut(nxt)) > 1e-6:
                break
        k = i
        while dist(ring[k % len(ring)], end) < 0.1 and abs(k - i) < len(ring):
            k += step
        q = ring[k % len(ring)]
        d = ((end[0] - q[0]) / dist(q, end), (end[1] - q[1]) / dist(q, end))
        along = (d[0] * nx + d[1] * ny) * s  # how fast the edge moves toward the strip's outer line
        if along <= 0 or 1 / along > MAX_EXTEND:
            return square
        t = a / along
        return (end[0] + d[0] * t, end[1] + d[1] * t)

    def allowance(part, s):
        ends = [strip_end(part, corner, s), strip_end(part, notch, s)]
        return part.union(Polygon([notch, corner, *ends]).buffer(1e-9))

    parts = {"chone-thumb": allowance(thumb, +1), "chone-body": allowance(body, -1)}
    for name, g in parts.items():
        doc.layers.add(name)
        g = g.simplify(0.001)
        msp.add_lwpolyline(list(g.exterior.coords)[:-1], close=True, dxfattribs={"layer": name})
        b = g.bounds
        print(f"{name}: {b[2] - b[0]:.2f} x {b[3] - b[1]:.2f} in")
    for h in holes:
        h.dxf.layer = "chone-body" if body.contains(Point(center(h)[0])) else "chone-thumb"
    msp.delete_entity(outline)
    doc.saveas(dst)
    print(f"cut line {length:.2f} in, notch ({notch[0] - x0:.2f}, {notch[1] - y0:.2f}), "
          f"corner ({corner[0] - x0:.2f}, {corner[1] - y0:.2f}) from the Chone's bottom-left")


def render_each(src, outdir):
    """One PNG per piece (per layer): its outline and holes, nothing around it."""
    from render_pieces import render

    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    doc = ezdxf.readfile(src)
    layers = {}
    for e in doc.modelspace():
        layers.setdefault(e.dxf.layer, []).append(e)
    for name, ents in layers.items():
        out = outdir / f"{name}.png"
        if out.exists():
            sys.exit(f"{out} exists, not overwriting")
        b = bbox.extents(ents)
        m = 0.25
        render(doc, {e.dxf.handle for e in ents},
               (b.extmin.x - m, b.extmax.x + m, b.extmin.y - m, b.extmax.y + m), out)
        print(f"{out}: {b.extmax.x - b.extmin.x:.2f} x {b.extmax.y - b.extmin.y:.2f} in")


if __name__ == "__main__":
    step, src, dst = sys.argv[1:4]
    {"clean": clean, "split-chone": split_chone, "render": render_each}[step](src, dst)
