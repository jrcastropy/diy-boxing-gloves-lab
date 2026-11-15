"""Print a large pattern piece at true size across several A4 pages (tiled), to tape together.

- Portrait A4 pages in a grid, each with a 0.6" white margin.
- Neighbouring pages overlap by OVERLAP inches. Inside every overlap strip there are
  alignment marks (circle + cross) that appear on BOTH pages: lay one page over the
  other so the marks and the pattern lines match exactly, then tape. Marks are kept
  clear of all pattern lines.
- Every page has its own check rulers in the margins (4 in along the bottom,
  10 cm up the left side), generated from real units, not from the DXF's scale bar.
- A small map in the top margin shows where the page goes.
- Smaller pieces listed in EXTRAS are packed into the main piece's empty space, each
  wholly on one page and outside the overlap strips, so they need no taping.
  Placements are searched each run, so they follow any change in piece size.

Print at 100% / "Actual size" (NOT "Fit to page").
Needs: ezdxf, matplotlib, shapely.

Usage: python scripts/print_tiled.py "dxf/Laces Boxing 14OZ - palm 96% cuff matched.dxf" print/chone-A4-tiled.pdf "Chone"
"""
import math
import string
import sys
from pathlib import Path

import ezdxf
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from ezdxf import bbox
from ezdxf.addons.drawing import Frontend, RenderContext
from ezdxf.addons.drawing.config import BackgroundPolicy, ColorPolicy, Configuration
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
from ezdxf.math import Matrix44
from shapely import affinity
from shapely.geometry import LineString, Point, Polygon, box

from print_pdf import handles_for
from render_pieces import poly

A4_W, A4_H = 210 / 25.4, 297 / 25.4  # inches
MARGIN = 0.6     # white border on every page (inches)
OVERLAP = 0.75   # shared strip between neighbouring pages (inches)
PAD = 0.15       # keep every piece at least this far inside the printable area
GAP = 0.25       # minimum gap between packed pieces
MARK_CLEAR = 0.35  # alignment marks stay this far from any pattern line
CM = 1 / 2.54
PIECES = {  # name -> [outer outline, inner outline]
    "Chone": ["95", "96"],
    "Chone Cuff": ["310", "311"],
    "Thumb": ["32E", "331"],
    "Mould 1": ["320"],  # foam moulds: one outline each
    "Mould 2": ["2FE"],
}
EXTRAS = {}  # e.g. {"Chone": ["Chone Cuff", "Thumb"]} to pack other pieces into the free space


def grid(b):
    """Grid anchored at the piece's bottom-left corner (plus PAD), so spare room collects top/right."""
    cw, ch = A4_W - 2 * MARGIN, A4_H - 2 * MARGIN
    w, h = b.size.x + 2 * PAD, b.size.y + 2 * PAD
    cols = max(1, math.ceil((w - OVERLAP) / (cw - OVERLAP)))
    rows = max(1, math.ceil((h - OVERLAP) / (ch - OVERLAP)))
    total_h = rows * ch - (rows - 1) * OVERLAP
    x0, ytop = b.extmin.x - PAD, b.extmin.y - PAD + total_h
    tiles = []
    for r in range(rows):
        for c in range(cols):
            tiles.append((r, c, x0 + c * (cw - OVERLAP), ytop - ch - r * (ch - OVERLAP)))
    return rows, cols, cw, ch, tiles


def safe_zones(rows, cols, cw, ch, tiles):
    """Area of each page a packed piece may use: inside PAD, outside the overlap strips."""
    zones = []
    for r, c, tx, ty in tiles:
        zones.append(box(tx + (OVERLAP if c > 0 else 0) + PAD,
                         ty + (OVERLAP if r < rows - 1 else 0) + PAD,
                         tx + cw - (OVERLAP if c < cols - 1 else 0) - PAD,
                         ty + ch - (OVERLAP if r > 0 else 0) - PAD))
    return zones


