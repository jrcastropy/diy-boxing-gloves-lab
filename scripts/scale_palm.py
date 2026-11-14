"""Save a copy of the pattern with the Front Palm scaled (everything else untouched).

The palm and everything inside it (inner line, lace slot, holes, dashed lines, label)
are scaled uniformly about the palm's thumb-notch corner (outer line), so the piece
stays in the same spot on the sheet. The original DXF is not modified.

Usage: python scripts/scale_palm.py "dxf/Laces Boxing 14OZ (1).dxf" "dxf/Laces Boxing 14OZ - palm 96%.dxf" 0.96
"""
import sys

import ezdxf
from ezdxf.math import Matrix44

from join_chone_cuff import piece_handles
from overlay_palm import PALM_INNER, PALM_OUTER, notch_corner


def main(src, dst, scale):
    doc = ezdxf.readfile(src)
    db = doc.entitydb
    palm = piece_handles(doc.modelspace(), db[PALM_OUTER]) | {PALM_INNER}
    px, py = notch_corner(db[PALM_OUTER])
    m = Matrix44.chain(
        Matrix44.translate(-px, -py, 0),
        Matrix44.scale(scale, scale, 1),
        Matrix44.translate(px, py, 0),
    )
    for h in palm:
        db[h].transform(m)
    doc.saveas(dst)
    print(f"scaled {len(palm)} palm entities by {scale} about ({px:.3f},{py:.3f}); saved {dst}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], float(sys.argv[3]))
