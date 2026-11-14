"""Make a true-scale A4 PDF of the Front Palm and the Thumb for printing.

Page 1: Front Palm (from whichever DXF you pass, e.g. the 96% file).
Page 2: Thumb.

The check rulers are generated here from real units (1 in = 25.4 mm, A4 = 210 x 297 mm).
They do NOT use the scale bar drawn in the DXF, which is inconsistent.
Every page has:
  - right margin: 10-inch ruler (1/8" ticks), running up the page
  - left margin: 25 cm ruler (mm ticks), running up the page
Page 2 also has horizontal 6-inch and 15 cm rulers.
1 drawing unit = 1 inch on paper. Print at 100% / "Actual size" (NOT "Fit to page").

Usage: python scripts/print_pdf.py "dxf/Laces Boxing 14OZ - palm 96%.dxf" print/thumb-and-palm-A4.pdf [piece ...]
       pieces default to "Front Palm" "Thumb"; e.g. add "Chone Cuff" for a cuff-only PDF.
"""
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

from overlay_palm import notch_corner
from render_pieces import center, inside, poly

A4_W, A4_H = 210 / 25.4, 297 / 25.4  # inches
CM = 1 / 2.54
EDGE = 0.62  # ruler line distance from the page edge (inches); ticks point outward
LW = dict(color="black", lw=0.5)
PIECES = {
    "Front Palm": ["2EE", "2EF"],
    "Thumb": ["32E", "331"],
    "Chone Cuff": ["310", "311"],
}
DEFAULT_PIECES = ["Front Palm", "Thumb"]


def handles_for(doc, outlines):
    shape = poly(doc.entitydb[outlines[0]])
    keep = set(outlines)
    for e in doc.modelspace():
        if inside(center(e)[0], shape):
            keep.add(e.dxf.handle)
    return keep


def tick_len(i, major_every, mid_every):
    if i % major_every == 0:
        return 0.16
    if mid_every and i % mid_every == 0:
        return 0.11
    return 0.06


def vertical_ruler(ax, x, y, length, step, major_every, mid_every, label, outward):
    """Ruler line at x from y up `length`; ticks every `step`, pointing `outward` (-1 left, +1 right)."""
    ax.plot([x, x], [y, y + length], color="black", lw=0.8)
    for i in range(round(length / step) + 1):
        yy = y + i * step
        ax.plot([x, x + outward * tick_len(i, major_every, mid_every)], [yy, yy], **LW)
        if i % major_every == 0:
            ax.text(x + outward * 0.2, yy, str(i // major_every), fontsize=6,
                    ha="right" if outward < 0 else "left", va="center")
    ax.text(x - outward * 0.06, y + length / 2, label, rotation=90, fontsize=6,
            ha="left" if outward < 0 else "right", va="center")


def horizontal_ruler(ax, x, y, length, step, major_every, mid_every, label):
    ax.plot([x, x + length], [y, y], color="black", lw=0.8)
    for i in range(round(length / step) + 1):
        xx = x + i * step
        ax.plot([xx, xx], [y, y - tick_len(i, major_every, mid_every)], **LW)
        if i % major_every == 0:
            ax.text(xx, y - 0.28, str(i // major_every), fontsize=6, ha="center", va="center")
    ax.text(x, y + 0.08, label, fontsize=7, ha="left", va="bottom")


def margin_rulers(ax, x0, y0):
    y = y0 + 0.9
    vertical_ruler(ax, x0 + A4_W - EDGE, y, 10, 1 / 8, 8, 4,
                   "INCHES - lay your ruler here: 0 to 10 must measure exactly 10 in", +1)
    vertical_ruler(ax, x0 + EDGE, y, 25 * CM, CM / 10, 10, 5,
                   "CENTIMETRES - lay your ruler here: 0 to 25 must measure exactly 25 cm", -1)


def page(doc, name, outlines, dxf, pdf):
    keep = handles_for(doc, outlines)
    b = bbox.extents([doc.entitydb[h] for h in keep])
    w, h = b.size.x, b.size.y
    cx, cy = (b.extmin.x + b.extmax.x) / 2, (b.extmin.y + b.extmax.y) / 2
    thumb_page = name != "Front Palm"  # small pieces: piece up top, horizontal rulers below
    if thumb_page:
        cy -= 2.0  # piece in the upper half, horizontal rulers below

    fig = plt.figure(figsize=(A4_W, A4_H))
    ax = fig.add_axes([0, 0, 1, 1])
    cfg = Configuration(background_policy=BackgroundPolicy.WHITE, color_policy=ColorPolicy.BLACK,
                        min_lineweight=0.3)
    Frontend(RenderContext(doc), MatplotlibBackend(ax), config=cfg).draw_layout(
        doc.modelspace(), finalize=False, filter_func=lambda e: e.dxf.handle in keep
    )
    x0, y0 = cx - A4_W / 2, cy - A4_H / 2
    ax.set_xlim(x0, x0 + A4_W)
    ax.set_ylim(y0, y0 + A4_H)
    ax.set_aspect("equal")
    ax.axis("off")

    margin_rulers(ax, x0, y0)

    size = f"{w:.2f}\" x {h:.2f}\" ({w * 25.4:.0f} x {h * 25.4:.0f} mm)"
    if thumb_page:
        horizontal_ruler(ax, x0 + 1.1, y0 + 3.0, 6, 1 / 8, 8, 4,
                         "INCHES: 0 to 6 must measure exactly 6 in")
        horizontal_ruler(ax, x0 + 1.1, y0 + 1.9, 15 * CM, CM / 10, 10, 5,
                         "CENTIMETRES: 0 to 15 must measure exactly 15 cm")
        ax.text(x0 + 1.1, b.extmax.y + 0.5,
                f"{name} 14OZ  -  {Path(dxf).stem}  -  {size}\n"
                "Print at 100% / \"Actual size\". Check the rulers before cutting.",
                fontsize=7, va="bottom")
    else:
        # palm: note sits in the empty thumb-notch area, outside the piece
        _, ny = notch_corner(doc.entitydb[outlines[0]])
        ax.text(b.extmin.x + 0.08, ny + 1.75,
                f"{name} 14OZ\n{Path(dxf).stem}\n{w:.2f}\" x {h:.2f}\"\n({w * 25.4:.0f} x {h * 25.4:.0f} mm)\n\n"
                "Print at 100% /\n\"Actual size\".\nCheck the rulers\nbefore cutting.",
                fontsize=6, va="center", ha="left")

    pdf.savefig(fig)
    plt.close(fig)
    return w, h


def main(dxf, out, names=None):
    doc = ezdxf.readfile(dxf)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    with PdfPages(out) as pdf:
        for i, name in enumerate(names or DEFAULT_PIECES):
            w, h = page(doc, name, PIECES[name], dxf, pdf)
            print(f"page {i + 1}: {name} {w:.3f} x {h:.3f} in")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3:] or None)
