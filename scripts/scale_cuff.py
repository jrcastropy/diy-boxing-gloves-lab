"""Scale the Chone Cuff so its top edge (outer line) is exactly as long as the Chone's
bottom edge (outer line). Everything else is left untouched.

The cuff is scaled uniformly about its top-left outer corner, so it stays in the same
spot on the sheet. Scale = Chone bottom outer / Cuff top outer.

Usage: python scripts/scale_cuff.py "dxf/Laces Boxing 14OZ - palm 96%.dxf" "dxf/Laces Boxing 14OZ - palm 96% cuff matched.dxf"
"""
import sys

import ezdxf
from ezdxf.math import Matrix44

from join_chone_cuff import CHONE_OUTER, CUFF_OUTER, horizontal_edge
from print_pdf import handles_for


def main(src, dst):
    doc = ezdxf.readfile(src)
    db = doc.entitydb
    cx0, cx1, _ = horizontal_edge(db[CHONE_OUTER], "bottom")
    ux0, ux1, uy = horizontal_edge(db[CUFF_OUTER], "top")
    scale = (cx1 - cx0) / (ux1 - ux0)
    cuff = handles_for(doc, ["310", "311"])
    m = Matrix44.chain(
        Matrix44.translate(-ux0, -uy, 0),
        Matrix44.scale(scale, scale, 1),
        Matrix44.translate(ux0, uy, 0),
    )
    for h in cuff:
        db[h].transform(m)
    doc.saveas(dst)
    nx0, nx1, _ = horizontal_edge(db[CUFF_OUTER], "top")
    print(f"Chone bottom outer {cx1 - cx0:.4f} | cuff top outer {ux1 - ux0:.4f} -> {nx1 - nx0:.4f} "
          f"(scale {scale:.5f}, {len(cuff)} entities); saved {dst}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
