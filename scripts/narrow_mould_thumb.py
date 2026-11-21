"""Make Mould 1's thumb narrower by a set amount, both edges coming in evenly.

Flat 2D only, from the DXF given. The thumb is the part of Mould 1 cut off by a line from
the crotch notch to the thumb's wrist corner; its centre line is the long axis of that
area. Every thumb outline point moves straight toward the centre line (square to it) by
half of NARROW, so the top and bottom edges each come in by NARROW/2. Points close to
the centre line (the tip) move less, so the tip stays round and the thumb keeps its
length. The move eases in over EASE inches out from the base line, so the notch, the
wrist corner and the rest of Mould 1 stay put. The thumb's angle doesn't change.

Writes a copy of the DXF (Mould 1 replaced in place, same handle) and a check render.
Refuses to overwrite an existing file.

Usage: uv run --with ezdxf --with shapely --with matplotlib python scripts/narrow_mould_thumb.py \
  "dxf/Laces Boxing 14OZ - mould1 minified chone.dxf" "dxf/Laces Boxing 14OZ - mould1 minified chone thumb -0.25in.dxf" \
  renders/mould1-minified-chone-thumb-narrow-0.25in.png 0.25
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

MOULD1 = "320"
STEP = 0.02  # inches between outline samples
EASE = 0.8  # inches along the outline, from the notch and from the wrist corner, over which the narrowing eases in
TIP = 0.25  # points closer than this to the centre line move less (keeps the tip round)


def resample(xy, step):
    xy = np.vstack([xy, xy[:1]])
    d = np.r_[0, np.cumsum(np.hypot(*np.diff(xy, axis=0).T))]
    t = np.arange(0, d[-1], step)
    return np.c_[np.interp(t, d, xy[:, 0]), np.interp(t, d, xy[:, 1])]


def landmarks(A):
    """Index of the crotch notch and of the thumb's wrist corner (thumb on the left)."""
    P = Polygon(A)
    hull = P.convex_hull
    dh = np.array([hull.exterior.distance(Point(q)) for q in A])
    y0, y1 = A[:, 1].min(), A[:, 1].max()
    cand = np.where((A[:, 0] < P.centroid.x) & (A[:, 1] < y0 + 0.5 * (y1 - y0)))[0]
    i_notch = cand[dh[cand].argmax()]
    bot = np.where(A[:, 1] < y0 + 0.01)[0]
    i_corner = bot[A[bot, 0].argmin()]
    return i_notch, i_corner


def thumb_area(A, i_notch, i_corner):
    n, c = A[i_notch], A[i_corner]
    v = (c - n) / np.linalg.norm(c - n)
    return min(split(Polygon(A), LineString([n - v * 20, c + v * 20])).geoms, key=lambda q: q.centroid.x)


def centre_line(th):
    x0, y0, x1, y1 = th.bounds
    G = np.array([(x, y) for x in np.arange(x0, x1, 0.02) for y in np.arange(y0, y1, 0.02) if th.contains(Point(x, y))])
    m = G.mean(0)
    a = np.linalg.eigh(np.cov((G - m).T))[1][:, -1]
    return m, (-a if a[0] > 0 else a)


def widths(edge, m, a, stations):
    """Edge-to-edge width of the thumb square to its centre line, at distances along it from the middle."""
    p = np.array([-a[1], a[0]])
    out = []
    for t in stations:
        c = m + a * t
        hit = edge.intersection(LineString([c - p * 10, c + p * 10]))
        q = np.array([g.coords[0] for g in getattr(hit, "geoms", [hit]) if not g.is_empty])
        out.append(np.ptp(q @ p) if len(q) >= 2 else np.nan)
    return np.array(out)


