"""Save a copy of the pattern with the Front Palm AND the Thumb scaled by the same amount
(everything else untouched).

- Front Palm and everything inside it (inner line, lace slot, holes, dashed lines, label):
  scaled about its thumb-notch corner (outer line), like scale_palm.py.
- Thumb and everything inside it (inner line, holes, label): scaled about the centre of
  its outer line's bounding box.
Both stay in the same spot on the sheet. Scaling both by the same amount keeps the
Thumb seam matched. The source DXF is not modified, and the output must not exist yet.

Usage: python scripts/scale_palm_thumb.py "dxf/Laces Boxing 14OZ - palm 96% cuff matched.dxf" "dxf/Laces Boxing 14OZ - palm+thumb 95%.dxf" 0.95
"""
import sys
from pathlib import Path

import ezdxf
from ezdxf import bbox
from ezdxf.math import Matrix44

from join_chone_cuff import piece_handles
from overlay_palm import PALM_INNER, PALM_OUTER, notch_corner

THUMB_OUTER = "32E"


def about(px, py, s):
    return Matrix44.chain(Matrix44.translate(-px, -py, 0), Matrix44.scale(s, s, 1), Matrix44.translate(px, py, 0))


def main(src, dst, scale):
    if Path(dst).exists():
        sys.exit(f"refusing to overwrite existing file: {dst}")
    doc = ezdxf.readfile(src)
    db = doc.entitydb
    msp = doc.modelspace()

    palm = piece_handles(msp, db[PALM_OUTER]) | {PALM_INNER}
    thumb = piece_handles(msp, db[THUMB_OUTER])
    assert not palm & thumb

    px, py = notch_corner(db[PALM_OUTER])
    b = bbox.extents([db[THUMB_OUTER]])
    tx, ty = (b.extmin.x + b.extmax.x) / 2, (b.extmin.y + b.extmax.y) / 2

    for h in palm:
        db[h].transform(about(px, py, scale))
    for h in thumb:
        db[h].transform(about(tx, ty, scale))
    doc.saveas(dst)
    print(f"palm: {len(palm)} entities scaled by {scale} about ({px:.3f},{py:.3f})")
    print(f"thumb: {len(thumb)} entities scaled by {scale} about ({tx:.3f},{ty:.3f})")
    print(f"saved {dst}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], float(sys.argv[3]))
