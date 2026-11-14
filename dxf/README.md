# DXF patterns

Pattern files for the 14 oz lace-up boxing glove. They're plain-text DXF (AutoCAD 2018 format), with units in inches. Each sheet holds every piece of the glove: Front Palm, linings, Chone, Chone Cuff, Thumb, Thumb Panel, the two foam Moulds, the Cuff Mould and a scale bar.

The scale bar drawn on the sheet doesn't match the file's units, so use the file's inches. [`../PATTERN-NOTES.md`](../PATTERN-NOTES.md) has the details.

| File | What it is | Made by |
| --- | --- | --- |
| `Laces Boxing 14OZ (1).dxf` | The original pattern, unchanged | — |
| `Laces Boxing 14OZ - palm 96%.dxf` | The original with the Front Palm scaled to 96%, so it matches the pieces it's sewn to | `scripts/scale_palm.py` |
| `Laces Boxing 14OZ - palm 96% cuff matched.dxf` | Palm at 96%, plus the Chone Cuff scaled by 100.58%, so its top outer edge matches the Chone's bottom outer edge | `scripts/scale_cuff.py` |
| `Laces Boxing 14OZ - chone 105%.dxf` | The "cuff matched" pattern with the Chone and Chone Cuff at 105%. This is the current test pattern. | `scripts/scale_chone.py` |
| `Laces Boxing 14OZ - chone 110%.dxf` | The same at 110% | `scripts/scale_chone.py` |
| `Laces Boxing 14OZ - chone 115%.dxf` | The same at 115% | `scripts/scale_chone.py` |
| `Laces Boxing 14OZ - chone 120%.dxf` | The same at 120% | `scripts/scale_chone.py` |

The Chone is scaled because, at 100%, it's too small to cover the 2" of foam. See "The Chone is too small" in [`../PATTERN-NOTES.md`](../PATTERN-NOTES.md).