def main(src, dst, png, narrow):
    if Path(dst).exists():
        sys.exit(f"refusing to overwrite existing file: {dst}")
    doc = ezdxf.readfile(src)
    db = doc.entitydb
    raw = np.array(poly(db[MOULD1]))
    fx = raw[:, 0].mean()
    M = resample(raw * [-1, 1] + [2 * fx, 0], STEP)  # flipped so the thumb is on the left, like the Chone
    if not Polygon(M).exterior.is_ccw:
        M = M[::-1]

    mn, mc = landmarks(M)
    th = thumb_area(M, mn, mc)
    m, a = centre_line(th)
    perp = np.array([-a[1], a[0]])

    n = len(M)
    arc1 = [(mn + k) % n for k in range((mc - mn) % n + 1)]
    arc2 = [(mc + k) % n for k in range((mn - mc) % n + 1)]
    arc = arc1 if M[arc1, 0].min() < M[arc2, 0].min() else arc2
    on = np.zeros(n, bool)
    on[arc] = True

    side = (M - m) @ perp  # signed distance from the centre line
    w = np.zeros(n)
    sa = np.arange(len(arc)) * STEP  # distance along the outline from the notch
    w[arc] = np.clip(np.minimum(sa, sa[-1] - sa) / EASE, 0, 1)
    w = 0.5 - 0.5 * np.cos(math.pi * w)
    move = -(narrow / 2) * np.tanh(side / TIP * 2) * w  # toward the centre line
    N = M + perp * move[:, None]

    th_new = thumb_area(N, mn, mc)
    st = np.linspace(0, 2.0, 9)
    w0, w1 = widths(LineString(M[arc]), m, a, st), widths(LineString(N[arc]), m, a, st)
    m1, a1 = centre_line(th_new)
    ang0 = math.degrees(math.atan2(a[1], a[0]))
    ang1 = math.degrees(math.atan2(a1[1], a1[0]))
    len0 = np.ptp(np.array(th.exterior.coords) @ a)
    len1 = np.ptp(np.array(th_new.exterior.coords) @ a)
    print("Width across the thumb (along the centre line, inches from its middle):")
    ok = ~np.isnan(w0) & ~np.isnan(w1)  # near the base the square cut meets the palm, not a second edge
    st, w0, w1 = st[ok], w0[ok], w1[ok]
    for t, x0, x1 in zip(st, w0, w1):
        print(f"  {t:+.1f}: {x0:.3f} -> {x1:.3f}  ({x1 - x0:+.3f})")
    print(f"Thumb angle {ang0:.2f} -> {ang1:.2f} deg; thumb length {len0:.3f} -> {len1:.3f} in")
    print(f"Mould 1 area {Polygon(M).area:.2f} -> {Polygon(N).area:.2f} sq in; valid {Polygon(N).is_valid}")

    back = N * [-1, 1] + [2 * fx, 0]  # un-flip
    bottom = M[:, 1].min()
    flat = np.where(M[:, 1] < bottom + 0.005)[0]
    k = int(flat[np.argmin(np.abs(M[flat, 0] - M[flat, 0].mean()))])  # start mid wrist edge
    pts = np.roll(back, -k, 0)[::4]
    pts = [(x, y, 0) for x, y in np.vstack([pts, pts[:1]])]
    spline = db[MOULD1]
    spline.apply_construction_tool(global_bspline_interpolation(pts, degree=3))
    spline.fit_points = []
    spline.closed = False
    doc.saveas(dst)

    chk = np.array(poly(ezdxf.readfile(dst).entitydb[MOULD1]))
    still = [Point(q) for q, ww in zip(back, w) if ww == 0]
    print(f"Rest of Mould 1 off its old line by at most {max(Polygon(chk).exterior.distance(p) for p in still):.4f} in")
    print(f"Saved {dst} (Mould 1 now {np.ptp(chk[:, 0]):.2f} x {np.ptp(chk[:, 1]):.2f} in, was {np.ptp(raw[:, 0]):.2f} x {np.ptp(raw[:, 1]):.2f})")

    S = chk * [-1, 1] + [2 * fx, 0]
    fig, ax = plt.subplots(figsize=(8, 9))
    ax.plot(*np.vstack([M, M[:1]]).T, color="0.6", lw=1, label="Mould 1 before (minified Chone)")
    ax.plot(*S.T, color="orange", lw=2, label=f"Mould 1 after, thumb {narrow:g}\" narrower (from the saved DXF)")
    ax.plot(*np.array([m - a * 2.5, m + a * 3]).T, "r-.", lw=1, label="Thumb centre line")
    for t, x0, x1 in zip(st, w0, w1):
        c = m + a * t
        ax.plot(*np.array([c - perp * x1 / 2, c + perp * x1 / 2]).T, color="royalblue", lw=0.6)
        ax.annotate(f'{x0:.2f}"→{x1:.2f}"', c + perp * (x1 / 2 + 0.1), fontsize=7)
    ax.set_aspect("equal")
    ax.grid(alpha=0.25)
    ax.legend(loc="upper right", fontsize=8)
    ax.set_title(f"Mould 1 thumb narrowed by {narrow:g}\" (both edges in {narrow / 2:g}\"), shown flipped\n{Path(src).name}", fontsize=10)
    fig.savefig(png, dpi=100, bbox_inches="tight")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4]))