def pack(doc, main_poly, extras, zones):
    """Find a shift (dx, dy) and rotation for each extra piece. Upright first, then 180/90/270."""
    blocked = main_poly.buffer(GAP)
    placements = []
    for name in extras:
        shape = Polygon(poly(doc.entitydb[PIECES[name][0]]))
        cx, cy = shape.centroid.x, shape.centroid.y
        done = None
        for ang in (0, 180, 90, 270):
            q = affinity.rotate(shape, ang, origin=(cx, cy))
            qx0, qy0, qx1, qy1 = q.bounds
            w, h = qx1 - qx0, qy1 - qy0
            for z in zones:
                zx0, zy0, zx1, zy1 = z.bounds
                if w > zx1 - zx0 or h > zy1 - zy0:
                    continue
                steps = 24
                for j in range(steps + 1):          # prefer top of the zone
                    for i in range(steps + 1):      # then left
                        tx = zx0 + (zx1 - zx0 - w) * i / steps
                        ty = zy1 - h - (zy1 - zy0 - h) * j / steps
                        moved = affinity.translate(q, tx - qx0, ty - qy0)
                        if not blocked.intersects(moved):
                            done = (ang, tx - qx0, ty - qy0, (cx, cy), moved)
                            break
                    if done:
                        break
                if done:
                    break
            if done:
                break
        if not done:
            raise SystemExit(f"could not fit {name} into the free space")
        ang, dx, dy, centre, moved = done
        blocked = blocked.union(moved.buffer(GAP))
        placements.append((name, ang, dx, dy, centre))
    return placements


def reg_marks(rows, cols, cw, ch, tiles, lines):
    """3 alignment marks per shared edge, in the overlap middle, clear of all pattern lines."""
    def clear(x, y):
        pt = Point(x, y)
        return all(pt.distance(ln) >= MARK_CLEAR for ln in lines)

    def pick(cands):
        chosen = []
        for t in (0.15, 0.5, 0.85):
            free = [c for c in cands if clear(*c[1]) and c[1] not in chosen]
            if free:
                chosen.append(min(free, key=lambda c: abs(c[0] - t))[1])
        return chosen

    fs = [i / 40 for i in range(3, 38)]
    marks = []
    for r, c, tx, ty in tiles:
        if c + 1 < cols:
            x = tx + cw - OVERLAP / 2
            marks += pick([(f, (x, ty + f * ch)) for f in fs])
        if r + 1 < rows:
            y = ty + OVERLAP / 2
            marks += pick([(f, (tx + f * cw, y)) for f in fs])
    return marks


def draw_mark(ax, x, y, s=0.18):
    ax.add_patch(plt.Circle((x, y), s * 0.6, fill=False, lw=0.6, color="black"))
    ax.plot([x - s, x + s], [y, y], color="black", lw=0.6)
    ax.plot([x, x], [y - s, y + s], color="black", lw=0.6)


