"""Make Mould 1's thumb longer by a set amount, along the thumb's own centre line.

Flat 2D only, from the DXF given. The thumb's neck is its narrowest point: the crotch
notch and the nearest point to it on the thumb's bottom edge. The thumb's centre line
runs from the middle of the neck to the tip (the thumb point furthest out along that
line). The thumb is stretched evenly along the centre line: each thumb outline point
past the neck slides toward the tip in proportion to how far out it is (nothing at the
neck, the full amount at the tip). Its distance from the centre line doesn't change,
so the thumb doesn't get wider or turn. The notch, the bottom edge down to the wrist
corner and the rest of Mould 1 stay put.

Preview (no DXF written): several amounts side by side in one image.
  uv run --with ezdxf --with shapely --with matplotlib python scripts/lengthen_mould_thumb.py preview \
    "dxf/Laces Boxing 14OZ - mould1 minified chone.dxf" renders/mould1-thumb-longer-preview.png 0.25 0.5 0.75
Same amounts, each laid inside the Chone, with and without the current Mould 1 behind (2 images each):
  uv run --with ezdxf --with shapely --with matplotlib python scripts/lengthen_mould_thumb.py preview-in-chone \
    "dxf/Laces Boxing 14OZ - mould1 minified chone.dxf" renders 0.25 0.5 0.75
For an outline that is already smooth curves (the smoothed Mould 1), use write-smooth instead of write: it moves only
the thumb's own curves, so the rest of the outline (corners, straight bottom edge) stays exactly as it is:
  uv run --with ezdxf --with shapely --with matplotlib --with scipy python scripts/lengthen_mould_thumb.py write-smooth \
    "dxf/Laces Boxing 14OZ - mould1 minified chone - edited - smoothed all.dxf" \
    "dxf/Laces Boxing 14OZ - mould1 minified chone - edited - smoothed all thumb +0.5in.dxf" renders/mould1-smoothed-thumb-longer-0.5in.png 0.5
Add --name NAME (e.g. --name smoothed) to name the previews mould1-NAME-thumb-longer-... and label the current Mould 1 as NAME.
Write a DXF (Mould 1 replaced in place, same handle) and a check render; refuses to overwrite:
  uv run --with ezdxf --with shapely --with matplotlib python scripts/lengthen_mould_thumb.py write \
    "dxf/Laces Boxing 14OZ - mould1 minified chone.dxf" "dxf/Laces Boxing 14OZ - mould1 minified chone thumb +0.5in.dxf" \
    renders/mould1-minified-chone-thumb-longer-0.5in.png 0.5
"""
import sys
from pathlib import Path

import ezdxf
import matplotlib
import numpy as np
from ezdxf.math import global_bspline_interpolation
from shapely.geometry import LineString, Point, Polygon

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from narrow_mould_thumb import landmarks, resample, widths  # noqa: E402
from render_pieces import poly  # noqa: E402

CHONE_CUT, CHONE_STITCH, MOULD1 = "95", "96", "320"
STEP = 0.02  # inches between outline samples
NAME = None  # --name NAME: which Mould 1 this is, for preview file names and labels (default: the minified Chone)


def load(src):
    raw = np.array(poly(ezdxf.readfile(src).entitydb[MOULD1]))
    fx = raw[:, 0].mean()
    M = resample(raw * [-1, 1] + [2 * fx, 0], STEP)  # flipped so the thumb is on the left, like the Chone
    if not Polygon(M).exterior.is_ccw:
        M = M[::-1]
    return raw, fx, M


