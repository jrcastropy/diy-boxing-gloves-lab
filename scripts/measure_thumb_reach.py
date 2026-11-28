"""Straight-line distance from Mould 1's thumb tip to the wrist corner on the thumb side, for several DXFs, and an image.

The thumb tip is where the thumb's centre line (from the first DXF) meets the outline. The wrist corner is the
thumb-side end of the straight bottom (wrist) edge. Drawn flipped (thumb on the left, like the Chone), all in the
first DXF's frame, the same way as compare_mould1_outlines.py.

  uv run --with ezdxf --with shapely --with matplotlib python scripts/measure_thumb_reach.py renders/out.png \
    "dxf/A.dxf" "Label A" "dxf/B.dxf" "Label B" ...
Refuses to overwrite an existing file.
"""
import sys
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

import lengthen_mould_thumb as L  # noqa: E402

COLOURS = ["0.45", "royalblue", "orangered", "seagreen", "purple"]


def main(png, pairs):
    if Path(png).exists():
        sys.exit(f"refusing to overwrite existing file: {png}")
    L.STEP = 0.002
    outs, fx0, m, a = [], None, None, None
    for src, label in pairs:
        _, fx, M = L.load(src)
        fx0 = fx if fx0 is None else fx0
        M = M + [2 * (fx0 - fx), 0]  # share the first mould's frame
        if m is None:
            _, _, _, _, _, m, a = L.thumb(M)
        t, d = (M - m) @ a, np.abs((M - m) @ np.array([-a[1], a[0]]))
        near = np.where(d < 0.01)[0]
        tip = M[near[np.argmax(t[near])]]
        y0 = M[:, 1].min()
        flat = np.where(M[:, 1] < y0 + 0.001)[0]
        corner = M[flat[np.argmin(M[flat, 0])]]
        dist = np.hypot(*(corner - tip))
        outs.append((M, label, tip, corner, dist))
        print(f"{label}: tip {tip.round(3)} -> corner {corner.round(3)}: {dist:.3f} in = {dist * 2.54:.2f} cm")

    fig, ax = plt.subplots(figsize=(10, 8))
    corner0 = outs[0][3]
    for k, ((M, label, tip, corner, dist), col) in enumerate(zip(outs, COLOURS)):
        ax.plot(*np.vstack([M, M[:1]]).T, color=col, lw=1.8 if col != COLOURS[0] else 1.2, label=label)
        ax.plot(*np.array([tip, corner]).T, color=col, lw=1.2, ls="--")
        ax.plot(*np.array([tip, corner]).T, "o", color=col, ms=5)
        mid = tip + (corner - tip) * 0.35
        ax.annotate(f"{dist * 2.54:.2f} cm ({dist:.2f}\")", mid, xytext=(corner0[0] - 5.2, corner0[1] + 0.2 + 0.5 * (len(outs) - 1 - k)), color=col,
                    fontsize=10, fontweight="bold", ha="right", arrowprops=dict(arrowstyle="-", color=col, lw=0.6))
    ax.plot(*np.array([m - a * 0.3, m + a * 5]).T, "k-.", lw=0.6, label="Thumb centre line")
    corner = outs[0][3]
    tips = np.array([o[2] for o in outs])
    ax.set_xlim(tips[:, 0].min() - 3.2, corner[0] + 2.5)
    ax.set_ylim(corner[1] - 0.6, tips[:, 1].max() + 1.2)
    ax.set_aspect("equal")
    ax.grid(alpha=0.25)
    ax.legend(loc="upper right", fontsize=9)
    ax.set_title("Mould 1: straight line from the thumb tip (on the centre line) to the wrist corner on the thumb side\n"
                 "shown flipped (thumb on the left, like the Chone); inches on the axes", fontsize=10)
    fig.savefig(png, dpi=110, bbox_inches="tight")
    print(f"Saved {png}")


if __name__ == "__main__":
    args = sys.argv[2:]
    main(sys.argv[1], list(zip(args[::2], args[1::2])))
