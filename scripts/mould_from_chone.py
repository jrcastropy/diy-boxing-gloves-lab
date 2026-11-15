"""Design a foam mould that fits the Chone, made from the Chone's own stitch line.

The Chone has to cover the mould's top face and wrap down its side wall so the stitch line
lands on the palm face, where it meets the palm. Laid flat, that means the stitch line must
sit one foam thickness (T) outside the mould all round, plus a little ease (default 0.1")
for the leather turning over the foam's top edge. So the mould is the Chone's stitch
line (inner line) pulled in by T, except along the wrist edge, which is sewn to the cuff and
stays flush with the Chone's. Optional extra allowances (tip, thumb) pull the fingertip end
and the thumb tip in further, for the extra length the Chone uses going round a curl.
Corners are rounded (radius ROUND) so the foam has no sharp points.

Writes:
  - a DXF (inches) with the mould on layer MOULD, drawn the same way round as the Chone
    (not mirrored like the original moulds), in the viewer's frame: origin at the middle of
    the Chone stitch line's wrist edge, y toward the fingertips. The Chone's stitch line is
    on layer CHONE_STITCH_REF for reference.
  - optionally a Chone Fit Lab config (one mould + the Chone) to load in the viewer.

Usage: uv run --with ezdxf --with shapely python scripts/mould_from_chone.py \
       "dxf/Laces Boxing 14OZ (1).dxf" "dxf/Mould from Chone 1in.dxf" \
       --foam 1.0 [--tip 0] [--thumb 0] [--config viewer/config/x.json --base viewer/config/y.json]
"""
import argparse, json
import ezdxf, numpy as np
from shapely.geometry import Polygon, box
from shapely.geometry.polygon import orient
from shapely import affinity
from render_pieces import poly
from join_chone_cuff import horizontal_edge

ap = argparse.ArgumentParser()
ap.add_argument("dxf"); ap.add_argument("out")
ap.add_argument("--foam", type=float, default=1.0, help="foam thickness T, inches")
ap.add_argument("--tip", type=float, default=0.0, help="extra pulled in at the fingertip end, inches")
ap.add_argument("--thumb", type=float, default=0.0, help="extra pulled in at the thumb tip, inches")
ap.add_argument("--ease", type=float, default=0.1, help="extra inset for the Chone turning over the foam edge, inches")
ap.add_argument("--round", type=float, default=0.25, help="corner rounding radius, inches")
ap.add_argument("--config"); ap.add_argument("--base", help="config to take the Chone's settings from")
a = ap.parse_args()

db = ezdxf.readfile(a.dxf).entitydb
ci = Polygon(poly(db["96"]))                       # Chone stitch (inner) line
bx0, bx1, by = horizontal_edge(db["96"], "bottom")
ci = affinity.translate(ci, -(bx0 + bx1) / 2, -by)  # viewer frame
T, R = a.foam, a.round
I = T + a.ease  # inset: foam thickness plus ease for the turn over the edge

# Extend the stitch line straight down past the wrist so the inset doesn't pull the wrist edge in,
# inset by T, round the corners, then cut back at the wrist line.
x0, _, x1, _ = ci.bounds
ext = ci.union(box(-(bx1 - bx0) / 2, -3 * T - 1, (bx1 - bx0) / 2, 0.05))
m = ext.buffer(-(I + R), join_style="round").buffer(R, join_style="round")
m = m.intersection(box(x0 - 1, 0, x1 + 1, 99))
# Extra allowances for curling: trim the fingertip end and the thumb tip back further.
_, _, _, ytop = ci.bounds
if a.tip > 0:
    m = m.intersection(box(x0 - 1, -1, x1 + 1, ytop - I - a.tip)).buffer(-R).buffer(R)
if a.thumb > 0:  # the thumb lobe is the part left of the thumb crotch
    tx = ci.bounds[0]
    thumb_cut = ci.buffer(-(I + a.thumb)).union(box(tx + I + a.thumb + 2.5, -1, x1 + 1, 99))
    m = m.intersection(thumb_cut).buffer(-R).buffer(R)
if m.geom_type != "Polygon":
    m = max(m.geoms, key=lambda g: g.area)
m = orient(Polygon(m.exterior), 1.0)

def ring(g, step):
    L = g.exterior.length; n = int(L / step)
    return [g.exterior.interpolate(t, normalized=True).coords[0] for t in np.linspace(0, 1, n, endpoint=False)]

# Report: gap from the stitch line to the mould, by region (wrist edge left out)
pts = [p for p in ring(ci, 0.05) if p[1] > 0.05]
gap = np.array([m.exterior.distance(__import__("shapely").geometry.Point(p)) for p in pts])
print(f"mould {m.bounds[2]-m.bounds[0]:.2f}\" wide x {m.bounds[3]-m.bounds[1]:.2f}\" long, area {m.area:.1f} sq in")
print(f"stitch line to mould: min {gap.min():.2f}\"  median {np.median(gap):.2f}\"  max {gap.max():.2f}\"")

doc = ezdxf.new("R2018"); doc.header["$INSUNITS"] = 1
doc.layers.add("MOULD", color=2); doc.layers.add("CHONE_STITCH_REF", color=8)
msp = doc.modelspace()
msp.add_lwpolyline(ring(m, 0.05), close=True, dxfattribs={"layer": "MOULD"})
msp.add_lwpolyline(list(ci.exterior.coords)[:-1], close=True, dxfattribs={"layer": "CHONE_STITCH_REF"})
doc.saveas(a.out)
print("wrote", a.out)

if a.config:
    base = json.load(open(a.base)) if a.base else {}
    chone = next((i for i in base.get("items", []) if i.get("key") == "chone"), {"key": "chone", "builtin": "chone"})
    chone = {**chone, "drape": 90, "edgeR": 0.1, "target": T, "show": True}
    pose = {"x": chone.get("pose", {}).get("x", 0), "y": chone.get("pose", {}).get("y", 0), "rot": 0, "scale": 100}
    chone["pose"] = {**pose, "scale": chone.get("pose", {}).get("scale", 100)}
    mould = {"key": "mould", "label": "Mould (from Chone)", "kind": "mould", "col": "foam1",
             "outline": [[round(x, 4), round(y, 4)] for x, y in ring(m, 0.12)],
             "thick": T, "opacity": 1, "show": True, "pose": pose}
    cfg = {"app": "chone-fit-lab", "version": 2, "items": [mould, chone], "item": "mould", "noOverlap": False,
           "newFor": {"mould": True, "chone": True}, "hinges": []}
    json.dump(cfg, open(a.config, "w"), indent=2)
    print("wrote", a.config)