def thumb(M):
    """Thumb outline indices (notch -> tip -> wrist corner), the neck and the centre line."""
    mn, mc = landmarks(M)
    n = len(M)
    arc1 = [(mn + k) % n for k in range((mc - mn) % n + 1)]
    arc2 = [(mc + k) % n for k in range((mn - mc) % n + 1)]
    arc = np.array(arc1 if M[arc1, 0].min() < M[arc2, 0].min() else arc2)
    i_tip = arc[np.argmin(M[arc, 0])]
    for _ in range(5):  # neck: notch + nearest bottom-edge point; tip: furthest out from the neck's middle
        k_tip = int(np.where(arc == i_tip)[0][0])
        bottom = arc[k_tip:]
        i_neck = bottom[np.argmin(np.hypot(*(M[bottom] - M[mn]).T))]
        m = (M[mn] + M[i_neck]) / 2
        a = M[i_tip] - m
        a /= np.linalg.norm(a)
        i_tip = arc[np.argmax((M[arc] - m) @ a)]
    return mn, mc, arc, i_neck, i_tip, m, a


def lengthen(M, amount):
    mn, mc, arc, i_neck, i_tip, m, a = thumb(M)
    t = (M - m) @ a  # distance along the centre line from the middle of the neck
    k_neck = int(np.where(arc == i_neck)[0][0])
    w = np.zeros(len(M))
    w[arc[:k_neck]] = np.clip(t[arc[:k_neck]] / t[i_tip], 0, 1)  # only notch -> tip -> neck moves
    N = M + a * (amount * w)[:, None]
    return N, dict(mn=mn, mc=mc, arc=arc, i_neck=i_neck, i_tip=i_tip, m=m, a=a, w=w)


def report(M, N, info, amount):
    a, m, arc = info["a"], info["m"], info["arc"]
    len0, len1 = ((M[arc] - m) @ a).max(), ((N[arc] - m) @ a).max()
    neck = np.hypot(*(M[info["mn"]] - M[info["i_neck"]]))
    st = np.linspace(0.5, 2.5, 5)
    w0, w1 = widths(LineString(M[arc]), m, a, st), widths(LineString(N[arc]), m, a, st)
    print(f"+{amount:g}\": neck {neck:.2f} in wide; thumb neck-to-tip {len0:.3f} -> {len1:.3f} in; "
          f"Mould 1 area {Polygon(M).area:.2f} -> {Polygon(N).area:.2f} sq in; valid {Polygon(N).is_valid}")
    print("   widths at 0.5..2.5 in from the neck: " + ", ".join(f"{x0:.2f}->{x1:.2f}" for x0, x1 in zip(w0, w1) if not np.isnan(x0)))
    return len0, len1


def draw(ax, M, N, info, amount, len0, len1):
    m, a = info["m"], info["a"]
    p = np.array([-a[1], a[0]])
    ax.plot(*np.vstack([M, M[:1]]).T, color="0.6", lw=1, label=f"Mould 1 now ({NAME or 'minified Chone'})")
    ax.plot(*np.vstack([N, N[:1]]).T, color="orange", lw=2, label=f"Thumb {amount:g}\" longer")
    ax.plot(*np.array([m - a * 0.5, m + a * (len1 + 0.5)]).T, "r-.", lw=0.8, label="Thumb centre line")
    tip0 = M[np.argmax((M - m) @ a)]
    tip1 = N[np.argmax((N - m) @ a)]
    for q, col in ((tip0, "0.4"), (tip1, "orange")):
        ax.plot(*np.array([q - p * 0.6, q + p * 0.6]).T, color=col, lw=1)
    nk = np.array([M[info["mn"]], M[info["i_neck"]]])
    ax.plot(*nk.T, color="royalblue", lw=1, ls=":", label="Thumb neck: nothing moves on the hand side")
    ax.set_title(f"+{amount:g}\": neck to tip {len0:.2f}\" → {len1:.2f}\"", fontsize=10)
    ax.set_aspect("equal")
    ax.grid(alpha=0.25)


