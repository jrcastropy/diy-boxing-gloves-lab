# Scripts

Python scripts that read the DXF patterns in [`../dxf/`](../dxf/) and produce renders, prints, scaled DXFs and the 3D viewer's data.

Run them **from the repo root**, so the `dxf/`, `renders/` and `print/` paths below work. The scripts import helpers from each other (for example `poly()` from `render_pieces.py`), so keep them together in this folder.

Libraries: `ezdxf` and `matplotlib` for all of them. Some also need `shapely`, `scipy` or `numpy`. The easiest way to get them is `uv run --with …`, as in the commands below.

## Analysis and renders

| Script | What it does |
| --- | --- |
| `render_pieces.py` | Draws each pattern piece on its own, with no neighbouring pieces. Also provides shared helpers (`poly`, `center`, `inside`). |
| `join_chone_cuff.py` | Moves the Chone Cuff so its top outer line sits on the Chone's bottom inner line, and draws the two as one image. Also provides `horizontal_edge` and the piece handles. |
| `overlay_palm.py` | Lays the Front Palm, optionally scaled, over the joined Chone and Chone Cuff. |
| `compare_thumb_seam.py` | Straightens the two edges of the Thumb seam and draws them side by side at true length. |
| `chone_vs_mould.py` | Lays foam Mould 1 inside the Chone at several sizes, coloured by how much room is left to wrap the foam. It writes `renders/chone-vs-mould1.png` (fixed input and output, no arguments). |
| `chone_mould_relation.py` | Fits Mould 1 inside the Chone stitch line where the gap is most even, and reports the gap region by region. Also compares Mould 2 to Mould 1, and the Cuff Mould to the Chone Cuff. |

## Scaled patterns

| Script | What it does |
| --- | --- |
| `scale_palm.py` | Saves a copy of the DXF with the Front Palm scaled. Nothing else changes. |
| `scale_cuff.py` | Scales the Chone Cuff so its top outer edge is exactly as long as the Chone's bottom outer edge. |
| `scale_chone.py` | Scales the Chone and the Chone Cuff by the same amount, so they still match. |
| `scale_palm_thumb.py` | Scales the Front Palm and the Thumb by the same amount, so the Thumb seam stays matched. Refuses to overwrite an existing file. |

## Printing

| Script | What it does |
| --- | --- |
| `print_pdf.py` | True-size A4 PDF of chosen pieces (default: Front Palm and Thumb), with check rulers built from real units. |
| `print_tiled.py` | Tiles a piece too big for one A4 page across a grid of pages, with alignment marks in the overlaps. |
| `print_free.py` | Like `print_tiled.py`, but finds the fewest A4 pages. Pages can be portrait or landscape and don't have to form a grid. |

## 3D viewer data

| Script | What it does |
| --- | --- |
| `export_3d.py` | Exports the Chone and both foam moulds as flat triangle meshes in one shared frame, to `viewer/glove-data.js`. See [`../docs/chone-fit-lab.md`](../docs/chone-fit-lab.md). |
| `mould_from_chone.py` | Designs one foam mould from the Chone's stitch line (pulled in by the foam thickness plus ease, wrist edge flush). Writes a DXF and, optionally, a viewer config. See "A mould designed from the Chone" in [`../PATTERN-NOTES.md`](../PATTERN-NOTES.md). |

## Commands

These are the commands used to make the files in this repo. Add `uv run --with ezdxf --with matplotlib --with shapely --with scipy` in front of any of them if you don't have the libraries installed.

```sh
python scripts/render_pieces.py "dxf/Laces Boxing 14OZ - palm 96%.dxf" renders
python scripts/join_chone_cuff.py "dxf/Laces Boxing 14OZ (1).dxf" renders/chone-with-cuff.png
python scripts/overlay_palm.py "dxf/Laces Boxing 14OZ (1).dxf" renders/palm-over-chone-with-cuff.png 0.96
python scripts/compare_thumb_seam.py "dxf/Laces Boxing 14OZ (1).dxf" renders/thumb-seam-compare.png 0.96
python scripts/chone_vs_mould.py
python scripts/chone_mould_relation.py "dxf/Laces Boxing 14OZ (1).dxf" renders/chone-mould-relation.png

python scripts/scale_palm.py "dxf/Laces Boxing 14OZ (1).dxf" "dxf/Laces Boxing 14OZ - palm 96%.dxf" 0.96
python scripts/scale_cuff.py "dxf/Laces Boxing 14OZ - palm 96%.dxf" "dxf/Laces Boxing 14OZ - palm 96% cuff matched.dxf"
python scripts/scale_chone.py "dxf/Laces Boxing 14OZ - palm 96% cuff matched.dxf" "dxf/Laces Boxing 14OZ - chone 105%.dxf" 1.05

python scripts/print_pdf.py "dxf/Laces Boxing 14OZ - palm 96%.dxf" print/thumb-and-palm-A4.pdf

python scripts/scale_palm_thumb.py "dxf/Laces Boxing 14OZ - palm 96% cuff matched.dxf" "dxf/Laces Boxing 14OZ - palm+thumb 95%.dxf" 0.95
python scripts/print_pdf.py "dxf/Laces Boxing 14OZ - palm+thumb 95%.dxf" print/thumb-and-palm-95-A4.pdf
python scripts/overlay_palm.py "dxf/Laces Boxing 14OZ - palm+thumb 95%.dxf" renders/palm-over-chone-with-cuff-95.png
python scripts/scale_palm_thumb.py "dxf/Laces Boxing 14OZ - palm 96% cuff matched.dxf" "dxf/Laces Boxing 14OZ - palm+thumb 96%.dxf" 0.96
python scripts/print_pdf.py "dxf/Laces Boxing 14OZ - palm+thumb 96%.dxf" print/thumb-and-palm-96-A4.pdf
python scripts/overlay_palm.py "dxf/Laces Boxing 14OZ - palm+thumb 96%.dxf" renders/palm-over-chone-with-cuff-96.png
python scripts/scale_palm_thumb.py "dxf/Laces Boxing 14OZ - palm 96% cuff matched.dxf" "dxf/Laces Boxing 14OZ - palm+thumb 97%.dxf" 0.97
python scripts/print_pdf.py "dxf/Laces Boxing 14OZ - palm+thumb 97%.dxf" print/thumb-and-palm-97-A4.pdf
python scripts/overlay_palm.py "dxf/Laces Boxing 14OZ - palm+thumb 97%.dxf" renders/palm-over-chone-with-cuff-97.png
python scripts/print_pdf.py "dxf/Laces Boxing 14OZ - chone 105%.dxf" print/chone-cuff-105-A4.pdf "Chone Cuff"
python scripts/print_free.py "dxf/Laces Boxing 14OZ - chone 105%.dxf" print/chone-105-A4-tiled.pdf "Chone"

python scripts/export_3d.py "dxf/Laces Boxing 14OZ (1).dxf" viewer/glove-data.js

python scripts/mould_from_chone.py "dxf/Laces Boxing 14OZ (1).dxf" "dxf/Mould from Chone - 1in foam.dxf" --foam 1.0 \
  --config viewer/config/mould-from-chone-flat.json --base viewer/config/chone-fit-config.json
```
