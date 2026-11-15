"""Print a large pattern piece at true size on as FEW A4 pages as possible.

Pages are not forced into a grid: each page can be portrait or landscape and sit
anywhere, as long as together they cover the whole piece and every join between
two pages is a BUTT join: no overlap. Each page prints only the region it owns
(its rectangle minus the pages placed before it), so the owned regions fit together
edge to edge like a jigsaw.

Search (exact up to a 0.25" step): the leftmost uncovered point of the piece must
be covered by some page, so that page's left edge goes exactly there; repeat for
the next page; the last page must cover everything left. Tries the piece upright
first, other angles only if upright needs more pages.

Each page has: the piece (clipped to the page's own region), a solid CUT LINE around
that region (cut exactly on it, then butt the cut edges together and tape), check rulers (4 in, 10 cm)
generated from real units, and a small map showing where the page goes.

Print at 100% / "Actual size" (NOT "Fit to page").
Needs: ezdxf, matplotlib, shapely.

Usage: python scripts/print_free.py "dxf/Laces Boxing 14OZ - palm 96% cuff matched.dxf" print/chone-A4-tiled-butt.pdf "Chone"
"""
import sys
from pathlib import Path

import ezdxf
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import PathPatch
from matplotlib.path import Path as MplPath
from ezdxf.addons.drawing import Frontend, RenderContext
from ezdxf.addons.drawing.config import BackgroundPolicy, ColorPolicy, Configuration
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend

from shapely.geometry import Polygon, box
from shapely.ops import transform
from shapely.ops import unary_union

from print_pdf import handles_for
from print_tiled import MARGIN, PAD, PIECES, margin_rulers
from render_pieces import poly

A4 = (210 / 25.4, 297 / 25.4)  # portrait (w, h) in inches
STEP = 0.25
SNAP = 0.25  # page edges closer than this are merged into one straight cut
CUT_LW = 0.9  # cut line weight (points)


def page_sizes():
    """(name, page w, page h, core w, core h). Core = the whole printable area (butt joins)."""
    out = []
    for name, (pw, ph) in (("portrait", A4), ("landscape", A4[::-1])):
        cw, ch = pw - 2 * MARGIN, ph - 2 * MARGIN
        out.append((name, pw, ph, cw, ch))
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


def as_polys(g):
    return [g] if g.geom_type == "Polygon" else [q for q in getattr(g, "geoms", []) if q.geom_type == "Polygon"]


def draw_region(ax, region, **kw):
    for q in as_polys(region):
        for ring in [q.exterior, *q.interiors]:
            xs, ys = ring.xy
            ax.plot(xs, ys, **kw)


def snap_edges(pages, shape):
    """Merge cut-line coordinates that are nearly equal, so joins are straight lines without tiny steps.
    For each cluster of close x (or y) values, try each value and keep the first that still covers the
    piece, keeps every region inside its printable area, and keeps regions from overlapping."""
    import numpy as np

    def ok(owns):
        if not unary_union(owns).buffer(1e-6).contains(shape.buffer(-1e-6)):
            return False
        if any(o.difference(p["rect"]).area > 1e-4 for o, p in zip(owns, pages)):
            return False
        return all(owns[a].intersection(owns[b]).area < 1e-6
                   for a in range(len(owns)) for b in range(a + 1, len(owns)))

    def remap(g, axis, src, dst):
        def f(x, y, z=None):
            x, y = np.atleast_1d(x).astype(float), np.atleast_1d(y).astype(float)
            c = x if axis == 0 else y
            c = np.where(np.isin(np.round(c, 6), src), dst, c)
            return (c, y) if axis == 0 else (x, c)
        return transform(f, g).buffer(0)

    for axis in (0, 1):
        vals = sorted({round(c[axis], 6) for p in pages for q in as_polys(p["own"]) for c in q.exterior.coords})
        groups, cur = [], [vals[0]]
        for v in vals[1:]:
            if v - cur[-1] < SNAP:
                cur.append(v)
            else:
                groups.append(cur)
                cur = [v]
        groups.append(cur)
        for g in groups:
            if len(g) < 2:
                continue
            for dst in g:
                owns = [remap(p["own"], axis, g, dst) for p in pages]
                if ok(owns):
                    for p, o in zip(pages, owns):
                        p["own"] = o
                    break


