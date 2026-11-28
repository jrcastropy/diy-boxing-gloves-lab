"""Draw one pattern piece with its length and width (the box around it as it sits on the sheet), in inches and cm.

PIECE is a name from render_pieces.PIECES (e.g. chone, mould-1). Mould 1 is shown flipped (thumb on the left, like
the Chone), the same way as the other Mould 1 renders; flipping doesn't change the box. Refuses to overwrite.

  uv run --with ezdxf --with shapely --with matplotlib python scripts/measure_piece_size.py "dxf/A.dxf" chone renders/out.png
"""
import sys
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

import ezdxf  # noqa: E402

from lengthen_mould_thumb import load  # noqa: E402
from render_pieces import PIECES, poly  # noqa: E402


def main(src, piece, png):
    if Path(png).exists():
        sys.exit(f"refusing to overwrite existing file: {png}")
    if piece == "mould-1":
        raw, _, M = load(src)
        name, how = "Mould 1", " (shown flipped: thumb on the left)"
    else:
        raw = M = np.array(poly(ezdxf.readfile(src).entitydb[PIECES[piece][0]]))
        name, how = piece.replace("-", " ").title(), ""
    x0, y0 = M.min(0)
    x1, y1 = M.max(0)
    W, L = x1 - x0, y1 - y0
    print(f"{name}: L {L:.3f} in ({L * 2.54:.2f} cm) x W {W:.3f} in ({W * 2.54:.2f} cm); DXF as drawn {np.ptp(raw[:, 1]):.3f} x {np.ptp(raw[:, 0]):.3f}")
    fig, ax = plt.subplots(figsize=(9, 9.5))
    ax.plot(*np.vstack([M, M[:1]]).T, color="orangered", lw=2, label=f"{name}" + (" (cut line)" if piece == "chone" else ""))
    ax.add_patch(plt.Rectangle((x0, y0), W, L, fill=False, ls="--", lw=1, color="0.4", label=f"Box around {name}"))
    arrow = dict(arrowstyle="<->", color="k", lw=1.2)
    yW = y1 + 0.6
    ax.annotate("", (x0, yW), (x1, yW), arrowprops=arrow)
    ax.text((x0 + x1) / 2, yW + 0.2, f"W = {W:.2f}\"  ({W * 2.54:.2f} cm)", ha="center", va="bottom", fontsize=12, fontweight="bold")
    xL = x1 + 0.6
    ax.annotate("", (xL, y0), (xL, y1), arrowprops=arrow)
    ax.text(xL + 0.2, (y0 + y1) / 2, f"L = {L:.2f}\"\n({L * 2.54:.2f} cm)", ha="left", va="center", fontsize=12, fontweight="bold")
    for (xa, ya), (xb, yb) in [((x0, y1), (x0, yW + 0.15)), ((x1, y1), (x1, yW + 0.15)), ((x1, y0), (xL + 0.15, y0)), ((x1, y1), (xL + 0.15, y1))]:
        ax.plot([xa, xb], [ya, yb], color="0.6", lw=0.6)
    tip = M[np.argmin(M[:, 0])]
    ax.annotate("thumb tip (widest point)", tip, xytext=(tip[0] + 0.3, tip[1] + 1.6), fontsize=9,
                arrowprops=dict(arrowstyle="->", lw=0.8))
    ax.set_xlim(x0 - 0.8, x1 + 4.0)
    ax.set_ylim(y0 - 0.8, y1 + 1.6)
    ax.set_aspect("equal")
    ax.grid(alpha=0.25)
    ax.legend(loc="lower left", fontsize=9)
    ax.set_title(f"{name} length x width, as it sits on the sheet{how}\n{Path(src).name}", fontsize=10)
    fig.savefig(png, dpi=110, bbox_inches="tight")
    print(f"Saved {png}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
