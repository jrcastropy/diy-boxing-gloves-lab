"""Overlay Mould 1 from several DXFs in one image, to see how they differ.

Each DXF's Mould 1 is drawn in place (same sheet position; flipped so the thumb is on the left, like the Chone).
The thumb's neck-to-tip length is measured on the first DXF's thumb centre line, so all lengths are comparable.
Left panel: the whole mould. Right panel: close-up of the thumb, with the tip of each marked and the gaps labelled.

  uv run --with ezdxf --with shapely --with matplotlib python scripts/compare_mould1_outlines.py renders/out.png \
    "dxf/A.dxf" "Label A" "dxf/B.dxf" "Label B" ...
Refuses to overwrite an existing file.
"""
import sys
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from lengthen_mould_thumb import load, thumb  # noqa: E402

COLOURS = ["0.45", "royalblue", "orangered", "seagreen", "purple"]


def main(png, pairs):
    if Path(png).exists():
        sys.exit(f"refusing to overwrite existing file: {png}")
    outs = []
    fx0 = None
    for src, label in pairs:
        raw, fx, M = load(src)
        fx0 = fx if fx0 is None else fx0
        M = M + [2 * (fx0 - fx), 0]  # load() flips about each mould's own middle; use the first one's, so all share one frame
        outs.append((M, label))
    _, _, arc, i_neck, i_tip, m, a = thumb(outs[0][0])
    p = np.array([-a[1], a[0]])
    lens = [((M - m) @ a).max() for M, _ in outs]
    tips = [M[np.argmax((M - m) @ a)] for M, _ in outs]

    fig, axs = plt.subplots(1, 2, figsize=(15, 8.5), gridspec_kw=dict(width_ratios=[1, 1.15]))
    for ax in axs:
        for (M, label), col, L in zip(outs, COLOURS, lens):
            d = L - lens[0]
            extra = "" if d == 0 else f", +{d:.3f}\" / +{d * 2.54:.2f} cm"
            ax.plot(*np.vstack([M, M[:1]]).T, color=col, lw=1.8 if col != COLOURS[0] else 1.2,
                    label=f"{label}: neck to tip {L:.3f}\" ({L * 2.54:.2f} cm){extra}")
        ax.plot(*np.array([m - a * 0.3, m + a * (max(lens) + 0.4)]).T, "k-.", lw=0.6, label="Thumb centre line")
        nk = np.array([outs[0][0][arc[0]], outs[0][0][i_neck]])
        ax.plot(*nk.T, "k:", lw=1, label="Thumb neck (nothing moves on the hand side)")
        for q, col in zip(tips, COLOURS):
            ax.plot(*np.array([q - p * 0.3, q + p * 1.35]).T, color=col, lw=1)
        ax.set_aspect("equal")
        ax.grid(alpha=0.25)
    # labelled gaps between successive tips, in the close-up
    ax = axs[1]
    for k in range(1, len(tips)):
        q0, q1 = m + a * lens[k - 1] + p * 1.25, m + a * lens[k] + p * 1.25
        ax.annotate("", q1, q0, arrowprops=dict(arrowstyle="<->", color=COLOURS[k], lw=1))
        d = lens[k] - lens[k - 1]
        mid = (q0 + q1) / 2 + p * 0.3
        ax.text(*mid, f"+{d:.3f}\"\n{d * 2.54:.2f} cm", color=COLOURS[k], fontsize=8, ha="center", va="center")
    allp = np.vstack([M for M, _ in outs])
    tipzone = np.vstack(tips)
    cx, cy = (tipzone.mean(0) + m) / 2
    r = max(lens) / 2 + 1.0
    ax.set_xlim(cx - r, cx + r)
    ax.set_ylim(cy - r, cy + r)
    ax.set_title("Thumb close-up", fontsize=10)
    axs[0].set_xlim(allp[:, 0].min() - 0.5, allp[:, 0].max() + 0.5)
    axs[0].set_ylim(allp[:, 1].min() - 0.5, allp[:, 1].max() + 0.5)
    axs[0].set_title("Whole Mould 1", fontsize=10)
    h, lab = axs[0].get_legend_handles_labels()
    fig.legend(h, lab, loc="lower center", ncol=2, fontsize=9, frameon=False)
    fig.subplots_adjust(bottom=0.16, top=0.92)
    fig.suptitle("Mould 1 compared, shown flipped (thumb on the left, like the Chone). Thumb lengths measured on the first outline's centre line.",
                 fontsize=10)
    fig.savefig(png, dpi=110)
    for (M, label), L in zip(outs, lens):
        print(f"{label}: neck to tip {L:.3f} in ({L * 2.54:.2f} cm), +{L - lens[0]:.3f} in vs first")
    print(f"Saved {png}")


if __name__ == "__main__":
    args = sys.argv[2:]
    main(sys.argv[1], list(zip(args[::2], args[1::2])))
