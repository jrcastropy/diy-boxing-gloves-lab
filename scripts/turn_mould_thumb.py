"""Turn Mould 1's thumb so it points at the same angle as the Chone's thumb.

Flat 2D only, from the DXF given. Mould 1 is drawn mirrored, so it is flipped and sat with
its wrist edge on the Chone's wrist stitch line. The angle of each thumb is the long axis
(centre line) of the thumb area: the part of the piece cut off by a line from the crotch
notch to the thumb's wrist corner. Mould 1's thumb outline is then turned about the middle
of that base line until its centre line matches the Chone's. The turn eases in over
EASE inches out from the base, so the notch and the wrist corner stay where they are.
Nothing else on Mould 1 moves, and the Chone does not change.

Writes a copy of the DXF (Mould 1 replaced in place, same handle) and a check render.
Refuses to overwrite an existing file.

Usage: uv run --with ezdxf --with shapely --with matplotlib python scripts/turn_mould_thumb.py \
  "dxf/Laces Boxing 14OZ - palm 96% cuff matched.dxf" "dxf/Laces Boxing 14OZ - mould1 thumb chone angle.dxf" \
  renders/mould1-thumb-chone-angle.png
"""
import math
import sys
from pathlib import Path

import ezdxf
import matplotlib
import numpy as np
from ezdxf.math import global_bspline_interpolation
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import split

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from render_pieces import poly  # noqa: E402

CHONE_CUT, CHONE_STITCH, MOULD1 = "95", "96", "320"
STEP = 0.02  # inches between outline samples
EASE = 1.0  # inches out from the thumb base over which the turn eases in


def resample(xy, step):
    xy = np.vstack([xy, xy[:1]])
    s = np.r_[0, np.cumsum(np.hypot(*np.diff(xy, axis=0).T))]
    t = np.arange(0, s[-1], step)
    return np.c_[np.interp(t, s, xy[:, 0]), np.interp(t, s, xy[:, 1])]


def landmarks(A):
    """Index of the crotch notch and of the thumb's wrist corner."""
    P = Polygon(A)
    hull = P.convex_hull
    d = np.array([hull.exterior.distance(Point(q)) for q in A])
    y0, y1 = A[:, 1].min(), A[:, 1].max()
    cand = np.where((A[:, 0] < P.centroid.x) & (A[:, 1] < y0 + 0.45 * (y1 - y0)))[0]
    i_notch = cand[d[cand].argmax()]
    bot = np.where(A[:, 1] < y0 + 0.15)[0]
    i_corner = bot[A[bot, 0].argmin()]
    return i_notch, i_corner


def thumb_axis(A, i_notch, i_corner):
    """Centre (area centroid) and angle in degrees of the thumb's long axis, pointing to the tip."""
    n, c = A[i_notch], A[i_corner]
    v = (c - n) / np.linalg.norm(c - n)
    th = min(split(Polygon(A), LineString([n - v * 20, c + v * 20])).geoms, key=lambda q: q.centroid.x)
    x0, y0, x1, y1 = th.bounds
    G = np.array([(x, y) for x in np.arange(x0, x1, 0.03) for y in np.arange(y0, y1, 0.03) if th.contains(Point(x, y))])
    m = G.mean(0)
    a = np.linalg.eigh(np.cov((G - m).T))[1][:, -1]
    if a[0] > 0:
        a = -a
    return m, a, math.degrees(math.atan2(a[1], a[0]))


