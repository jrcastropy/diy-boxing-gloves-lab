"""Print a large pattern piece at true size on as FEW A4 pages as possible.

Pages are not forced into a grid: each page can be portrait or landscape and sit
anywhere, as long as together they cover the whole piece and every join between
two pages overlaps by at least OVERLAP inches (so the pages can be taped).

Search (exact up to a 0.25" step): the leftmost uncovered point of the piece must
be covered by some page, so that page's left edge goes exactly there; repeat for
the next page; the last page must cover everything left. Tries the piece upright
first, other angles only if upright needs more pages.

Each page has: the piece (clipped to the page), alignment marks (circle + cross)
in every overlap, kept clear of pattern lines, check rulers (4 in, 10 cm) generated
from real units, and a small map showing where the page goes.

Print at 100% / "Actual size" (NOT "Fit to page").
Needs: ezdxf, matplotlib, shapely.

Usage: python scripts/print_free.py "dxf/Laces Boxing 14OZ - palm 96% cuff matched.dxf" print/chone-A4-tiled.pdf "Chone"
"""
import sys
from pathlib import Path

import ezdxf
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from ezdxf.addons.drawing import Frontend, RenderContext
from ezdxf.addons.drawing.config import BackgroundPolicy, ColorPolicy, Configuration
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
from shapely.geometry import LineString, Point, Polygon, box

from print_pdf import handles_for
from print_tiled import CM, MARGIN, OVERLAP, PAD, PIECES, draw_mark, margin_rulers
from render_pieces import poly

A4 = (210 / 25.4, 297 / 25.4)  # portrait (w, h) in inches
STEP = 0.25
MARK_CLEAR = 0.35


def page_sizes():
    """(name, page w, page h, core w, core h). Core = printable area minus OVERLAP/2 per side."""
    out = []
    for name, (pw, ph) in (("portrait", A4), ("landscape", A4[::-1])):
        cw, ch = pw - 2 * MARGIN, ph - 2 * MARGIN
        out.append((name, pw, ph, cw - OVERLAP, ch - OVERLAP))
    return out


def search(shape, max_pages=6):
    """Fewest pages covering `shape`. Returns a list of (size, x, y) cores, or None."""
    sizes = page_sizes()

    def rec(region, pages, limit):
        if region.is_empty or region.area < 1e-6:
            return pages
        if len(pages) == limit:
            return None
        x0, y0, x1, y1 = region.bounds
        for s in sizes:
            _, _, _, w, h = s
            if len(pages) == limit - 1 and (x1 - x0 > w + 1e-9 or y1 - y0 > h + 1e-9):
                continue  # last page must take everything left
            n = int((y1 - y0 + h) / STEP) + 1
            for k in range(n):
                y = y0 - h + k * STEP
                if y + h < y0 or y > y1:
                    continue
                core = box(x0, y, x0 + w, y + h)
                if not core.intersects(region):
                    continue
                res = rec(region.difference(core), pages + [(s, x0, y)], limit)
                if res:
                    return res
        return None

    for limit in range(1, max_pages + 1):
        res = rec(shape, [], limit)
        if res:
            return res
    return None


def overlap_marks(pages, lines):
    """3 marks in each overlap between two pages, along the overlap's long axis, clear of lines."""
    marks = []
    for i in range(len(pages)):
        for j in range(i + 1, len(pages)):
            inter = pages[i]["rect"].intersection(pages[j]["rect"])
            if inter.is_empty or inter.area < 0.05:
                continue
            x0, y0, x1, y1 = inter.bounds
            horiz = (x1 - x0) >= (y1 - y0)
            cands = []
            for k in range(3, 38):
                f = k / 40
                pt = (x0 + f * (x1 - x0), (y0 + y1) / 2) if horiz else ((x0 + x1) / 2, y0 + f * (y1 - y0))
                if all(Point(pt).distance(ln) >= MARK_CLEAR for ln in lines):
                    cands.append((f, pt))
            chosen = []
            for t in (0.15, 0.5, 0.85):
                free = [c for c in cands if c[1] not in chosen]
                if free:
                    chosen.append(min(free, key=lambda c: abs(c[0] - t))[1])
            marks += chosen
    # drop marks that crowd another (where two overlap strips meet)
    kept = []
    for m in marks:
        if all(Point(m).distance(Point(k)) >= 0.6 for k in kept):
            kept.append(m)
    return kept


