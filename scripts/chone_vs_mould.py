import ezdxf, numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from shapely.geometry import Polygon, LineString, Point
from shapely import affinity
from pathlib import Path
from render_pieces import poly
from join_chone_cuff import horizontal_edge
ROOT = Path(__file__).resolve().parent.parent
doc = ezdxf.readfile(ROOT / "dxf" / "Laces Boxing 14OZ - palm 96% cuff matched.dxf"); db = doc.entitydb
ch = Polygon(poly(db["96"])); cho = Polygon(poly(db["95"]))
bx0, bx1, by = horizontal_edge(db["96"], "bottom")
seam = ch.exterior.difference(LineString([(bx0-1e-3,by),(bx1+1e-3,by)]).buffer(1e-3))
m0 = affinity.scale(Polygon(poly(db["320"])), -1, 1)
fig, axs = plt.subplots(1, 4, figsize=(20, 7))
for ax, s in zip(axs, (1.0, 1.10, 1.15, 1.20)):
    o = (ch.centroid.x, by)
    c, co, sm = (affinity.scale(g, s, s, origin=o) for g in (ch, cho, seam))
    best = (-9,)
    for r in np.arange(6, 12.1, 0.5):
        mr = affinity.rotate(m0, r, origin="centroid")
        mr = affinity.translate(mr, c.centroid.x - mr.centroid.x, by - mr.bounds[1])
        for dx in np.arange(-1.5, 1.51, 0.05):
            for dy in np.arange(0, 3.01, 0.05):
                mm = affinity.translate(mr, dx, dy)
                if c.contains(mm):
                    g = sm.distance(mm)
                    if g > best[0]: best = (g, mm)
    g, mm = best
    # gaps along the seam
    L = sm.length; samp = [sm.interpolate(t) for t in np.linspace(0, L, 400)]
    d = [p.distance(mm) for p in samp]
    for (p, dd) in zip(samp, d):
        ax.plot(p.x, p.y, "o", ms=3, color=plt.cm.RdYlGn(min(dd / 2.0, 1.0)))
    ax.plot(*co.exterior.xy, color="0.6", lw=0.7)
    ax.fill(*mm.exterior.xy, color="tab:orange", alpha=0.3); ax.plot(*mm.exterior.xy, color="tab:orange", lw=1)
    p = min(samp, key=lambda q: q.distance(mm))
    ax.set_title(f"Chone at {s:.0%}\ntightest gap {g:.2f}\" ({g*25.4:.0f} mm), median {np.median(d):.2f}\"", fontsize=12)
    ax.set_aspect("equal"); ax.axis("off")
    W = co.bounds[2]-co.bounds[0]; H = co.bounds[3]-co.bounds[1]
    ax.text(co.bounds[0], co.bounds[1]-0.6, f"Chone outer {W:.2f}\" x {H:.2f}\"", fontsize=10)
    print(s, round(g,2), round(float(np.median(d)),2), round(W,2), round(H,2))
fig.suptitle("Foam Mould 1 (orange, flipped to match) laid inside the Chone stitch line. Dots = room left on the seam to wrap over the 2\" foam edge: red 0\", yellow 1\", green 2\"+", fontsize=12)
fig.tight_layout(rect=(0, 0, 1, 0.93)); fig.savefig(ROOT / "renders" / "chone-vs-mould1.png", dpi=90, facecolor="white")
