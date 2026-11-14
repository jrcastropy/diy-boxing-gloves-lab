"""Render each pattern piece from the DXF on its own (no neighbouring pieces).

Usage: python scripts/render_pieces.py "dxf/Laces Boxing 14OZ (1).dxf" renders/
"""
import sys
from pathlib import Path

import ezdxf
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from ezdxf import bbox
from ezdxf.addons.drawing import Frontend, RenderContext
from ezdxf.addons.drawing.config import BackgroundPolicy, ColorPolicy, Configuration
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend

# Piece name -> handles of the outermost outline(s). Everything whose bounding-box
# centre falls inside one of these outlines is drawn with it.
PIECES = {
    # 2EF (inner line) listed explicitly: its bbox centre falls in the lace slot,
    # so the inside-the-outline test would otherwise drop it.
    "front-palm": ["2EE", "2EF"],
    "chone": ["95"],
    "chone-cuff": ["310"],
    "thumb": ["32E"],
    "thumb-panel": ["367"],
    "mould-1": ["320"],  # upright label, the larger one (10.13 x 12.68)
    "mould-2": ["2FE"],  # upside-down label (9.33 x 11.58)
    "cuff-mould": ["E7"],
}
# Scale bar has no outline: take what lies fully inside this box, minus other pieces.
SCALE_BOX = (185.8, 194.5, -73.6, -71.0)
MARGIN = 0.25


def poly(e):
    return [(p.x, p.y) for p in e.flattening(0.005)]


def inside(pt, pts):
    x, y = pt
    hit = False
    for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]):
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            hit = not hit
    return hit


def center(e):
    b = bbox.extents([e])
    return ((b.extmin.x + b.extmax.x) / 2, (b.extmin.y + b.extmax.y) / 2), b


def render(doc, keep, extents, out):
    x0, x1, y0, y1 = extents
    fig = plt.figure(figsize=(12, 12 * (y1 - y0) / (x1 - x0)))
    ax = fig.add_axes([0, 0, 1, 1])
    cfg = Configuration(background_policy=BackgroundPolicy.WHITE, color_policy=ColorPolicy.BLACK)
    Frontend(RenderContext(doc), MatplotlibBackend(ax), config=cfg).draw_layout(
        doc.modelspace(), finalize=False, filter_func=lambda e: e.dxf.handle in keep
    )
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.savefig(out, dpi=100, facecolor="white")
    plt.close(fig)


def main(dxf, outdir):
    doc = ezdxf.readfile(dxf)
    msp = doc.modelspace()
    ents = list(msp)
    info = {e.dxf.handle: center(e) for e in ents}
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    all_outlines = {h: poly(doc.entitydb[h]) for hs in PIECES.values() for h in hs}
    for name, handles in PIECES.items():
        keep = set(handles)
        for h, (c, _) in info.items():
            if any(inside(c, all_outlines[o]) for o in handles):
                keep.add(h)
        b = bbox.extents([doc.entitydb[h] for h in handles])
        ext = (b.extmin.x - MARGIN, b.extmax.x + MARGIN, b.extmin.y - MARGIN, b.extmax.y + MARGIN)
        render(doc, keep, ext, outdir / f"{name}.png")

    x0, x1, y0, y1 = SCALE_BOX
    keep = set()
    for h, (c, b) in info.items():
        fully_in = x0 <= b.extmin.x and b.extmax.x <= x1 and y0 <= b.extmin.y and b.extmax.y <= y1
        in_piece = any(h == o or inside(c, pts) for o, pts in all_outlines.items())
        if fully_in and not in_piece:
            keep.add(h)
    b = bbox.extents([doc.entitydb[h] for h in keep])
    render(doc, keep, (b.extmin.x - MARGIN, b.extmax.x + MARGIN, b.extmin.y - MARGIN, b.extmax.y + MARGIN),
           outdir / "scale-bar.png")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
