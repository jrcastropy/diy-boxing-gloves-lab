"""Scale the Chone (and the Chone Cuff to match) and save a new DXF.

The Chone is scaled uniformly about the centre of its bottom edge, so it stays in
place on the sheet. The Chone Cuff is scaled by the same amount about its top-left
outer corner, so its top outer edge stays exactly as long as the Chone's bottom
outer edge. Nothing else changes.

Usage: python scripts/scale_chone.py "dxf/Laces Boxing 14OZ - palm 96% cuff matched.dxf" "dxf/Laces Boxing 14OZ - chone 110%.dxf" 1.10
"""
import sys

import ezdxf
from ezdxf.math import Matrix44

from join_chone_cuff import CHONE_OUTER, CUFF_OUTER, horizontal_edge
from print_pdf import handles_for


def scale_about(x, y, s):
    return Matrix44.chain(Matrix44.translate(-x, -y, 0), Matrix44.scale(s, s, 1), Matrix44.translate(x, y, 0))


def main(src, dst, s):
    doc = ezdxf.readfile(src)
    db = doc.entitydb
    chone = handles_for(doc, ["95", "96"])
    cuff = handles_for(doc, ["310", "311"])
    cx0, cx1, cy = horizontal_edge(db[CHONE_OUTER], "bottom")
    ux0, _, uy = horizontal_edge(db[CUFF_OUTER], "top")
    for h in chone:
        db[h].transform(scale_about((cx0 + cx1) / 2, cy, s))
    for h in cuff:
        db[h].transform(scale_about(ux0, uy, s))
    doc.saveas(dst)
    nx0, nx1, _ = horizontal_edge(db[CHONE_OUTER], "bottom")
    ux0, ux1, _ = horizontal_edge(db[CUFF_OUTER], "top")
    print(f"{s:.0%}: Chone bottom outer {nx1 - nx0:.3f}, cuff top outer {ux1 - ux0:.3f} "
          f"({len(chone)} Chone + {len(cuff)} cuff entities); saved {dst}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], float(sys.argv[3]))