def preview(src, png, amounts):
    raw, fx, M = load(src)
    fig, axs = plt.subplots(1, len(amounts), figsize=(6.5 * len(amounts), 7.5))
    axs = np.atleast_1d(axs)
    for ax, amt in zip(axs, amounts):
        N, info = lengthen(M, amt)
        len0, len1 = report(M, N, info, amt)
        draw(ax, M, N, info, amt, len0, len1)
        ax.set_xlim(M[:, 0].min() - 1.2, M[:, 0].min() + 7)
        ax.set_ylim(M[:, 1].min() - 0.5, M[:, 1].min() + 7)
    axs[0].legend(loc="upper right", fontsize=7)
    fig.suptitle(f"PREVIEW, no DXF written. Mould 1 thumb made longer along its centre line; width, angle and the rest of Mould 1 unchanged.\n"
                 f"{Path(src).name}, shown flipped (thumb on the left, like the Chone)", fontsize=10)
    fig.savefig(png, dpi=95, bbox_inches="tight")


def wrist_mid(A):
    """Middle of the straight bottom (wrist) edge."""
    y0 = A[:, 1].min()
    e = A[A[:, 1] < y0 + 0.01]
    return np.array([(e[:, 0].min() + e[:, 0].max()) / 2, y0])


def preview_in_chone(src, out_dir, amounts):
    """One image per amount, each in two versions: with the current Mould 1 drawn behind, and without.
    Mould 1 is laid inside the Chone like renders/mould1-minified-chone.png: wrist middles together, raised 0.3"."""
    db = ezdxf.readfile(src).entitydb
    C = np.array(poly(db[CHONE_CUT]))
    S = np.array(poly(db[CHONE_STITCH]))
    raw, fx, M = load(src)
    shift = wrist_mid(C) + [0, 0.3] - wrist_mid(M)
    for amt in amounts:
        N, info = lengthen(M, amt)
        len0, len1 = report(M, N, info, amt)
        for with_old in (True, False):
            fig, ax = plt.subplots(figsize=(8, 9))
            ax.plot(*np.vstack([C, C[:1]]).T, "k", lw=1, label="Chone cut line")
            ax.plot(*np.vstack([S, S[:1]]).T, "k--", lw=0.8, label="Chone stitch line")
            if with_old:
                ax.plot(*np.vstack([M, M[:1]]).T + shift[:, None], color="0.65", lw=1, label=f"Mould 1 now ({NAME or 'minified Chone'})")
            ax.plot(*np.vstack([N, N[:1]]).T + shift[:, None], color="orange", lw=2, label=f"Mould 1, thumb {amt:g}\" longer")
            ax.set_aspect("equal")
            ax.grid(alpha=0.25)
            ax.legend(loc="upper left", fontsize=8)
            ax.set_title(f"PREVIEW (no DXF): Mould 1 thumb {amt:g}\" longer, neck to tip {len0:.2f}\" → {len1:.2f}\"\n"
                         f"{Path(src).name}, flipped back, wrist middles together, raised 0.3\"", fontsize=10)
            name = f"mould1-{NAME + '-' if NAME else ''}thumb-longer-{amt:g}in-preview{'-with-old' if with_old else ''}.png"
            dst = Path(out_dir) / name
            if dst.exists():
                sys.exit(f"refusing to overwrite existing file: {dst}")
            fig.savefig(dst, dpi=100, bbox_inches="tight")
            plt.close(fig)
            print(f"   wrote {dst}")


def write(src, dst, png, amount):
    if Path(dst).exists():
        sys.exit(f"refusing to overwrite existing file: {dst}")
    doc = ezdxf.readfile(src)
    db = doc.entitydb
    raw, fx, M = load(src)
    N, info = lengthen(M, amount)
    len0, len1 = report(M, N, info, amount)
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
    S = chk * [-1, 1] + [2 * fx, 0]
    still = Polygon(S).exterior
    off = max(still.distance(Point(q)) for q, ww in zip(M, info["w"]) if ww == 0)
    print(f"Rest of Mould 1 off its old line by at most {off:.4f} in")
    print(f"Saved {dst} (Mould 1 now {np.ptp(chk[:, 0]):.2f} x {np.ptp(chk[:, 1]):.2f} in, was {np.ptp(raw[:, 0]):.2f} x {np.ptp(raw[:, 1]):.2f})")
    fig, ax = plt.subplots(figsize=(8, 9))
    draw(ax, M, S, info, amount, len0, len1)
    ax.legend(loc="upper right", fontsize=8)
    ax.set_title(f"Mould 1 thumb {amount:g}\" longer (from the saved DXF), shown flipped: {len0:.2f}\" → {len1:.2f}\"\n{Path(src).name}", fontsize=10)
    fig.savefig(png, dpi=100, bbox_inches="tight")