def main(src, dst, png):
    if Path(dst).exists():
        sys.exit(f"refusing to overwrite existing file: {dst}")
    doc = ezdxf.readfile(src)
    db = doc.entitydb
    co = Polygon(poly(db[CHONE_CUT]))
    ci = Polygon(poly(db[CHONE_STITCH]))
    C = np.array(ci.exterior.coords)[:-1]
    raw = np.array(poly(db[MOULD1]))

    # Flip Mould 1 and sit its wrist edge on the Chone's wrist stitch line.
    fx = raw[:, 0].mean()
    M = resample(raw * [-1, 1] + [2 * fx, 0], STEP)
    cx0, cy0, cx1, cy1 = ci.bounds
    shift = np.array([(cx1 - 0.4) - M[:, 0].max(), cy0 - M[:, 1].min()])
    M = M + shift
    if not Polygon(M).exterior.is_ccw:
        M = M[::-1]

    cn, cc = landmarks(C)
    Cm, Ca, c_ang = thumb_axis(C, cn, cc)
    mn, mc = landmarks(M)
    Mm, Ma, m_ang = thumb_axis(M, mn, mc)

    # Turn the thumb outline (the arc notch -> tip -> wrist corner) about the middle of its base.
    piv = (M[mn] + M[mc]) / 2
    u = (M[mc] - M[mn]) / np.linalg.norm(M[mc] - M[mn])
    nrm = np.array([u[1], -u[0]])
    if nrm @ (Mm - piv) < 0:
        nrm = -nrm
    out = (M - piv) @ nrm
    n = len(M)
    arc1 = [(mn + k) % n for k in range((mc - mn) % n + 1)]
    arc2 = [(mc + k) % n for k in range((mn - mc) % n + 1)]
    arc = max((arc1, arc2), key=lambda r: out[r].mean())
    w = np.zeros(n)
    w[arc] = np.clip(out[arc] / EASE, 0, 1)
    w = 0.5 - 0.5 * np.cos(math.pi * w)

    def turn(deg):
        a = np.radians(deg) * w
        R = M - piv
        return np.c_[R[:, 0] * np.cos(a) - R[:, 1] * np.sin(a), R[:, 0] * np.sin(a) + R[:, 1] * np.cos(a)] + piv

    lo, hi = 0.0, 2 * (c_ang - m_ang)
    if lo > hi:
        lo, hi = hi, lo
    for _ in range(40):
        mid = (lo + hi) / 2
        if (thumb_axis(turn(mid), mn, mc)[2] < c_ang) == (c_ang > m_ang):
            lo = mid
        else:
            hi = mid
    deg = (lo + hi) / 2
    N = turn(deg)
    Nm, Na, n_ang = thumb_axis(N, mn, mc)
    moved = np.hypot(*(N - M).T)
    print(f"Chone thumb {c_ang:.1f} deg, Mould 1 thumb {m_ang:.1f} deg -> {n_ang:.1f} deg (turned {deg:+.1f} deg at the tip)")
    print(f"Thumb tip moved {moved.max():.2f} in; Mould 1 area {Polygon(M).area:.2f} -> {Polygon(N).area:.2f} sq in")
    print(f"Outside the Chone stitch line: {Polygon(N).difference(ci).area:.3f} sq in")

    # Back to the sheet: undo the shift and the flip.
    back = (N - shift) * [-1, 1] + [2 * fx, 0]
    # Start the curve on the straight wrist edge so the closing join is on a straight line.
    bottom = M[:, 1].min()
    k = int(np.argmin(np.abs(M[:, 1] - bottom) + np.abs(M[:, 0] - (M[mc, 0] + 2.5))))
    back = np.roll(back, -k, 0)[::4]
    pts = [(x, y, 0) for x, y in np.vstack([back, back[:1]])]
    spline = db[MOULD1]
    spline.apply_construction_tool(global_bspline_interpolation(pts, degree=3))
    spline.fit_points = []
    spline.closed = False
    doc.saveas(dst)

    # Check: the saved outline, away from the thumb, sits on the old one.
    chk = np.array(poly(ezdxf.readfile(dst).entitydb[MOULD1]))
    old = Polygon(raw).exterior
    far = [Point(q) for q, ww in zip((N - shift) * [-1, 1] + [2 * fx, 0], w) if ww == 0]
    newline = Polygon(chk).exterior
    print(f"Rest of Mould 1 off its old line by at most {max(newline.distance(p) for p in far):.4f} in")
    print(f"Saved {dst} (Mould 1 now {np.ptp(chk[:, 0]):.2f} x {np.ptp(chk[:, 1]):.2f} in, "
          f"was {np.ptp(raw[:, 0]):.2f} x {np.ptp(raw[:, 1]):.2f}; old outline length {old.length:.2f})")

    # Render from the saved file, placed the same way.
    S = chk * [-1, 1] + [2 * fx, 0] + shift
    fig, ax = plt.subplots(figsize=(8, 9))
    ax.plot(*co.exterior.xy, "k", lw=1, label="Chone cut line")
    ax.plot(*ci.exterior.xy, "k--", lw=0.8, label="Chone stitch line")
    ax.plot(*np.vstack([M, M[:1]]).T, color="0.65", lw=1, label="Mould 1 before")
    ax.plot(*S.T, color="orange", lw=2, label="Mould 1 after (from the saved DXF)")
    ax.plot(*np.array([Cm - Ca * 1.5, Cm + Ca * 3.2]).T, color="royalblue", lw=1.6, label=f"Chone thumb line {c_ang:.0f}°")
    ax.plot(*np.array([Nm - Na * 1.5, Nm + Na * 3.2]).T, color="red", lw=1.6, ls="-.", label=f"Mould 1 thumb line {n_ang:.0f}°")
    ax.plot(*piv, "k+", ms=10)
    ax.set_xlim(182.5, 196)
    ax.set_ylim(-71.5, -55)
    ax.set_aspect("equal")
    ax.grid(alpha=0.25)
    ax.legend(loc="upper left", fontsize=8)
    ax.set_title(f"Mould 1 thumb turned to the Chone thumb angle ({m_ang:.0f}° → {n_ang:.0f}°)\n{Path(src).name}", fontsize=10)
    fig.savefig(png, dpi=100, bbox_inches="tight")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
