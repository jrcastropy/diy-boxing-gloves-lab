"""Make Mould 1's thumb bigger so it closes part of the gap to the Chone's inner line.

Flat 2D only, from the DXF given. Mould 1 (drawn mirrored, so flipped) is turned and slid
until its thumb sits in the Chone's thumb with the gap to the Chone stitch line (inner
line) as even as possible, notch on notch. Each point on the mould's thumb edge then moves
outward by FRACTION of its own gap (0.5 = half: a 0.39" gap becomes 0.20").
The thumb edge moves right down to the wrist corner, so the corner moves out too; past
the corner the wrist edge comes back to its old line within WRIST_RETURN. The move fades
out close to the notch. The rest of Mould 1 does not change.

Writes a copy of the DXF (Mould 1 replaced in place, same handle) and a check render.
Refuses to overwrite an existing file.

Usage: uv run --with ezdxf --with shapely --with scipy --with matplotlib python scripts/grow_mould_thumb.py \
  "dxf/Laces Boxing 14OZ - palm 96% cuff matched.dxf" "dxf/Laces Boxing 14OZ - mould1 thumb half gap v2.dxf" \
  renders/mould1-thumb-half-gap-v2.png 0.5
"""
import math
import sys
from pathlib import Path

import ezdxf
import matplotlib
import numpy as np
from ezdxf.math import global_bspline_interpolation
from scipy.ndimage import gaussian_filter1d
from scipy.optimize import minimize
from shapely.geometry import Point, Polygon

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from render_pieces import poly  # noqa: E402

CHONE_CUT, CHONE_STITCH, MOULD1 = "95", "96", "320"
STEP = 0.02  # inches between outline samples
WRIST_RETURN = 0.35  # inches along the wrist edge for the moved corner to rejoin the old edge


def resample(xy, step):
    xy = np.vstack([xy, xy[:1]])
    s = np.r_[0, np.cumsum(np.hypot(*np.diff(xy, axis=0).T))]
    t = np.arange(0, s[-1], step)
    return np.c_[np.interp(t, s, xy[:, 0]), np.interp(t, s, xy[:, 1])]


def rot(deg):
    a = math.radians(deg)
    return np.array([[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]])


