# DXF patterns

Pattern files for the 14 oz lace-up boxing glove. They're plain-text DXF (AutoCAD 2018 format), with units in inches. Each sheet holds every piece of the glove: Front Palm, linings, Chone, Chone Cuff, Thumb, Thumb Panel, the two foam Moulds, the Cuff Mould and a scale bar.

The scale bar drawn on the sheet doesn't match the file's units, so use the file's inches. [`../PATTERN-NOTES.md`](../PATTERN-NOTES.md) has the details.

## `latest.dxf`

**`latest.dxf` is always the current working pattern.** It's a byte-for-byte copy of one of the named DXFs below. Point to `latest.dxf` rather than a long filename. When a new DXF is made the latest, it gets copied over `latest.dxf` and this section is updated.

- **Copy of:** `Laces Boxing 14OZ - mould1 minified chone - edited - smoothed all thumb +0.75in +2cm.dxf`
- **Since:** 2026-11-28, replacing the `smoothed all thumb +0.75in` DXF
- **What's new:** Mould 1's thumb is another 2 cm (0.787") longer than in `+0.75in`, after a test fit showed `+0.75in` was still 2 cm short. Thumb neck to tip went from 7.39 cm (base `smoothed all.dxf`) to 11.29 cm.
- **What was edited:** only the curves of Mould 1's thumb. The rest of Mould 1's outline, both bottom corners and every other piece are exactly as in `smoothed all.dxf`.
- **What was deleted:** nothing.
- **A4 print:** `../print/mould1-smoothed-thumb+0.75in+2cm-A4-tiled-butt.pdf` (3 pages, butt joins)

## All files

| File | What it is | Made by |
| --- | --- | --- |
| `Laces Boxing 14OZ (1).dxf` | The original pattern, unchanged | — |
| `Laces Boxing 14OZ - palm 96%.dxf` | The original with the Front Palm scaled to 96%, so it matches the pieces it's sewn to | `scripts/scale_palm.py` |
| `Laces Boxing 14OZ - palm 96% cuff matched.dxf` | Palm at 96%, plus the Chone Cuff scaled by 100.58%, so its top outer edge matches the Chone's bottom outer edge | `scripts/scale_cuff.py` |
| `Laces Boxing 14OZ - palm+thumb 95%.dxf` (and `96%`, `97%`) | The "cuff matched" pattern with the Front Palm and the Thumb both at 95% (or 96%, 97%) of their size in that file. Not the same as `palm 96%.dxf`. Original Chone and matched Cuff unchanged. | `scripts/scale_palm_thumb.py` |
| `Laces Boxing 14OZ - chone 105%.dxf` | The "cuff matched" pattern with the Chone and Chone Cuff at 105%. | `scripts/scale_chone.py` |
| `Laces Boxing 14OZ - chone 102%.dxf`, `... chone 103%.dxf` | The "cuff matched" pattern with the Chone and Chone Cuff at 102% / 103%. | `scripts/scale_chone.py` |
| `Laces Boxing 14OZ - chone 110%.dxf` | The same at 110% | `scripts/scale_chone.py` |
| `Laces Boxing 14OZ - chone 115%.dxf` | The same at 115% | `scripts/scale_chone.py` |
| `Laces Boxing 14OZ - chone 120%.dxf` | The same at 120% | `scripts/scale_chone.py` |
| `Mould from Chone - 1in foam.dxf` | **Not a full sheet.** One foam mould designed to fit the original (100%) Chone, for 1" foam. Layer `MOULD` is the mould; layer `CHONE_STITCH_REF` is the Chone's stitch line, for reference. Drawn the same way round as the Chone (the original moulds are mirrored), with the origin at the middle of the Chone's wrist edge. | `scripts/mould_from_chone.py` |
| `Laces Boxing 14OZ - mould1 minified chone - edited - smoothed all.dxf` | **Smoothed Mould 1 (base).** Mould 1 as the minified Chone, thumb reshaped by hand in the viewer's Edit pattern tab, then the whole outline smoothed: 172 smooth curves, a straight level bottom edge and two sharp bottom corners. Only Mould 1 differs from `mould1 minified chone.dxf`. A4 print: `print/mould1-smoothed-A4-tiled-butt.pdf`. | viewer Edit pattern, then smoothing ([`../docs/outline-smoothing.md`](../docs/outline-smoothing.md)) |
| `Laces Boxing 14OZ - mould1 minified chone - edited - smoothed all thumb +0.25in.dxf` (and `+0.5in`, `+0.75in`) | The smoothed Mould 1 with its thumb 0.25" (0.5", 0.75") longer along its centre line. Only the thumb's own curves moved; the rest of the outline, the other pieces and both bottom corners are exactly as in `smoothed all.dxf`. A4 prints: `print/mould1-smoothed-thumb+0.25in-A4-tiled-butt.pdf` (and `+0.5in`, `+0.75in`). | `scripts/lengthen_mould_thumb.py write-smooth` |
| `Laces Boxing 14OZ - mould1 minified chone - edited - smoothed all thumb +0.75in +2cm.dxf` | The `+0.75in` Mould 1 with its thumb another 2 cm (0.787") longer, after a test showed +0.75" still 2 cm short. Thumb neck to tip 7.39 → 11.29 cm against `smoothed all.dxf`. Only the thumb's curves moved. A4 print: `print/mould1-smoothed-thumb+0.75in+2cm-A4-tiled-butt.pdf`. | `scripts/lengthen_mould_thumb.py write-smooth` |
| `Laces Boxing 14OZ - leather cut - step1 outlines and holes.dxf` | **Cutting-machine file, step 1 (Cameo 4 Plus).** Only the five leather pieces from `latest.dxf` (Front Palm, Chone, Chone Cuff, Thumb, Thumb Panel), each with only its outer cut line and its real holes (27 on the palm, 1 on the Chone, 3 on the Thumb). Inner lines, dash marks and lettering are removed; moulds, linings and the scale bar are gone. Pieces are where they were on the sheet, each on its own layer named after it. Render: `renders/leather-cut-step1-outlines-and-holes.png`; one image per piece in `renders/leather-cut-step1/`. | `scripts/leather_cut.py clean` |
| `Laces Boxing 14OZ - leather cut - step2 chone thumb split.dxf` | **Cutting-machine file, step 2.** Step 1 with the Chone (12.20" × 15.37", too big for either mat) cut in two along a straight 5.51" line from the thumb notch to the corner where the bottom edge starts. Both parts get 5 mm added along the cut for the join. The body's bottom edge simply carries on 5 mm; the other strip ends are square. Layers `chone-body` (8.56" × 15.37", keeps the Chone's hole; needs the 12"×24" mat) and `chone-thumb` (5.69" × 6.09"). Other pieces as in step 1. Images: one per piece in `renders/leather-cut-step2/`, split line `renders/leather-cut-step2-chone-split-preview.png`, both ends close up `renders/leather-cut-step2-split-ends-zoom.png`. | `scripts/leather_cut.py split-chone` |

The Chone is scaled because, at 100%, it's too small to cover the 2" of foam. See "The Chone is too small" in [`../PATTERN-NOTES.md`](../PATTERN-NOTES.md).
