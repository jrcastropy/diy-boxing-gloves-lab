"""Join the Chone Cuff to the bottom of the Chone and render it as one image.

The cuff is moved (not rotated or scaled) so its top OUTER line sits exactly on
the Chone's bottom INNER line, centred on it. Chone is drawn in black, Chone
Cuff in blue, and the joining line in red.

Usage: python scripts/join_chone_cuff.py "dxf/Laces Boxing 14OZ (1).dxf" renders/chone-with-cuff.png
"""
import sys

import ezdxf
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from ezdxf import bbox
from ezdxf.addons.drawing import Frontend, RenderContext
from ezdxf.addons.drawing.config import BackgroundPolicy, ColorPolicy, Configuration
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
from ezdxf.math import Matrix44

from render_pieces import center, inside, poly

CHONE_OUTER, CHONE_INNER = "95", "96"
CUFF_OUTER, CUFF_INNER = "310", "311"
MARGIN = 0.3


def horizontal_edge(e, which):
    """(x_left, x_right, y) of the flat bottom/top edge of an outline."""
    pts = poly(e)
    y = min(p[1] for p in pts) if which == "bottom" else max(p[1] for p in pts)
    xs = [p[0] for p in pts if abs(p[1] - y) < 1e-3]
    return min(xs), max(xs), y


def piece_handles(msp, outer):
    outline = poly(outer)
    return {e.dxf.handle for e in msp if e is outer or inside(center(e)[0], outline)}


def join(doc):
    """Move the cuff into place on the loaded doc. Returns (handles to draw, info dict)."""
    msp = doc.modelspace()
    db = doc.entitydb
    chone = piece_handles(msp, db[CHONE_OUTER])
    cuff = piece_handles(msp, db[CUFF_OUTER])

    cx0, cx1, cy = horizontal_edge(db[CHONE_INNER], "bottom")
    ox0, ox1, _ = horizontal_edge(db[CHONE_OUTER], "bottom")
    ux0, ux1, uy = horizontal_edge(db[CUFF_OUTER], "top")
    # sideways: centre the cuff's top outer edge on the Chone's bottom OUTER edge
    # (corners line up exactly when the two are the same length);
    # height: the cuff's top outer line sits on the Chone's bottom INNER line.
    dx = (ox0 + ox1) / 2 - (ux0 + ux1) / 2
    dy = cy - uy
    move = Matrix44.translate(dx, dy, 0)
    for h in cuff:
        db[h].transform(move)
        db[h].dxf.color = 5  # blue
    for h in chone:
        db[h].dxf.color = 7  # black on white background

    # joining line, spanning the longer of the two edges
    seam = msp.add_line((min(cx0, ux0 + dx), cy), (max(cx1, ux1 + dx), cy), dxfattribs={"color": 1})
    keep = chone | cuff | {seam.dxf.handle}
    info = {
        "dx": dx, "dy": dy,
        "chone_inner_bottom": cx1 - cx0, "cuff_outer_top": ux1 - ux0,
        # left end of the join = cuff's top-left outer corner, after moving
        "join_left": (ux0 + dx, cy),
    }
    return keep, info


def render(doc, keep, out):
    db = doc.entitydb
    b = bbox.extents([db[h] for h in keep])
    x0, x1 = b.extmin.x - MARGIN, b.extmax.x + MARGIN
    y0, y1 = b.extmin.y - MARGIN, b.extmax.y + MARGIN
    fig = plt.figure(figsize=(12, 12 * (y1 - y0) / (x1 - x0)))
    ax = fig.add_axes([0, 0, 1, 1])
    cfg = Configuration(background_policy=BackgroundPolicy.WHITE, color_policy=ColorPolicy.COLOR)
    Frontend(RenderContext(doc), MatplotlibBackend(ax), config=cfg).draw_layout(
        doc.modelspace(), finalize=False, filter_func=lambda e: e.dxf.handle in keep
    )
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.savefig(out, dpi=100, facecolor="white")
    plt.close(fig)
    return b


def main(dxf, out):
    doc = ezdxf.readfile(dxf)
    keep, info = join(doc)
    b = render(doc, keep, out)
    print(f"cuff moved by dx={info['dx']:.3f} dy={info['dy']:.3f}")
    d = info["cuff_outer_top"] - info["chone_inner_bottom"]
    print(f"join: Chone inner bottom {info['chone_inner_bottom']:.3f} in, Cuff outer top {info['cuff_outer_top']:.3f} in "
          f"(Cuff {'wider' if d > 0 else 'narrower'} by {abs(d):.3f}, {abs(d) / 2:.3f} each side)")
    print(f"combined size: W={b.size.x:.3f} L={b.size.y:.3f}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