def main(src, dst, png, frac):
    if Path(dst).exists():
        sys.exit(f"refusing to overwrite existing file: {dst}")
    doc = ezdxf.readfile(src)
    db = doc.entitydb
    co = Polygon(poly(db[CHONE_CUT]))
    ci = Polygon(poly(db[CHONE_STITCH]))
    raw = np.array(poly(db[MOULD1]))
    fx = Polygon(raw).centroid.x  # flip about this x (and back again at the end)
    M = resample(raw * [-1, 1] + [2 * fx, 0], STEP)
    if Polygon(M).exterior.is_ccw is False:
        M = M[::-1]

    # The thumb: mould points left of the line notch -> bottom-left wrist corner, minus the finger side.
    near = M[(M[:, 1] > -66) & (M[:, 1] < -64.5) & (M[:, 0] < 198)]
    notch = near[near[:, 0].argmax()]
    bottom = M[:, 1].min()
    corner = M[np.abs(M[:, 1] - bottom) < 0.01][:, 0].min()
    corner = np.array([corner, bottom])
    d = corner - notch
    side = d[0] * (M[:, 1] - notch[1]) - d[1] * (M[:, 0] - notch[0])
    ref = d[0] * (-67 - notch[1]) - d[1] * (193 - notch[0])
    is_thumb = (np.sign(side) == np.sign(ref)) & ~((M[:, 0] > notch[0] - 0.84) & (M[:, 1] > notch[1] + 0.5))
    T = M[is_thumb]

    # Line the thumb up inside the Chone thumb: most even gap, nothing outside the stitch line.
    c = T.mean(0)

    def tf(p, X):
        return (X - c) @ rot(p[2]).T + c + p[:2]

    def gaps(X):
        return np.array([(1 if ci.contains(Point(q)) else -1) * ci.exterior.distance(Point(q)) for q in X])

    def cost(p):
        g = gaps(tf(p, T))
        return g.std() + 5 * np.clip(-g, 0, None).sum()

    best = None
    for r0 in range(-40, 41, 10):
        for dx in (-0.5, 0, 0.5):
            for dy in (-0.5, 0, 0.5):
                p0 = [186.5 - c[0] + dx, -67.5 - c[1] + dy, r0]
                r = minimize(cost, p0, method="Nelder-Mead", options={"xatol": 1e-3, "fatol": 1e-6, "maxiter": 800})
                if best is None or r.fun < best.fun:
                    best = r
    p = best.x
    A = tf(p, M)  # whole mould, lined up
    gap = gaps(A)

    # Outward normals (outline is counter-clockwise, so outward = tangent turned clockwise).
    tang = np.roll(A, -1, 0) - np.roll(A, 1, 0)
    nrm = np.c_[tang[:, 1], -tang[:, 0]]
    nrm /= np.linalg.norm(nrm, axis=1)[:, None]
    nrm = gaussian_filter1d(nrm, 5, axis=0, mode="wrap")
    nrm /= np.linalg.norm(nrm, axis=1)[:, None]

    # How far each point moves: frac x gap on the whole thumb edge, right down to the wrist
    # corner (the corner moves out too). Faded to 0 only close to the notch. Past the corner,
    # the wrist edge comes back to its old line over WRIST_RETURN inches.
    move = np.where(is_thumb, frac * np.clip(gap, 0, None), 0.0)
    idx = np.flatnonzero(is_thumb)
    i_corner = np.argmin(np.linalg.norm(M - corner, axis=1))
    i_notch = np.argmin(np.linalg.norm(M - notch, axis=1))
    n = len(M)
    for i in idx:
        dn = min((i - i_notch) % n, (i_notch - i) % n) * STEP
        w = min(1.0, dn / 0.5)
        move[i] *= 0.5 - 0.5 * math.cos(math.pi * w)  # smooth ease-in
    corner_move = move[i_corner]
    for k in range(1, int(WRIST_RETURN / STEP) + 1):
        for i in ((i_corner + k) % n, (i_corner - k) % n):
            if not is_thumb[i]:
                move[i] = corner_move * (1 - k * STEP / WRIST_RETURN)
    move = gaussian_filter1d(move, 3, mode="wrap")
    G = A + nrm * move[:, None]

    new_gap = gaps(G)
    th = is_thumb & (move > 0.02)
    print(f"Mould 1 thumb turned {p[2]:.1f} deg to line up.")
    print(f"Gap before (thumb): avg {gap[is_thumb].mean():.3f}  min {gap[is_thumb].min():.3f}  max {gap[is_thumb].max():.3f}")
    print(f"Gap after  (thumb): avg {new_gap[is_thumb].mean():.3f}  min {new_gap[is_thumb].min():.3f}  max {new_gap[is_thumb].max():.3f}")
    print(f"Thumb edge moved out: avg {move[th].mean():.3f}  max {move.max():.3f}")
    print(f"Mould 1 area {Polygon(A).area:.2f} -> {Polygon(G).area:.2f} sq in")

    # Back to the sheet: undo the lineup, then un-flip.
    back = (G - c - p[:2]) @ rot(-p[2]).T + c
    back = back * [-1, 1] + [2 * fx, 0]
    # Start the curve on the straight wrist edge so the closing join is on a straight line.
    k = int(np.argmin(np.abs(M[:, 1] - bottom) + np.abs(M[:, 0] - (corner[0] + 2.5))))
    back = np.roll(back, -k, 0)[::4]
    pts = np.vstack([back, back[:1]])
    pts = [(x, y, 0) for x, y in pts]
    spline = db[MOULD1]
    bs = global_bspline_interpolation(pts, degree=3)
    spline.apply_construction_tool(bs)
    spline.fit_points = []
    spline.closed = False
    doc.saveas(dst)
    chk = np.array(poly(ezdxf.readfile(dst).entitydb[MOULD1]))
    print(f"Saved {dst} (Mould 1 now {np.ptp(chk[:, 0]):.2f} x {np.ptp(chk[:, 1]):.2f} in, was {np.ptp(raw[:, 0]):.2f} x {np.ptp(raw[:, 1]):.2f})")

    fig, ax = plt.subplots(figsize=(10, 8))
    ax.plot(*co.exterior.xy, "k", lw=1, label="Chone cut line")
    ax.plot(*ci.exterior.xy, "k--", lw=1, label="Chone stitch line (inner)")
    ax.plot(*np.vstack([A, A[:1]]).T, color="0.6", lw=1, label="Mould 1 before")
    ax.plot(*np.vstack([G, G[:1]]).T, color="orange", lw=1.6, label=f"Mould 1 after (thumb closes {frac:.0%} of gap)")
    for i in idx[::25]:
        if move[i] > 0.02:
            ax.annotate(f'{gap[i]:.2f}" → {new_gap[i]:.2f}"', G[i], fontsize=7, xytext=(4, 4), textcoords="offset points")
    ax.set_xlim(182.5, 192)
    ax.set_ylim(-72, -63)
    ax.set_aspect("equal")
    ax.grid(alpha=0.3)
    ax.legend(loc="upper right", fontsize=8)
    ax.set_title(f"Mould 1 thumb made bigger, lined up in the Chone thumb\n{Path(src).name}")
    fig.savefig(png, dpi=110, bbox_inches="tight")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4]) if len(sys.argv) > 4 else 0.5)