def mini_map(pg, pages, current, x0, y0, scale=0.09):
    allx = [v for p in pages for v in (p["rect"].bounds[0], p["rect"].bounds[2])]
    ally = [v for p in pages for v in (p["rect"].bounds[1], p["rect"].bounds[3])]
    ox, oy = min(allx), min(ally)
    for i, p in enumerate(pages):
        a, b, c, d = p["rect"].bounds
        pg.add_patch(plt.Rectangle((x0 + (a - ox) * scale, y0 + (b - oy) * scale), (c - a) * scale, (d - b) * scale,
                                   fill=i == current, facecolor="0.6", edgecolor="black", lw=0.5))
        pg.text(x0 + ((a + c) / 2 - ox) * scale, y0 + ((b + d) / 2 - oy) * scale, str(i + 1),
                fontsize=5, ha="center", va="center")
    return (max(allx) - ox) * scale, (max(ally) - oy) * scale


def main(dxf, out, name):
    doc = ezdxf.readfile(dxf)
    db = doc.entitydb
    keep = handles_for(doc, PIECES[name])
    shape = Polygon(poly(db[PIECES[name][0]])).buffer(PAD)
    found = search(shape)
    if not found:
        raise SystemExit("no layout found")

    pages = []
    for (sname, pw, ph, w, h), x, y in found:
        # real printable area = core grown by OVERLAP/2 on every side
        rect = box(x - OVERLAP / 2, y - OVERLAP / 2, x + w + OVERLAP / 2, y + h + OVERLAP / 2)
        pages.append({"orient": sname, "pw": pw, "ph": ph, "rect": rect})
    # number pages top-to-bottom, then left-to-right
    pages.sort(key=lambda p: (-round(p["rect"].bounds[3], 1), p["rect"].bounds[0]))

    lines = [LineString(poly(db[h])) for h in PIECES[name]]
    marks = overlap_marks(pages, lines)
    cfg = Configuration(background_policy=BackgroundPolicy.WHITE, color_policy=ColorPolicy.BLACK,
                        min_lineweight=0.3)
    Path(out).parent.mkdir(parents=True, exist_ok=True)

    with PdfPages(out) as pdf:
        for i, p in enumerate(pages):
            pw, ph = p["pw"], p["ph"]
            a, b, c, d = p["rect"].bounds
            fig = plt.figure(figsize=(pw, ph))
            pg = fig.add_axes([0, 0, 1, 1])
            pg.set_xlim(0, pw)
            pg.set_ylim(0, ph)
            pg.axis("off")
            ax = fig.add_axes([MARGIN / pw, MARGIN / ph, (c - a) / pw, (d - b) / ph])
            Frontend(RenderContext(doc), MatplotlibBackend(ax), config=cfg).draw_layout(
                doc.modelspace(), finalize=False, filter_func=lambda e: e.dxf.handle in keep
            )
            ax.set_xlim(a, c)
            ax.set_ylim(b, d)
            ax.set_aspect("equal")
            ax.axis("off")
            for mx, my in marks:
                if a <= mx <= c and b <= my <= d:
                    draw_mark(ax, mx, my)
            pg.add_patch(plt.Rectangle((MARGIN, MARGIN), c - a, d - b, fill=False, lw=0.3, ls=(0, (2, 2))))
            pg.text(MARGIN, ph - MARGIN + 0.32,
                    f"{name} 14OZ  -  page {i + 1} of {len(pages)} ({p['orient']})  -  {Path(dxf).stem}",
                    fontsize=8, va="bottom")
            pg.text(MARGIN, ph - MARGIN + 0.12,
                    "Print at 100% / Actual size. Overlap pages so the circle-cross marks and lines match, then tape.",
                    fontsize=6, va="bottom")
            allw = max(q["rect"].bounds[2] for q in pages) - min(q["rect"].bounds[0] for q in pages)
            allh = max(q["rect"].bounds[3] for q in pages) - min(q["rect"].bounds[1] for q in pages)
            scale = (MARGIN - 0.15) / allh  # fits in the top margin
            mini_map(pg, pages, i, pw - MARGIN - allw * scale, ph - MARGIN + 0.05, scale)
            margin_rulers(pg)
            pdf.savefig(fig)
            plt.close(fig)
            print(f"page {i + 1}: {p['orient']}, drawing x {a:.2f}..{c:.2f}  y {b:.2f}..{d:.2f}")

    # checks
    from shapely.ops import unary_union
    covered = unary_union([box(*q["rect"].bounds).buffer(-PAD) for q in pages])
    print(f"check: {name} fully inside the printed areas with {PAD}\" clearance:",
          covered.buffer(1e-6).contains(Polygon(poly(db[PIECES[name][0]]))))
    for i in range(len(pages)):
        for j in range(i + 1, len(pages)):
            inter = pages[i]["rect"].intersection(pages[j]["rect"])
            if not inter.is_empty and inter.area > 0.05:
                x0, y0, x1, y1 = inter.bounds
                print(f"  pages {i + 1}+{j + 1} overlap strip: {min(x1 - x0, y1 - y0):.2f}\" wide")
    print(f"{name}: {len(pages)} pages, {len(marks)} alignment marks")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
