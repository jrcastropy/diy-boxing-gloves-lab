"""Straighten the Thumb seam edges and draw them side by side at true length.

- Front Palm: thumb-notch INNER line, corner to corner (palm optionally scaled).
- Thumb: top-edge OUTER line, tip to tip.
(Seam convention: Thumb outer line is sewn onto the palm's inner line.)

Both curves are measured along their path and drawn as straight bars starting
at the same point, with a ruler and a zoomed view of the right-hand ends.

Usage: python scripts/compare_thumb_seam.py "dxf/Laces Boxing 14OZ (1).dxf" renders/thumb-seam-compare.png [palm_scale]
"""
import math
import sys

import ezdxf
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from render_pieces import poly

PALM_INNER = "2EF"
THUMB_OUTER = "32E"


def sharp_corners(pts, thr=20, step=0.03):
    idx = [0]
    for i in range(1, len(pts)):
        if math.dist(pts[i], pts[idx[-1]]) >= step:
            idx.append(i)
    out = []
    for k in range(len(idx)):
        a, b, c = pts[idx[k - 1]], pts[idx[k]], pts[idx[(k + 1) % len(idx)]]
        turn = math.atan2(c[1] - b[1], c[0] - b[0]) - math.atan2(b[1] - a[1], b[0] - a[0])
        if abs((math.degrees(turn) + 180) % 360 - 180) > thr:
            out.append(idx[k])
    return out


def shorter_arc(pts, i, j):
    """Length of the shorter way round a closed outline between point i and j."""
    n = len(pts)

    def walk(a, b):
        total, k = 0.0, a
        while k != b:
            total += math.dist(pts[k], pts[(k + 1) % n])
            k = (k + 1) % n
        return total

    return min(walk(i, j), walk(j, i))


def palm_notch_inner(doc):
    pts = poly(doc.entitydb[PALM_INNER])
    xmin = min(p[0] for p in pts)
    ymin = min(p[1] for p in pts)
    c = [i for i in sharp_corners(pts) if pts[i][0] < xmin + 0.5 and pts[i][1] > ymin + 0.5]
    top, bottom = max(c, key=lambda i: pts[i][1]), min(c, key=lambda i: pts[i][1])
    return shorter_arc(pts, top, bottom)


def thumb_top_outer(doc):
    pts = poly(doc.entitydb[THUMB_OUTER])
    if math.dist(pts[0], pts[-1]) < 1e-6:
        pts = pts[:-1]
    tips = sharp_corners(pts)
    assert len(tips) == 2, tips
    return shorter_arc(pts, *tips)


def main(dxf, out, palm_scale=1.0):
    doc = ezdxf.readfile(dxf)
    palm = palm_notch_inner(doc) * palm_scale
    thumb = thumb_top_outer(doc)
    diff = palm - thumb
    longer = "Front Palm" if diff > 0 else "Thumb"

    bars = [
        (f"Front Palm notch, inner line ({palm_scale:.0%} scale)", palm, "#d62728"),
        ("Thumb top edge, outer line", thumb, "#1f4fd6"),
    ]
    fig, (ax, zoom) = plt.subplots(2, 1, figsize=(12, 5.5), gridspec_kw={"height_ratios": [3, 2]})

    for k, (label, length, colour) in enumerate(bars):
        y = 1 - k
        ax.plot([0, length], [y, y], color=colour, lw=6, solid_capstyle="butt")
        ax.text(0, y + 0.22, f"{label}:  {length:.3f}\"  ({length * 25.4:.1f} mm)", color=colour, fontsize=11)
        zoom.plot([0, length], [y, y], color=colour, lw=8, solid_capstyle="butt")
        zoom.axvline(length, color=colour, lw=1, ls="--")

    top = math.ceil(max(palm, thumb))
    ax.set_xticks([i / 4 for i in range(top * 4 + 1)], minor=True)
    ax.set_xticks(range(top + 1))
    ax.set_xlim(-0.1, top + 0.1)
    ax.set_ylim(-0.6, 1.6)
    ax.set_yticks([])
    ax.set_xlabel("inches (true length, measured along the curve)")
    ax.grid(axis="x", which="both", alpha=0.25)
    ax.set_title(f"Thumb seam: {longer} is longer by {abs(diff):.3f}\" ({abs(diff) * 25.4:.1f} mm)", fontsize=13)
    for s in ("left", "right", "top"):
        ax.spines[s].set_visible(False)

    lo, hi = min(palm, thumb), max(palm, thumb)
    pad = max(0.15, (hi - lo) * 1.5)
    zoom.set_xlim(lo - pad, hi + pad)
    zoom.set_ylim(-0.6, 1.6)
    zoom.set_yticks([])
    zoom.set_xlabel("zoom on the right-hand ends (inches)")
    zoom.grid(axis="x", alpha=0.3)
    zoom.annotate("", xy=(hi, 0.5), xytext=(lo, 0.5), arrowprops=dict(arrowstyle="<->", color="black"))
    zoom.text((lo + hi) / 2, 0.62, f"{abs(diff):.3f}\" / {abs(diff) * 25.4:.1f} mm", ha="center", fontsize=10)
    for s in ("left", "right", "top"):
        zoom.spines[s].set_visible(False)

    fig.tight_layout()
    fig.savefig(out, dpi=110, facecolor="white")
    print(f"palm notch inner ({palm_scale:.3f}): {palm:.3f}\"   thumb top outer: {thumb:.3f}\"   "
          f"{longer} longer by {abs(diff):.3f}\" ({abs(diff) * 25.4:.2f} mm)")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], float(sys.argv[3]) if len(sys.argv) > 3 else 1.0)