def write_smooth(src, dst, png, amount, preview_check=True):
    """Like write(), but for an outline that is already a smooth Bezier chain (e.g. the smoothed Mould 1).

    Instead of re-drawing the whole outline through sample points, this moves only the control points of the thumb's
    own curves, so every other curve (corners, straight bottom edge) stays exactly as it is. Each control point slides
    along the thumb's centre line by amount * w, where w goes from 0 on the neck line (notch to the nearest bottom-edge
    point) to 1 at the tip, easing in from the neck (zero slope there) so no kink appears where the thumb meets the hand.
    """
    from dxf_link import entity_chain
    if Path(dst).exists():
        sys.exit(f"refusing to overwrite existing file: {dst}")
    doc = ezdxf.readfile(src)
    ent = doc.entitydb[MOULD1]
    raw, fx, M = load(src)
    _, info = lengthen(M, amount)
    flip = lambda P: np.asarray(P) * [-1, 1] + [2 * fx, 0]  # DXF <-> the flipped frame M lives in (its own inverse)
    chain = np.array(entity_chain(ent, 1.0))
    F = flip(chain)  # (N, 4, 2), flipped frame
    N = len(F)
    J = F[:, 0]
    # the thumb runs between two curve joints: the one at the notch and the one at the neck's bottom-edge point. The
    # neck line goes through exactly those two joints, so the shift is zero there and nothing past them moves.
    j1 = int(np.argmin(np.hypot(*(J - M[info["mn"]]).T)))
    j2 = int(np.argmin(np.hypot(*(J - M[info["i_neck"]]).T)))
    tip = M[info["i_tip"]]
    jt = int(np.argmin(np.hypot(*(F[:, 1:3].mean(1) - tip).T)))
    run = lambda s0, s1: [(s0 + k) % N for k in range((s1 - s0) % N)]
    moving = run(j1, j2) if jt in run(j1, j2) else run(j2, j1)
    notch, neck = J[j1], J[j2]
    a = info["a"]
    nrm = np.array([-(neck - notch)[1], (neck - notch)[0]])
    nrm /= np.linalg.norm(nrm)
    if (tip - notch) @ nrm < 0:
        nrm = -nrm  # points from the neck line out toward the tip
    reach = (tip - notch) @ nrm
    EASE = 0.25  # share of the neck-to-tip distance over which the stretch eases in from the neck line

    def g(v):
        v = np.clip(v, 0, None)
        return np.where(v < EASE, v * v / (2 * EASE), v - EASE / 2)

    def shift(P):  # P in the flipped frame -> moved points
        w = g(((P - notch) @ nrm) / reach) / g(np.array(1.0))
        return P + np.outer(amount * w, a)

    G = F.copy()
    for j in moving:
        G[j] = shift(F[j])
    # one point per joint: the curves either side of a joint moved the same point the same way, so they still meet;
    # keep the handles either side of each moved joint in line, so the outline stays smooth there
    kinks = []
    for j in sorted(set(moving) | {(moving[0] - 1) % N}):  # every joint a moved curve touches
        k = (j + 1) % N
        P, h0, h1 = G[j][3], G[j][2], G[k][1]
        u0, u1 = P - h0, h1 - P
        l0, l1 = np.linalg.norm(u0), np.linalg.norm(u1)
        if l0 < 1e-9 or l1 < 1e-9:
            continue
        ang = np.degrees(np.arccos(np.clip(u0 @ u1 / l0 / l1, -1, 1)))
        before = F[j][3] - F[j][2], F[k][1] - F[k][0]
        was = np.degrees(np.arccos(np.clip(before[0] @ before[1] / np.linalg.norm(before[0]) / np.linalg.norm(before[1]), -1, 1)))
        if was < 0.5 and ang > 1e-6:  # it was smooth: make it exactly smooth again
            d = u0 / l0 + u1 / l1
            d /= np.linalg.norm(d)
            G[j][2], G[k][1] = P - d * l0, P + d * l1
        kinks.append(ang if was < 0.5 else 0)
    out = flip(G)
    ctrl = [out[0][0]] + [p for b in out for p in b[1:]]
    knots = [0, 0, 0, 0] + [x for j in range(1, N) for x in (j, j, j)] + [N] * 4
    ent.control_points = [(x, y, 0) for x, y in ctrl]
    ent.knots = [float(x) for x in knots]
    ent.fit_points = []
    ent.dxf.degree, ent.dxf.flags = 3, 8
    doc.saveas(dst)

    # checks, from the saved file
    chk = np.array(poly(ezdxf.readfile(dst).entitydb[MOULD1]))
    S = resample(flip(chk), STEP)
    len0 = ((M[info["arc"]] - info["m"]) @ a).max()
    len1 = ((S - info["m"]) @ a).max()
    rest = np.array([q for q, ww in zip(M, info["w"]) if ww == 0 and (q - notch) @ nrm < 0])
    still = Polygon(flip(chk)).exterior
    off = max(still.distance(Point(q)) for q in rest)
    Np, _ = lengthen(M, amount)
    vs = max(Polygon(Np).exterior.distance(Point(q)) for q in S)
    st = np.linspace(0.5, 2.5, 5)
    w0 = widths(LineString(M[info["arc"]]), info["m"], a, st)
    print(f"+{amount:g}\": {len(moving)} of {N} curves moved; thumb neck-to-tip {len0:.3f} -> {len1:.3f} in; "
          f"area {Polygon(M).area:.2f} -> {Polygon(S).area:.2f} sq in; valid {Polygon(S).is_valid}")
    print(f"   rest of Mould 1 off its old line by at most {off:.5f} in; largest bend at a moved joint before its handles were lined up again {max(kinks):.4f} deg (0 after); "
          f"differs from the preview by at most {vs:.3f} in")
    print(f"Saved {dst}")
    fig, ax = plt.subplots(figsize=(8, 9))
    draw(ax, M, S, info, amount, len0, len1)
    ax.legend(loc="upper right", fontsize=8)
    ax.set_title(f"Mould 1 thumb {amount:g}\" longer (from the saved DXF), shown flipped: {len0:.2f}\" → {len1:.2f}\"\n{Path(dst).name}", fontsize=10)
    ax.set_xlim(M[:, 0].min() - 1.2, M[:, 0].min() + 7)
    ax.set_ylim(M[:, 1].min() - 0.5, M[:, 1].min() + 7)
    fig.savefig(png, dpi=100, bbox_inches="tight")


if __name__ == "__main__":
    if "--name" in sys.argv:
        i = sys.argv.index("--name")
        NAME = sys.argv[i + 1]
        del sys.argv[i:i + 2]
    if sys.argv[1] == "preview-in-chone":
        preview_in_chone(sys.argv[2], sys.argv[3], [float(x) for x in sys.argv[4:]])
    elif sys.argv[1] == "preview":
        preview(sys.argv[2], sys.argv[3], [float(x) for x in sys.argv[4:]])
    elif sys.argv[1] == "write-smooth":
        write_smooth(sys.argv[2], sys.argv[3], sys.argv[4], float(sys.argv[5]))
    else:
        write(sys.argv[2], sys.argv[3], sys.argv[4], float(sys.argv[5]))
