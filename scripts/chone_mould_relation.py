"""How the foam moulds relate to the leather pieces that cover them.

Lays Mould 1 (flipped) inside the Chone stitch line at the position where the gap
is most even, and reports the gap region by region. Also compares Mould 2 to
Mould 1 and the Cuff Mould to the Chone Cuff.

Usage: uv run --with ezdxf --with shapely --with matplotlib --with scipy \
       python scripts/chone_mould_relation.py "dxf/Laces Boxing 14OZ (1).dxf" renders/chone-mould-relation.png
"""
import sys
import ezdxf, numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from shapely.geometry import Polygon
from shapely import affinity
from scipy.optimize import minimize
from render_pieces import poly

doc = ezdxf.readfile(sys.argv[1]); db = doc.entitydb
P = lambda h: Polygon(poly(db[h]))
ci, co = P("96"), P("95")
m1 = affinity.scale(P("320"), -1, 1, origin="centroid")
m2 = affinity.scale(P("2FE"), -1, 1, origin="centroid")
cui, cm = P("311"), P("E7")

def samples(g, n): return [g.exterior.interpolate(t, normalized=True) for t in np.linspace(0, 1, n, endpoint=False)]

def fit(outer, m, n=400, scale=False, turns=range(-20, 25, 5)):
    """Place m inside outer so the gap is as even as possible. Returns placed m, gaps."""
    pts = samples(outer, n)
    def place(p):
        g = affinity.rotate(m, p[0], origin="centroid")
        if scale: g = affinity.scale(g, p[3], p[3], origin="centroid")
        return affinity.translate(g, outer.centroid.x - m.centroid.x + p[1], outer.centroid.y - m.centroid.y + p[2])
    def gaps(g): return np.array([(g.exterior.distance(q) if not g.contains(q) else -g.exterior.distance(q)) for q in pts])
    best = None
    for r0 in turns:
        r = minimize(lambda p: gaps(place(p)).std(), [r0, 0, 0], method="Nelder-Mead")
        if best is None or r.fun < best.fun: best = r
    g = place(best.x)
    return g, pts, gaps(g), best.x[0]

def dims(g): b = g.bounds; return b[2] - b[0], b[3] - b[1]

g1, pts, gap, rot = fit(ci, m1)
b = ci.bounds
# regions on the Chone (x,y measured from the Chone stitch line's lower-left)
def region(q):
    x, y = q.x - b[0], q.y - b[1]
    if y < 0.05 and x > 5.5: return "wrist edge (bottom)"
    if y > 12.5: return "fingertips (top)"
    if x > 10.5: return "knuckle side (right)"
    if x < 2.0 or (y < 4.5 and x < 5.5): return "thumb tip / thumb outer"
    if 4.0 < y < 7.0 and x < 5.0: return "thumb crotch"
    if 5.5 <= x and y < 1.5: return "wrist edge (bottom)"
    return "index-finger side (left)"
rows = {}
for q, d in zip(pts, gap): rows.setdefault(region(q), []).append(d)
print(f"Mould 1 turned {rot:.1f} deg to fit. Gap chone stitch line -> mould 1:")
for k, v in rows.items(): print(f"  {k:26s} min {min(v):5.2f}  avg {np.mean(v):5.2f}  max {max(v):5.2f}")
print(f"  overall avg {gap.mean():.2f}")

# Mould 2 is drawn upside down on the sheet: try it both flipped and unflipped, any angle
m2u = P("2FE")
cands = [fit(m1, c, 300, turns=range(-180, 180, 20)) + (c,) for c in (m2, m2u)]
g2, pts2, gap2, rot2, _ = min(cands, key=lambda c: c[2].std())
gc, ptsc, gapc, rotc = fit(cui, cm, 200)
for name, a, bb in [("Mould 2 / Mould 1", m2, m1), ("Cuff Mould / Chone Cuff inner", cm, cui), ("Mould 1 / Chone inner", m1, ci)]:
    wa, la = dims(a); wb, lb = dims(bb)
    print(f"{name:30s} W {wa/wb:.3f}  L {la/lb:.3f}  perimeter {a.exterior.length/bb.exterior.length:.3f}  sqrt(area) {(a.area/bb.area)**.5:.3f}")
print(f"Mould 2 inside Mould 1: gap avg {gap2.mean():.2f} min {gap2.min():.2f} max {gap2.max():.2f}")
print(f"Cuff Mould inside Chone Cuff inner: gap avg {gapc.mean():.2f} min {gapc.min():.2f} max {gapc.max():.2f}")

fig, axs = plt.subplots(1, 3, figsize=(20, 8), gridspec_kw=dict(width_ratios=[1.4, 1, 0.7]))
ax = axs[0]
ax.plot(*co.exterior.xy, color="0.75", lw=0.8, label="Chone cut line")
ax.plot(*ci.exterior.xy, color="0.3", lw=1, label="Chone stitch line")
ax.fill(*g1.exterior.xy, color="tab:orange", alpha=0.25); ax.plot(*g1.exterior.xy, color="tab:orange", lw=1.2, label="Mould 1 (flipped)")
for q, d in zip(pts, gap):
    ax.plot(q.x, q.y, "o", ms=3.5, color=plt.cm.RdYlGn(np.clip(d / 1.5, 0, 1)))
for k, v in rows.items():
    qs = [q for q in pts if region(q) == k]; mx = np.mean([q.x for q in qs]); my = np.mean([q.y for q in qs])
    ax.annotate(f"{k}\navg {np.mean(v):.2f}\"", (mx, my), (mx + (1.6 if mx < ci.centroid.x else -1.6) * 0 , my),
                fontsize=9, ha="center", va="center", bbox=dict(fc="white", ec="0.7", alpha=0.9))
ax.set_title(f"Chone vs Mould 1: gap from stitch line to foam\n(red 0\", yellow 0.75\", green 1.5\"+), average {gap.mean():.2f}\"")
ax.legend(loc="lower left", fontsize=9)
for a, (outer, inner, gp, t) in zip(axs[1:], [(m1, g2, gap2, "Mould 2 inside Mould 1"), (cui, gc, gapc, "Cuff Mould inside Chone Cuff stitch line")]):
    a.plot(*outer.exterior.xy, color="0.3"); a.fill(*inner.exterior.xy, color="tab:blue", alpha=0.25); a.plot(*inner.exterior.xy, color="tab:blue")
    a.set_title(f"{t}\ngap avg {gp.mean():.2f}\", min {gp.min():.2f}\", max {gp.max():.2f}\"")
for a in axs: a.set_aspect("equal"); a.axis("off")
fig.tight_layout(); fig.savefig(sys.argv[2], dpi=90, facecolor="white")
