"""Lay the Front Palm over the joined Chone + Chone Cuff.

The palm is optionally scaled (uniformly, about the corner below), then moved, never
rotated or mirrored. The corner on the palm's left side where the thumb-notch curve
meets the straight lower side (outer line) is placed on the left end of the
Chone/Cuff join (the cuff's top-left outer corner).

Colours: Chone black, Chone Cuff blue, Front Palm red.

Usage: python scripts/overlay_palm.py "dxf/Laces Boxing 14OZ (1).dxf" renders/palm-over-chone-with-cuff.png [scale]
       scale defaults to 1.0 (as drawn); e.g. 0.96 for 96%.
"""
import math
import sys

import ezdxf
from ezdxf.math import Matrix44

from join_chone_cuff import join, piece_handles, render
from render_pieces import poly

PALM_OUTER = "2EE"
PALM_INNER = "2EF"  # bbox centre sits in the lace slot, so add it explicitly


def notch_corner(e):
    """Lower corner of the thumb notch on the palm's left side (sharp turn, left edge,
    above the bottom-left corner)."""
    pts = poly(e)
    r = [pts[0]]
    for p in pts[1:]:
        if math.dist(p, r[-1]) >= 0.03:
            r.append(p)
    xmin = min(p[0] for p in r)
    ymin = min(p[1] for p in r)
    corners = []
    for i in range(len(r)):
        a, b, c = r[i - 1], r[i], r[(i + 1) % len(r)]
        turn = math.atan2(c[1] - b[1], c[0] - b[0]) - math.atan2(b[1] - a[1], b[0] - a[0])
        deg = abs((math.degrees(turn) + 180) % 360 - 180)
        if deg > 20 and b[0] < xmin + 0.5 and b[1] > ymin + 0.5:
            corners.append(b)
    return min(corners, key=lambda p: p[1])  # the lower of the two notch corners


def place_palm(doc, info, scale=1.0):
    """Scale the palm about its notch corner and move that corner onto the join point.
    Returns (palm handles, original corner, target point)."""
    db = doc.entitydb
    palm = piece_handles(doc.modelspace(), db[PALM_OUTER]) | {PALM_INNER}
    px, py = notch_corner(db[PALM_OUTER])
    tx, ty = info["join_left"]
    move = Matrix44.chain(
        Matrix44.translate(-px, -py, 0),
        Matrix44.scale(scale, scale, 1),
        Matrix44.translate(tx, ty, 0),
    )
    for h in palm:
        db[h].transform(move)
    return palm, (px, py), (tx, ty)


def main(dxf, out, scale=1.0):
    doc = ezdxf.readfile(dxf)
    keep, info = join(doc)
    db = doc.entitydb
    palm, (px, py), (tx, ty) = place_palm(doc, info, scale)
    for h in palm:
        db[h].dxf.color = 1  # red

    b = render(doc, keep | palm, out)
    print(f"palm scale {scale:.3f}; corner ({px:.3f},{py:.3f}) -> join point ({tx:.3f},{ty:.3f})")

    # how the palm's outline sits against the back piece
    from ezdxf import bbox as _bb
    pb = _bb.extents([db[PALM_OUTER]])
    cuff = _bb.extents([db["310"]])
    chone = _bb.extents([db["95"]])
    print(f"palm outer: x {pb.extmin.x:.3f}..{pb.extmax.x:.3f}  y {pb.extmin.y:.3f}..{pb.extmax.y:.3f}")
    print(f"cuff outer: x {cuff.extmin.x:.3f}..{cuff.extmax.x:.3f}  y {cuff.extmin.y:.3f}..{cuff.extmax.y:.3f}")
    print(f"chone outer: x {chone.extmin.x:.3f}..{chone.extmax.x:.3f}  y {chone.extmin.y:.3f}..{chone.extmax.y:.3f}")
    print(f"palm bottom vs cuff bottom: {pb.extmin.y - cuff.extmin.y:+.3f} (positive = palm ends higher)")
    print(f"palm right vs chone right: {pb.extmax.x - chone.extmax.x:+.3f} (positive = palm sticks out)")
    print(f"overall size: W={b.size.x:.3f} L={b.size.y:.3f}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], float(sys.argv[3]) if len(sys.argv) > 3 else 1.0)
