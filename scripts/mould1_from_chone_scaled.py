"""Replace Mould 1 with a scaled-down copy of the Chone outline.

Flat 2D only, from the DXF given. The Chone cut line is scaled evenly (same % across and
up) so its area equals Mould 1's current area, mirrored (Mould 1 is drawn mirrored on the
sheet) and put where Mould 1 was: the middle of its straight wrist edge on the middle of
Mould 1's wrist edge. Every angle of the Chone, thumb included, carries over unchanged.
The Chone itself does not change.

Writes a copy of the DXF (Mould 1 replaced in place, same handle) and a check render.
Refuses to overwrite an existing file.

Usage: uv run --with ezdxf --with shapely --with matplotlib python scripts/mould1_from_chone_scaled.py \
  "dxf/Laces Boxing 14OZ - palm 96% cuff matched.dxf" "dxf/Laces Boxing 14OZ - mould1 minified chone.dxf" \
  renders/mould1-minified-chone.png
"""
import math
import sys
from pathlib import Path

import ezdxf
import matplotlib
import numpy as np
from ezdxf.math import global_bspline_interpolation
from shapely.geometry import Polygon

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from render_pieces import poly  # noqa: E402

CHONE_CUT, CHONE_STITCH, MOULD1 = "95", "96", "320"


def resample(xy, step):
    xy = np.vstack([xy, xy[:1]])
    d = np.r_[0, np.cumsum(np.hypot(*np.diff(xy, axis=0).T))]
    t = np.arange(0, d[-1], step)
    return np.c_[np.interp(t, d, xy[:, 0]), np.interp(t, d, xy[:, 1])]


def wrist_mid(A):
    """Middle of the straight bottom (wrist) edge."""
    y0 = A[:, 1].min()
    e = A[A[:, 1] < y0 + 0.01]
    return np.array([(e[:, 0].min() + e[:, 0].max()) / 2, y0])


def main(src, dst, png):
    if Path(dst).exists():
        sys.exit(f"refusing to overwrite existing file: {dst}")
    doc = ezdxf.readfile(src)
    db = doc.entitydb
    C = np.array(poly(db[CHONE_CUT]))
    raw = np.array(poly(db[MOULD1]))
    a_m, a_c = Polygon(raw).area, Polygon(C).area
    s = math.sqrt(a_m / a_c)

    cw, mw = wrist_mid(C), wrist_mid(raw)
    N = (C - cw) * s * [-1, 1] + mw  # scale about the wrist middle, mirror, move onto Mould 1's wrist
    print(f"Chone cut line {np.ptp(C[:, 0]):.2f} x {np.ptp(C[:, 1]):.2f} in, area {a_c:.2f} sq in")
    print(f"Mould 1 was {np.ptp(raw[:, 0]):.2f} x {np.ptp(raw[:, 1]):.2f} in, area {a_m:.2f} sq in")
    print(f"Scale {s * 100:.2f}% -> new Mould 1 {np.ptp(N[:, 0]):.2f} x {np.ptp(N[:, 1]):.2f} in, area {Polygon(N).area:.2f} sq in")

    # Start the curve in the middle of the straight wrist edge so the closing join is on a straight line.
    k = int(np.argmin(np.hypot(*(N - mw).T)))
    pts = np.roll(N, -k, 0)
    pts = resample(pts, 0.08)  # even spacing, so the curve fit doesn't wobble
    pts = [(x, y, 0) for x, y in np.vstack([pts, pts[:1]])]
    spline = db[MOULD1]
    spline.apply_construction_tool(global_bspline_interpolation(pts, degree=3))
    spline.fit_points = []
    spline.closed = False
    doc.saveas(dst)
    chk = np.array(poly(ezdxf.readfile(dst).entitydb[MOULD1]))
    print(f"Saved {dst} (Mould 1 now {np.ptp(chk[:, 0]):.2f} x {np.ptp(chk[:, 1]):.2f} in, area {Polygon(chk).area:.2f} sq in)")

    # Check render: the new Mould 1 flipped back and laid inside the Chone, wrist middles together.
    S = np.array(poly(db[CHONE_STITCH]))
    back = (chk - mw) * [-1, 1] + cw + [0, 0.3]
    old = (raw - mw) * [-1, 1] + cw + [0, 0.3]
    fig, ax = plt.subplots(figsize=(8, 9))
    ax.plot(*np.vstack([C, C[:1]]).T, "k", lw=1, label="Chone cut line")
    ax.plot(*np.vstack([S, S[:1]]).T, "k--", lw=0.8, label="Chone stitch line")
    ax.plot(*np.vstack([old, old[:1]]).T, color="0.65", lw=1, label="Mould 1 before")
    ax.plot(*back.T, color="orange", lw=2, label=f"Mould 1 = Chone at {s * 100:.1f}% (from the saved DXF)")
    ax.set_aspect("equal")
    ax.grid(alpha=0.25)
    ax.legend(loc="upper left", fontsize=8)
    ax.set_title(f"Mould 1 replaced by a minified Chone (flipped back, wrist middles together, raised 0.3\")\n{Path(src).name}", fontsize=10)
    fig.savefig(png, dpi=100, bbox_inches="tight")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
