"""Make Mould 1's thumb narrower: each side comes in by a set amount, the tip stays where it is.

Flat 2D only, from the DXF given. Same thumb as lengthen_mould_thumb.py: the neck runs
from the crotch notch to the nearest point on the thumb's bottom edge; the centre line
runs from the middle of the neck to the tip. The thumb edge past the neck moves inward
(square to the outline) by SIDE inches all the way round, so the tip stays a round curve,
then slides back out along the centre line (nothing at the neck, SIDE at the tip) so the
tip ends up exactly where it was: the thumb is 2 x SIDE narrower and keeps its length.
On the top edge the move eases in over EASE inches out from the crotch. On the bottom edge
it's the full amount down to the neck, then fades out over FADE inches toward the wrist, so
the thumb is fully narrower right from the neck without a step. The rest of Mould 1 stays put.

Preview (no DXF written): one image per DXF and amount, laid inside the Chone like
renders/mould1-minified-chone.png, with the DXF's own Mould 1 drawn behind in grey.
  uv run --with ezdxf --with shapely --with matplotlib python scripts/slim_mould_thumb.py preview-in-chone \
    renders 0.125,0.25 "dxf/Laces Boxing 14OZ - mould1 minified chone.dxf" ...
Write a DXF (Mould 1 replaced in place, same handle) and a check render; refuses to overwrite:
  uv run --with ezdxf --with shapely --with matplotlib python scripts/slim_mould_thumb.py write \
    "dxf/Laces Boxing 14OZ - mould1 minified chone.dxf" OUT.dxf OUT.png 0.125
"""
import math
import sys
from pathlib import Path

import ezdxf
import matplotlib
import numpy as np
from ezdxf.math import global_bspline_interpolation
from shapely.geometry import LineString, Point, Polygon

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from lengthen_mould_thumb import CHONE_CUT, CHONE_STITCH, MOULD1, load, thumb, wrist_mid  # noqa: E402
from narrow_mould_thumb import widths  # noqa: E402
from render_pieces import poly  # noqa: E402

STEP = 0.02  # inches between outline samples (as load() makes them)
EASE = 0.4  # top edge: inches out from the crotch (past the neck line) over which the move eases in
FADE = 1.5  # bottom edge: inches along it, past the neck toward the wrist, over which the move fades out


def slim(M, side):
    mn, mc, arc, i_neck, i_tip, m, a = thumb(M)
    k_neck = int(np.where(arc == i_neck)[0][0])
    part = arc[: k_neck + 1]  # notch -> tip -> bottom of the neck
    # how far each point is out past the neck line (0 at both ends of the neck), toward the tip
    u = M[i_neck] - M[mn]
    nrm = np.array([u[1], -u[0]]) / np.linalg.norm(u)
    if nrm @ (M[i_tip] - m) < 0:
        nrm = -nrm
    w = np.zeros(len(M))
    k_tip = int(np.where(arc == i_tip)[0][0])
    top, bottom, wrist = arc[:k_tip], arc[k_tip:k_neck + 1], arc[k_neck + 1:]
    e = np.clip(((M[top] - m) @ nrm) / EASE, 0, 1)  # top edge: in from the crotch over EASE
    w[top] = 0.5 - 0.5 * np.cos(math.pi * e)
    w[bottom] = 1.0  # bottom edge: the full amount right down to the neck ...
    d = np.arange(1, len(wrist) + 1) * STEP  # ... then fading out along the edge toward the wrist
    w[wrist] = 0.5 + 0.5 * np.cos(math.pi * np.clip(d / FADE, 0, 1))
    # 1) the thumb edge moves inward (square to the outline) by `side`, so the round tip stays round
    tang = np.roll(M, -3, 0) - np.roll(M, 3, 0)
    inward = np.c_[-tang[:, 1], tang[:, 0]]  # outline runs counter-clockwise, so inward is to its left
    inward /= np.linalg.norm(inward, axis=1)[:, None]
    N = M + inward * (side * w)[:, None]
    # 2) slide it back out along the centre line, nothing at the neck and `side` at the tip, so the tip ends up
    #    exactly where it was and the thumb keeps its length
    t = (M - m) @ a
    slide = np.clip(t / t[i_tip], 0, 1) * w
    N = N + a * (side * slide)[:, None]
    return N, dict(mn=mn, mc=mc, arc=arc, i_neck=i_neck, i_tip=i_tip, m=m, a=a, w=w)


def report(M, N, info, side, name):
    a, m, arc = info["a"], info["m"], info["arc"]
    len0, len1 = ((M[arc] - m) @ a).max(), ((N[arc] - m) @ a).max()
    st = np.arange(0.5, len0 - 0.2, 0.5)
    w0, w1 = widths(LineString(M[arc]), m, a, st), widths(LineString(N[arc]), m, a, st)
    ok = ~np.isnan(w0) & ~np.isnan(w1)
    print(f"{name}, {side:g}\" each side: neck to tip {len0:.3f} -> {len1:.3f} in; "
          f"Mould 1 area {Polygon(M).area:.2f} -> {Polygon(N).area:.2f} sq in; valid {Polygon(N).is_valid}")
    print("   width at " + ", ".join(f"{t:.1f}\": {x0:.2f}->{x1:.2f}" for t, x0, x1 in zip(st[ok], w0[ok], w1[ok])))
    return len0, len1, st[ok], w0[ok], w1[ok]


