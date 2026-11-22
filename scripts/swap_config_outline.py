"""Copy a Chone Fit Lab config, swapping one item's outline for the same piece from another DXF.

Everything else in the config is kept: the other items, every bend line, poses, layers and
settings. The item's outline must have come from OLD_DXF (via the viewer's DXF import, which
mirrors and/or moves it). This finds that mirror + shift by matching OLD_DXF's piece onto the
item's outline (it stops if they don't match), then puts the piece from NEW_DXF through the
exact same mirror + shift, so the parts that didn't change land exactly where they were.
The item's pose is kept as it is, adjusted for the outline's new centre when the pose turns
or scales the item (the viewer turns and scales about that centre).

Refuses to overwrite an existing file.

Usage: python scripts/swap_config_outline.py CONFIG ITEM_KEY OLD_DXF NEW_DXF OUT_CONFIG [HANDLE]
  python scripts/swap_config_outline.py viewer/config/chone-fit-manual-test-minified-chone.json item3 \
    "dxf/Laces Boxing 14OZ - mould1 minified chone.dxf" "dxf/Laces Boxing 14OZ - mould1 minified chone thumb +0.5in.dxf" \
    viewer/config/chone-fit-manual-test-minified-chone-thumb+0.5in.json
HANDLE is the piece's outline in the DXF (default 320, Mould 1).
"""
import json
import math
import sys
from pathlib import Path

import ezdxf
import numpy as np
from shapely.geometry import Point, Polygon

from render_pieces import poly

STEP = 0.12  # outline spacing, the same as the viewer's DXF import
MATCH = 0.01  # inches: OLD_DXF's piece must sit this close to the item's outline


def resample_ring(pts, step):
    """Even spacing round a closed outline, counter-clockwise (like the viewer's resampleRing)."""
    xy = np.vstack([pts, pts[:1]])
    d = np.r_[0, np.cumsum(np.hypot(*np.diff(xy, axis=0).T))]
    t = np.arange(max(16, round(d[-1] / step))) * d[-1] / max(16, round(d[-1] / step))
    out = np.c_[np.interp(t, d, xy[:, 0]), np.interp(t, d, xy[:, 1])]
    return out if Polygon(out).exterior.is_ccw else out[::-1]


def fit_shift(P, R):
    """Shift that lays outline P onto the points R, and the largest leftover distance."""
    off = R.mean(0) - P.mean(0)
    for _ in range(15):
        ring = Polygon(P + off).exterior
        near = np.array([ring.interpolate(ring.project(Point(p))).coords[0] for p in R])
        off = off + (R - near).mean(0)
    ring = Polygon(P + off).exterior
    return off, max(ring.distance(Point(p)) for p in R)


def main(cfg_path, key, old_dxf, new_dxf, out, handle="320"):
    if Path(out).exists():
        sys.exit(f"refusing to overwrite existing file: {out}")
    cfg = json.load(open(cfg_path))
    item = next((i for i in cfg["items"] if i["key"] == key), None)
    if item is None or "outline" not in item:
        sys.exit(f"no item '{key}' with an outline in {cfg_path}")
    R = np.array(item["outline"])

    old = np.array(poly(ezdxf.readfile(old_dxf).entitydb[handle]))
    best = min(((m,) + fit_shift(old * [m, 1], R) for m in (-1, 1)), key=lambda r: r[2])
    mirror, off, err = best
    print(f"{key} = {Path(old_dxf).name} {'mirrored' if mirror < 0 else 'as drawn'}, shifted {off.round(4)}; off by at most {err:.4f} in")
    if err > MATCH:
        sys.exit(f"the item's outline doesn't match {old_dxf} (off by {err:.3f} in), stopping")

    new = np.array(poly(ezdxf.readfile(new_dxf).entitydb[handle]))
    ring = resample_ring(new * [mirror, 1] + off, STEP)
    ring = [[round(x, 4), round(y, 4)] for x, y in ring]

    # Keep the pose meaning the same: the viewer turns/scales about the outline's centre.
    c_old, c_new = R.mean(0), np.array(ring).mean(0)
    p = item.get("pose", {})
    s, a = p.get("scale", 100) / 100, math.radians(p.get("rot", 0))
    if s != 1 or a != 0:
        d = c_old - c_new
        rd = np.array([d[0] * math.cos(a) - d[1] * math.sin(a), d[0] * math.sin(a) + d[1] * math.cos(a)]) * s
        p["x"] = round(p.get("x", 0) + d[0] - rd[0], 4)
        p["y"] = round(p.get("y", 0) + d[1] - rd[1], 4)
        print(f"pose x, y adjusted to {p['x']}, {p['y']} (outline centre moved {d.round(4)})")

    item["outline"] = ring
    cfg.pop("savedAt", None)
    json.dump(cfg, open(out, "w"), indent=1)
    print(f"Saved {out}: {key} now from {Path(new_dxf).name} ({len(ring)} points, area {Polygon(ring).area:.2f} sq in, "
          f"was {Polygon(R).area:.2f}); {len(cfg['hinges'])} bends and {len(cfg['items'])} items kept")


if __name__ == "__main__":
    main(*sys.argv[1:])