def mini_map(pg, pages, current, x0, y0, scale):
    allx = [v for p in pages for v in (p["rect"].bounds[0], p["rect"].bounds[2])]
    ally = [v for p in pages for v in (p["rect"].bounds[1], p["rect"].bounds[3])]
    ox, oy = min(allx), min(ally)
    for i, p in enumerate(pages):
        for q in as_polys(p["own"]):
            xy = [(x0 + (x - ox) * scale, y0 + (y - oy) * scale) for x, y in q.exterior.coords]
            pg.add_patch(plt.Polygon(xy, closed=True, fill=i == current, facecolor="0.6", edgecolor="black", lw=0.5))
        c = p["own"].representative_point()
        pg.text(x0 + (c.x - ox) * scale, y0 + (c.y - oy) * scale, str(i + 1), fontsize=5, ha="center", va="center")


def main(dxf, out, name):
    doc = ezdxf.readfile(dxf)
    db = doc.entitydb
    keep = handles_for(doc, PIECES[name])
    shape = Polygon(poly(db[PIECES[name][0]])).buffer(PAD)
    found = search(shape)
    if not found:
        raise SystemExit("no layout found")

    # each page owns its rectangle minus the pages placed before it (search order),
    # trimmed to a box around the piece so no page carries empty paper
    pages, taken = [], None
    for (sname, pw, ph, w, h), x, y in found:
        rect = box(x, y, x + w, y + h)
        own = rect if taken is None else rect.difference(taken)
        taken = rect if taken is None else taken.union(rect)
        pages.append({"orient": sname, "pw": pw, "ph": ph, "rect": rect, "own": own})
    hull = box(*shape.bounds)
    for p in pages:
        p["own"] = p["own"].intersection(hull).buffer(0)
    snap_edges(pages, shape)
    pages = [p for p in pages if p["own"].area > 1e-3]
    # number pages top-to-bottom, then left-to-right
    pages.sort(key=lambda p: (-round(p["own"].bounds[3], 1), p["own"].bounds[0]))

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
            # clip the pattern to the region this page owns
            clip = PathPatch(MplPath.make_compound_path(*[MplPath(list(q.exterior.coords), closed=True)
                                                           for q in as_polys(p["own"])]),
                             transform=ax.transData, visible=False)
            ax.add_patch(clip)
            for art in list(ax.get_children()):
                if art is not ax.patch and art is not clip and hasattr(art, "set_clip_path"):
                    art.set_clip_path(clip)
            draw_region(ax, p["own"], color="black", lw=CUT_LW, solid_capstyle="projecting", clip_on=False)
            ax.set_xlim(a, c)
            ax.set_ylim(b, d)
            ax.set_aspect("equal")
            ax.axis("off")
            pg.text(MARGIN, ph - MARGIN + 0.32,
                    f"{name} 14OZ  -  page {i + 1} of {len(pages)} ({p['orient']})  -  {Path(dxf).stem}",
                    fontsize=8, va="bottom")
            pg.text(MARGIN, ph - MARGIN + 0.12,
                    "Print at 100% / Actual size. Cut exactly on the solid border, butt the edges together, tape.",
                    fontsize=6, va="bottom")
            allw = max(q["rect"].bounds[2] for q in pages) - min(q["rect"].bounds[0] for q in pages)
            allh = max(q["rect"].bounds[3] for q in pages) - min(q["rect"].bounds[1] for q in pages)
            scale = (MARGIN - 0.15) / allh  # fits in the top margin
            mini_map(pg, pages, i, pw - MARGIN - allw * scale, ph - MARGIN + 0.05, scale)
            margin_rulers(pg)
            pdf.savefig(fig)
            plt.close(fig)
            print(f"page {i + 1}: {p['orient']}, owns x {p['own'].bounds[0]:.2f}..{p['own'].bounds[2]:.2f}"
                  f"  y {p['own'].bounds[1]:.2f}..{p['own'].bounds[3]:.2f}")

    # checks
    owns = [p["own"] for p in pages]
    covered = unary_union(owns)
    print(f"check: {name} fully covered by the pages with {PAD}\" clearance:",
          covered.buffer(1e-6).contains(shape.buffer(-1e-6)))
    worst = max((owns[i].intersection(owns[j]).area for i in range(len(owns)) for j in range(i + 1, len(owns))), default=0)
    print(f"check: pages do not overlap (largest shared area {worst:.2e} sq in)")
    for k, p in enumerate(pages):
        spill = p["own"].difference(p["rect"]).area
        print(f"check: page {k + 1} region inside its printable area: {spill < 1e-4} (spill {spill:.2e} sq in)")
    print(f"{name}: {len(pages)} pages, butt joins")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