def base_name(src):
    """'mould1 minified chone thumb +0.5in' -> 'mould1-minified-chone-thumb+0.5in'"""
    return Path(src).stem.split(" - ", 1)[1].replace(" +", "+").replace(" ", "-")


def figure(C, S, M, N, info, shift, side, src, len0, len1, st, w0, w1, title, ticks=None):
    """ticks: the new outline sampled like M (for the width ticks); N is what's drawn."""
    fig, ax = plt.subplots(figsize=(8, 9))
    ax.plot(*np.vstack([C, C[:1]]).T, "k", lw=1, label="Chone cut line")
    ax.plot(*np.vstack([S, S[:1]]).T, "k--", lw=0.8, label="Chone stitch line")
    ax.plot(*(np.vstack([M, M[:1]]) + shift).T, color="0.65", lw=1, label=f"Mould 1 before ({base_name(src)})")
    ax.plot(*(np.vstack([N, N[:1]]) + shift).T, color="orange", lw=2, label=f"Thumb {side:g}\" narrower each side ({2 * side:g}\" in all)")
    m, a = info["m"] + shift, info["a"]
    p = np.array([-a[1], a[0]])
    arcN = LineString((N if ticks is None else ticks)[info["arc"]] + shift)
    lines = []
    for k, (t, x0, x1) in enumerate(zip(st, w0, w1), 1):
        c = m + a * t
        hit = arcN.intersection(LineString([c - p * 10, c + p * 10]))
        q = np.array([g.coords[0] for g in getattr(hit, "geoms", [hit]) if not g.is_empty])
        if len(q) >= 2:
            q = q[np.argsort(q @ p)][[0, -1]]
            ax.plot(*q.T, color="royalblue", lw=0.7)
            ax.annotate(str(k), q[0], fontsize=7, color="royalblue", xytext=(-2, -9), textcoords="offset points")
        lines.append(f'{k}) {t:.1f}" out: {x0:.2f}" → {x1:.2f}"')
    ax.text(0.98, 0.02, "Width across the thumb\n(distance out from the neck)\n" + "\n".join(lines), transform=ax.transAxes,
            fontsize=8, color="royalblue", ha="right", va="bottom", bbox=dict(fc="white", ec="0.8"))
    ax.set_aspect("equal")
    ax.grid(alpha=0.25)
    ax.legend(loc="upper left", fontsize=8)
    ax.set_title(title, fontsize=10)
    return fig


def preview_in_chone(out_dir, sides, srcs):
    for src in srcs:
        db = ezdxf.readfile(src).entitydb
        C, S = np.array(poly(db[CHONE_CUT])), np.array(poly(db[CHONE_STITCH]))
        raw, fx, M = load(src)
        shift = wrist_mid(C) + [0, 0.3] - wrist_mid(M)
        for side in sides:
            dst = Path(out_dir) / f"{base_name(src)}-slim-{side:g}in-each-side-preview.png"
            if dst.exists():
                sys.exit(f"refusing to overwrite existing file: {dst}")
            N, info = slim(M, side)
            len0, len1, st, w0, w1 = report(M, N, info, side, base_name(src))
            fig = figure(C, S, M, N, info, shift, side, src, len0, len1, st, w0, w1,
                         f"PREVIEW (no DXF): thumb {side:g}\" narrower each side, tip kept (neck to tip {len0:.2f}\" → {len1:.2f}\")\n"
                         f"{Path(src).name}, flipped back, wrist middles together, raised 0.3\". Blue: width across the thumb")
            fig.savefig(dst, dpi=100, bbox_inches="tight")
            plt.close(fig)
            print(f"   wrote {dst}")


def write(src, dst, png, side):
    if Path(dst).exists():
        sys.exit(f"refusing to overwrite existing file: {dst}")
    doc = ezdxf.readfile(src)
    db = doc.entitydb
    C, S = np.array(poly(db[CHONE_CUT])), np.array(poly(db[CHONE_STITCH]))
    raw, fx, M = load(src)
    N, info = slim(M, side)
    len0, len1, st, w0, w1 = report(M, N, info, side, base_name(src))
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
    Sv = chk * [-1, 1] + [2 * fx, 0]
    line = Polygon(Sv).exterior
    print(f"Rest of Mould 1 off its old line by at most {max(line.distance(Point(q)) for q, ww in zip(M, info['w']) if ww == 0):.4f} in")
    print(f"Saved {dst} (Mould 1 now {np.ptp(chk[:, 0]):.2f} x {np.ptp(chk[:, 1]):.2f} in, was {np.ptp(raw[:, 0]):.2f} x {np.ptp(raw[:, 1]):.2f})")
    shift = wrist_mid(C) + [0, 0.3] - wrist_mid(M)
    fig = figure(C, S, M, Sv, info, shift, side, src, len0, len1, st, w0, w1,
                 f"Mould 1 thumb {side:g}\" narrower each side (from the saved DXF), neck to tip {len0:.2f}\" → {len1:.2f}\"\n"
                 f"{Path(src).name}, flipped back, wrist middles together, raised 0.3\"", ticks=N)
    fig.savefig(png, dpi=100, bbox_inches="tight")


if __name__ == "__main__":
    if sys.argv[1] == "preview-in-chone":
        preview_in_chone(sys.argv[2], [float(x) for x in sys.argv[3].split(",")], sys.argv[4:])
    else:
        write(sys.argv[2], sys.argv[3], sys.argv[4], float(sys.argv[5]))