def margin_rulers(pg):
    """Rulers in page coordinates (inches from the sheet's bottom-left)."""
    x, y = MARGIN, MARGIN - 0.12
    pg.plot([x, x + 4], [y, y], color="black", lw=0.8)
    for i in range(33):
        t = 0.14 if i % 8 == 0 else (0.1 if i % 4 == 0 else 0.05)
        pg.plot([x + i / 8] * 2, [y, y - t], color="black", lw=0.5)
        if i % 8 == 0:
            pg.text(x + i / 8, y - 0.24, str(i // 8), fontsize=5, ha="center", va="center")
    pg.text(x + 4.1, y - 0.1, "inches: 0 to 4 must measure exactly 4 in", fontsize=5, va="center")
    x, y = MARGIN - 0.12, MARGIN + 0.3
    pg.plot([x, x], [y, y + 10 * CM], color="black", lw=0.8)
    for i in range(101):
        t = 0.14 if i % 10 == 0 else (0.1 if i % 5 == 0 else 0.05)
        pg.plot([x, x - t], [y + i * CM / 10] * 2, color="black", lw=0.4)
        if i % 10 == 0:
            pg.text(x - 0.24, y + i * CM / 10, str(i // 10), fontsize=5, ha="center", va="center")
    pg.text(x - 0.3, y + 10 * CM + 0.15, "cm: 0 to 10 = 10 cm", fontsize=5, va="bottom", rotation=90)


def mini_map(pg, rows, cols, r, c):
    size = 0.16
    x0, y0 = A4_W - MARGIN - cols * size, A4_H - MARGIN + 0.12
    for rr in range(rows):
        for cc in range(cols):
            pg.add_patch(plt.Rectangle((x0 + cc * size, y0 + (rows - 1 - rr) * size), size, size,
                                       fill=(rr, cc) == (r, c), facecolor="black", edgecolor="black", lw=0.5))


def main(dxf, out, name):
    doc = ezdxf.readfile(dxf)
    db = doc.entitydb
    keep = handles_for(doc, PIECES[name])
    b = bbox.extents([db[h] for h in keep])
    rows, cols, cw, ch, tiles = grid(b)

    main_poly = Polygon(poly(db[PIECES[name][0]]))
    extras = EXTRAS.get(name, [])
    placed_names = []
    if extras:
        for ename, ang, dx, dy, (cx, cy) in pack(doc, main_poly, extras, safe_zones(rows, cols, cw, ch, tiles)):
            m = Matrix44.chain(Matrix44.translate(-cx, -cy, 0), Matrix44.z_rotate(math.radians(ang)),
                               Matrix44.translate(cx + dx, cy + dy, 0))
            hs = handles_for(doc, PIECES[ename])
            for h in hs:
                db[h].transform(m)
            keep |= hs
            placed_names.append(ename)
            print(f"packed {ename}: rotated {ang} deg, shifted ({dx:.2f}, {dy:.2f})")

    lines = [LineString(poly(db[h])) for n in [name] + placed_names for h in PIECES[n]]
    marks = reg_marks(rows, cols, cw, ch, tiles, lines)
    title = f"{name} 14OZ" + (f"  +  {', '.join(placed_names)}" if placed_names else "")
    cfg = Configuration(background_policy=BackgroundPolicy.WHITE, color_policy=ColorPolicy.BLACK,
                        min_lineweight=0.3)
    Path(out).parent.mkdir(parents=True, exist_ok=True)

    with PdfPages(out) as pdf:
        for r, c, tx, ty in tiles:
            label = f"{string.ascii_uppercase[r]}{c + 1}"
            fig = plt.figure(figsize=(A4_W, A4_H))
            pg = fig.add_axes([0, 0, 1, 1])
            pg.set_xlim(0, A4_W)
            pg.set_ylim(0, A4_H)
            pg.axis("off")
            ax = fig.add_axes([MARGIN / A4_W, MARGIN / A4_H, cw / A4_W, ch / A4_H])
            Frontend(RenderContext(doc), MatplotlibBackend(ax), config=cfg).draw_layout(
                doc.modelspace(), finalize=False, filter_func=lambda e: e.dxf.handle in keep
            )
            ax.set_xlim(tx, tx + cw)
            ax.set_ylim(ty, ty + ch)
            ax.set_aspect("equal")
            ax.axis("off")
            for mx, my in marks:
                if tx <= mx <= tx + cw and ty <= my <= ty + ch:
                    draw_mark(ax, mx, my)
            pg.add_patch(plt.Rectangle((MARGIN, MARGIN), cw, ch, fill=False, lw=0.3, ls=(0, (2, 2))))
            pg.text(MARGIN, A4_H - MARGIN + 0.32,
                    f"{title}  -  page {label}  ({len(tiles)} pages, {rows} x {cols})  -  {Path(dxf).stem}",
                    fontsize=8, va="bottom")
            pg.text(MARGIN, A4_H - MARGIN + 0.12,
                    "Print at 100% / Actual size. Overlap pages so the circle-cross marks and lines match, then tape.",
                    fontsize=6, va="bottom")
            mini_map(pg, rows, cols, r, c)
            margin_rulers(pg)
            pdf.savefig(fig)
            plt.close(fig)

    # sanity checks: everything inside the printed areas, with PAD clearance
    cover = [box(tx + PAD, ty + PAD, tx + cw - PAD, ty + ch - PAD) for _, _, tx, ty in tiles]
    from shapely.ops import unary_union
    inside = unary_union(cover).buffer(1e-6)
    for n in [name] + placed_names:
        ok = inside.contains(Polygon(poly(db[PIECES[n][0]])))
        print(f"check: {n} fully inside printable area with {PAD}\" clearance: {ok}")
    print(f"{name}: {b.size.x:.3f} x {b.size.y:.3f} in on {rows} x {cols} pages; {len(marks)} alignment marks")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
