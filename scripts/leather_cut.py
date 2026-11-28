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
has a square end. Layers: chone-body (keeps the Chone's hole) and chone-thumb.
The parts are written as closed polylines; everything else is copied unchanged.

Step 3 (join-edges): 5 mm added below the Chone body's bottom edge and above the
Chone Cuff's top edge, so the two butt together with the margin that used to be
added by hand when tracing. The added strip has straight up-and-down sides, so
both edges keep their length. The Cuff is rewritten as a closed polyline.

Step 4 (trim-cuff): the Cuff's bottom is cut straight across so it lines up with
the Front Palm's bottom edge in the finished glove. The placement comes from the
reference pattern (normally dxf/latest.dxf), the same rule as overlay_palm.py:
the Cuff's top outer line on the Chone's bottom inner line, and the palm's lower
thumb-notch corner on the left end of that join.

Layout (layout): lays the pieces out on cutting mats of a given size and writes
one DXF per mat. No mat border is drawn. Pieces stay EDGE_MARGIN (10 mm) inside
the mat's edges. Each mat's design is then moved so its top-left is 10 mm in from
the mat's top-left, i.e. top edge at y = -10 mm, left edge at x = 10 mm (see
Studio top below). Largest piece first, each goes as low, then as far left, as it fits on
the first mat with room, LAYOUT_GAP (10 mm) apart. Pieces turn only in 90-degree steps (so
they keep their direction on the hide), except where TILT says otherwise: on
the 14" x 15" mat the Chone body only fits tilted 41 degrees (about 1 mm spare).
It also draws a preview PNG of each mat as Silhouette Studio shows it (y down
from the mat's top), with the 10 mm edge margin dashed in red.
Given a list of pieces and a label, it lays out only those, on one mat (used to
put each leather colour on its own mat); if they don't fit largest-first, it
tries every placing order and rotation.

Studio top (studio-top): moves a laid-out DXF, without changing shapes or size,
so its top edge is at y = 0 and its left edge at x = 0 (or an optional margin
in from both); the design then runs down to negative y. Silhouette Studio counts y downward from the page's top
(Studio y = -DXF y), so with its Import preference set to "As is" the design
opens on the mat, top-left at the page's top-left. A design with its bottom at
y = 0 opens entirely above the mat.

Usage:
  python scripts/leather_cut.py clean dxf/latest.dxf "dxf/<new name>.dxf"
  python scripts/leather_cut.py split-chone "dxf/<step 1>.dxf" "dxf/<new name>.dxf"
  python scripts/leather_cut.py join-edges "dxf/<step 2>.dxf" "dxf/<new name>.dxf"
  python scripts/leather_cut.py trim-cuff "dxf/<step 3>.dxf" "dxf/<new name>.dxf" dxf/latest.dxf
  python scripts/leather_cut.py layout "dxf/Laces Boxing 14OZ - leather cut - step4 cuff bottom trimmed to palm.dxf" 14 15
    (writes "dxf/Laces Boxing 14OZ - leather cut - 14x15 mat <n> of <m> - studio top 10mm edge 10mm gap.dxf"
    and renders/leather-cut-mat14x15-mat<n>-10mm-edge-10mm-gap.png)
  python scripts/leather_cut.py layout "dxf/<step 4>.dxf" 12 24 chone-body,chone-cuff,chone-thumb,thumb-panel "chone colour"
    (only those pieces, all on one mat: "dxf/... leather cut - chone colour 12x24 - studio top 10mm edge 10mm gap.dxf"
    and renders/leather-cut-chone-colour-12x24-10mm-edge-10mm-gap.png)
  python scripts/leather_cut.py studio-top "dxf/<mat file>.dxf" "dxf/<new name>.dxf" [margin mm, default 0]
  python scripts/leather_cut.py render "dxf/<leather cut>.dxf" renders/<folder>
    (one PNG per layer, i.e. per piece)
All refuse to overwrite.
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
JOIN_ALLOWANCE = 5 * MM
# Layer -> which flat edge gets the join allowance (-1 bottom, +1 top).
JOIN_EDGES = {"chone-body": -1, "chone-cuff": +1}
LAYOUT_GAP = 10 * MM
# Clear space kept between every piece and the mat's edges.
EDGE_MARGIN = 10 * MM
LAYOUT_STEP = 0.05  # search grid, inches
# Mat size -> {piece: allowed rotations} where a piece may not use 0/90/180/270.
TILT = {(14.0, 15.0): {"chone-body": [41.0]}}
PIECE_COLOURS = {"chone-body": "#333", "chone-thumb": "#777", "front-palm": "#c33",
                 "chone-cuff": "#25c", "thumb": "#2a7", "thumb-panel": "#a5c"}


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


def join_edges(src, dst):
    from shapely.geometry import Polygon

    if Path(dst).exists():
        sys.exit(f"{dst} exists, not overwriting")
    doc = ezdxf.readfile(src)
    msp = doc.modelspace()
    for layer, side in JOIN_EDGES.items():
        outline = next(e for e in msp if e.dxf.layer == layer and not is_hole(e))
        if outline.dxftype() == "LWPOLYLINE":
            ring = [(x, y) for x, y, *_ in outline.get_points()]
        else:
            ring = poly(outline)
            if ring[0] == ring[-1]:
                ring = ring[:-1]
        ys = [y for _, y in ring]
        edge_y = max(ys) if side > 0 else min(ys)
        flat = [q for q in ring if abs(q[1] - edge_y) < 0.01]
        left, right = min(flat), max(flat)
        y2 = edge_y + side * JOIN_ALLOWANCE
        strip = Polygon([(left[0], edge_y), (right[0], edge_y), (right[0], y2), (left[0], y2)])
        g = Polygon(ring).buffer(0).union(strip.buffer(1e-9)).simplify(0.001)
        msp.add_lwpolyline(list(g.exterior.coords)[:-1], close=True, dxfattribs={"layer": layer})
        msp.delete_entity(outline)
        b = g.bounds
        print(f"{layer}: {'top' if side > 0 else 'bottom'} edge {right[0] - left[0]:.2f} in, "
              f"+5 mm, now {b[2] - b[0]:.2f} x {b[3] - b[1]:.2f} in")
    doc.saveas(dst)


def trim_cuff(src, dst, ref):
    from shapely.geometry import box, Polygon

    from join_chone_cuff import join
    from overlay_palm import PALM_OUTER, notch_corner

    if Path(dst).exists():
        sys.exit(f"{dst} exists, not overwriting")
    # Where the Cuff and the Front Palm sit in the finished glove, from the
    # reference pattern. The cut pieces are still at the reference's sheet
    # positions, so the same moves apply to them.
    rdoc = ezdxf.readfile(ref)
    px, py = notch_corner(rdoc.entitydb[PALM_OUTER])
    palm_bottom = min(y for _, y in poly(rdoc.entitydb[PALM_OUTER]))
    _, info = join(rdoc)  # moves the reference cuff into place; gives dx, dy
    palm_dy = info["join_left"][1] - py
    cut_y = palm_bottom + palm_dy - info["dy"]  # palm bottom, in the cut file's cuff position

    doc = ezdxf.readfile(src)
    msp = doc.modelspace()
    outline = next(e for e in msp if e.dxf.layer == "chone-cuff" and not is_hole(e))
    ring = [(x, y) for x, y, *_ in outline.get_points()]
    g = Polygon(ring)
    x0, y0, x1, y1 = g.bounds
    if not y0 < cut_y < y1:
        sys.exit(f"palm bottom ({cut_y:.3f}) is not inside the Cuff ({y0:.3f}..{y1:.3f}); nothing to trim")
    g = g.intersection(box(x0 - 1, cut_y, x1 + 1, y1 + 1)).simplify(0.001)
    msp.add_lwpolyline(list(g.exterior.coords)[:-1], close=True, dxfattribs={"layer": "chone-cuff"})
    msp.delete_entity(outline)
    doc.saveas(dst)
    b = g.bounds
    print(f"chone-cuff: cut {cut_y - y0:.3f} in ({(cut_y - y0) * 25.4:.1f} mm) off the bottom; "
          f"now {b[2] - b[0]:.2f} x {b[3] - b[1]:.2f} in")


def layout(src, mat_w, mat_h, only=None, label=None):
    """only: comma-separated layers to lay out (all if omitted); they must fit on
    one mat. label: name used in the output files instead of "mat <i> of <n>"."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from ezdxf.math import Matrix44
    from shapely import affinity
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    from shapely.prepared import prep

    mat_w, mat_h = float(mat_w), float(mat_h)
    tag = f"{mat_w:g}x{mat_h:g}"
    # Pieces are packed inside the mat less EDGE_MARGIN on every side.
    area_w, area_h = mat_w - 2 * EDGE_MARGIN, mat_h - 2 * EDGE_MARGIN
    doc = ezdxf.readfile(src)
    pieces = {}
    for e in doc.modelspace():
        if only and e.dxf.layer not in only.split(","):
            continue
        d = pieces.setdefault(e.dxf.layer, {"outline": None, "ents": []})
        d["ents"].append(e)
        if not is_hole(e):
            ring = [(x, y) for x, y, *_ in e.get_points()] if e.dxftype() == "LWPOLYLINE" else poly(e)
            d["outline"] = Polygon(ring).buffer(0)
    rotations = {n: [0, 90, 180, 270] for n in pieces}
    rotations.update(TILT.get((mat_w, mat_h), {}))

    def place(placed, shape):
        """Lowest, then leftmost, spot on the mat where shape fits, or None."""
        x0, y0, x1, y1 = shape.bounds
        w, h = x1 - x0, y1 - y0
        if w > area_w + 1e-9 or h > area_h + 1e-9:
            return None
        taken = prep(unary_union([q.buffer(LAYOUT_GAP) for *_, q in placed])) if placed else None
        nx = int((area_w - w) / LAYOUT_STEP + 1e-9) + 1
        ny = int((area_h - h) / LAYOUT_STEP + 1e-9) + 1
        for iy in range(ny):
            for ix in range(nx):
                dx = min(ix * LAYOUT_STEP, area_w - w) - x0
                dy = min(iy * LAYOUT_STEP, area_h - h) - y0
                q = affinity.translate(shape, dx, dy)
                if taken is None or not taken.intersects(q):
                    return dx, dy, q
        return None

    mats = []  # each: list of (name, rotation, dx, dy, placed outline)
    for name in sorted(pieces, key=lambda n: -pieces[n]["outline"].area):
        best = None
        for mi in range(len(mats) + 1):
            placed = mats[mi] if mi < len(mats) else []
            for r in rotations[name]:
                res = place(placed, affinity.rotate(pieces[name]["outline"], r, origin=(0, 0)))
                if res:
                    key = (mi, res[2].bounds[1] + res[2].bounds[3])  # earliest mat, then lowest
                    if best is None or key < best[0]:
                        best = (key, mi, r, res)
            if best:
                break
        if best is None:
            sys.exit(f"{name} does not fit on a {tag} mat")
        _, mi, r, (dx, dy, q) = best
        if mi == len(mats):
            mats.append([])
        mats[mi].append((name, r, dx, dy, q))

    if only and len(mats) > 1:
        # One mat was asked for: try every placing order and every rotation.
        import itertools

        names = list(pieces)
        for order in itertools.permutations(names):
            for rots in itertools.product(*[rotations[nm] for nm in order]):
                placed = []
                for nm, r in zip(order, rots):
                    res = place(placed, affinity.rotate(pieces[nm]["outline"], r, origin=(0, 0)))
                    if not res:
                        break
                    placed.append((nm, r, *res))
                else:
                    mats = [placed]
                    break
            if len(mats) == 1:
                break
    n = len(mats)
    if only:
        missing = set(only.split(",")) - set(pieces)
        if missing:
            sys.exit(f"no such layer(s): {', '.join(sorted(missing))}")
        if n > 1:
            sys.exit(f"{only} needs {n} {tag} mats, not one")
    outs = [(Path(src).parent / ("Laces Boxing 14OZ - leather cut - "
             + (f"{label} {tag}" if label else f"{tag} mat {i + 1} of {n}") + f" - studio top {EDGE_MARGIN / MM:g}mm edge {LAYOUT_GAP / MM:g}mm gap.dxf"),
             Path("renders") / (f"leather-cut-{label.replace(' ', '-')}-{tag}-{EDGE_MARGIN / MM:g}mm-edge-{LAYOUT_GAP / MM:g}mm-gap.png" if label
                                else f"leather-cut-mat{tag}-mat{i + 1}-{EDGE_MARGIN / MM:g}mm-edge-{LAYOUT_GAP / MM:g}mm-gap.png")) for i in range(n)]
    for d, png in outs:
        for f in (d, png):
            if f.exists():
                sys.exit(f"{f} exists, not overwriting")
    for i, (placed, (dxf_out, png_out)) in enumerate(zip(mats, outs)):
        out = ezdxf.readfile(src)
        msp = out.modelspace()
        keep = {p[0] for p in placed}
        for e in list(msp):
            if e.dxf.layer not in keep:
                msp.delete_entity(e)
        for name, r, dx, dy, _ in placed:
            m = Matrix44.chain(Matrix44.z_rotate(r * 3.141592653589793 / 180), Matrix44.translate(dx, dy, 0))
            for e in msp:
                if e.dxf.layer == name:
                    e.transform(m)
        to_studio_top(out, EDGE_MARGIN)
        fig, ax = plt.subplots(figsize=(8 * mat_w / 14, 8.6 * mat_h / 15))
        ax.add_patch(plt.Rectangle((0, 0), mat_w, mat_h, fill=False, lw=2, color="k"))
        ax.add_patch(plt.Rectangle((EDGE_MARGIN, EDGE_MARGIN), area_w, area_h, fill=False, lw=0.8, ls="--", color="r"))
        for e in msp:
            c = PIECE_COLOURS.get(e.dxf.layer, "k")
            ring = [(x, y) for x, y, *_ in e.get_points()] if e.dxftype() == "LWPOLYLINE" else poly(e)
            ring = [(x, -y) for x, y in ring]  # Studio view: y measured down from the mat's top
            ring = ring + ring[:1]
            ax.plot([x for x, _ in ring], [y for _, y in ring], color=c, lw=0.8 if is_hole(e) else 1.2)
            if not is_hole(e):
                g = Polygon(ring)
                ax.fill(*g.exterior.xy, color=c, alpha=0.15)
                rot = next(p[1] for p in placed if p[0] == e.dxf.layer)
                b = g.bounds
                pt = g.representative_point()
                ax.text(pt.x, pt.y, f'{e.dxf.layer}\n{b[2] - b[0]:.2f}" x {b[3] - b[1]:.2f}"'
                        + (f"\nrotated {rot:g}°" if rot else ""), ha="center", va="center", fontsize=9, color=c)
        ax.set_xlim(-0.5, mat_w + 0.5)
        ax.set_ylim(mat_h + 0.5, -0.5)
        ax.xaxis.tick_top()
        ax.set_aspect("equal")
        ax.set_xticks(range(0, int(mat_w) + 1))
        ax.set_yticks(range(0, int(mat_h) + 1))
        ax.grid(alpha=0.3)
        ax.set_title((f"{label.capitalize()}: " if label else f"Mat {i + 1} of {n}: ")
                     + f'{mat_w:g}" x {mat_h:g}" mat as in Silhouette Studio (inches from top-left)\n'
                     + f"{LAYOUT_GAP / MM:g} mm between pieces, {EDGE_MARGIN / MM:g} mm from the edges (red dashes)", pad=20)
        fig.savefig(png_out, dpi=90, bbox_inches="tight")
        plt.close(fig)
        out.saveas(dxf_out)
        print(f"{dxf_out.name}: " + ", ".join(f"{p[0]}" + (f" ({p[1]:g} deg)" if p[1] else "") for p in placed))


def to_studio_top(doc, margin=0.0):
    """Move everything so the top edge is at y = -margin and the left edge at x = margin."""
    from ezdxf.math import Matrix44

    msp = doc.modelspace()
    b = bbox.extents(msp)
    m = Matrix44.translate(margin - b.extmin.x, -margin - b.extmax.y, 0)
    for e in msp:
        e.transform(m)
    return b


def studio_top(src, dst, margin_mm="0"):
    if Path(dst).exists():
        sys.exit(f"{dst} exists, not overwriting")
    doc = ezdxf.readfile(src)
    b = to_studio_top(doc, float(margin_mm) * MM)
    doc.saveas(dst)
    a = bbox.extents(doc.modelspace())
    print(f"{dst}: {b.extmax.x - b.extmin.x:.3f} x {b.extmax.y - b.extmin.y:.3f} in, "
          f"was x {b.extmin.x:.3f}..{b.extmax.x:.3f} y {b.extmin.y:.3f}..{b.extmax.y:.3f}, "
          f"now x {a.extmin.x:.3f}..{a.extmax.x:.3f} y {a.extmin.y:.3f}..{a.extmax.y:.3f}")


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
    step, *args = sys.argv[1:]
    {"clean": clean, "split-chone": split_chone, "join-edges": join_edges,
     "trim-cuff": trim_cuff, "layout": layout, "studio-top": studio_top,
     "render": render_each}[step](*args)
