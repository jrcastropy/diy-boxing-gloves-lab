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
| `compare_mould1_outlines.py` | Overlays Mould 1 from several DXFs (whole mould and a thumb close-up) and labels each thumb's neck-to-tip length, measured on the first one's centre line. Refuses to overwrite. |
| `measure_thumb_reach.py` | Straight-line distance from Mould 1's thumb tip (where the centre line meets the outline) to the wrist corner on the thumb side, for several DXFs, drawn in one image. Refuses to overwrite. |
| `chone_mould_relation.py` | Fits Mould 1 inside the Chone stitch line where the gap is most even, and reports the gap region by region. Also compares Mould 2 to Mould 1, and the Cuff Mould to the Chone Cuff. |

## Scaled patterns

| Script | What it does |
| --- | --- |
| `scale_palm.py` | Saves a copy of the DXF with the Front Palm scaled. Nothing else changes. |
| `scale_cuff.py` | Scales the Chone Cuff so its top outer edge is exactly as long as the Chone's bottom outer edge. |
| `scale_chone.py` | Scales the Chone and the Chone Cuff by the same amount, so they still match. |
| `grow_mould_thumb.py` | Lines up Mould 1's thumb in the Chone's thumb (flat, from the DXF) and moves the thumb edge out by a fraction of the gap to the Chone stitch line (0.5 = half). The rest of Mould 1 stays the same. Refuses to overwrite an existing file. |
| `turn_mould_thumb.py` | Turns Mould 1's thumb about the middle of its base so its centre line points at the same angle as the Chone's thumb (flat, from the DXF, with the wrist edge on the Chone's wrist stitch line). The notch, wrist corner and the rest of Mould 1 stay put, and the Chone doesn't change. Refuses to overwrite an existing file. |
| `mould1_from_chone_scaled.py` | Replaces Mould 1 with the Chone cut line scaled evenly to Mould 1's area (mirrored, wrist edge on Mould 1's wrist edge), so every angle matches the Chone. Refuses to overwrite an existing file. |
| `narrow_mould_thumb.py` | Makes Mould 1's thumb narrower by a set amount in inches, both edges moving in evenly toward the thumb's centre line. The thumb keeps its length; the notch, wrist corner and the rest of Mould 1 stay put. Refuses to overwrite an existing file. |
| `lengthen_mould_thumb.py` | Makes Mould 1's thumb longer by a set amount, stretched evenly along the line from the middle of the thumb's neck to its tip. The neck, the wrist corner and the rest of Mould 1 stay put. `preview` and `preview-in-chone` modes draw options without writing a DXF; `write` makes the DXF; `write-smooth` does it for an outline that is already smooth curves (the smoothed Mould 1) by moving only the thumb's own curves, so the corners and the rest of the outline stay exact. `--name` labels previews of a different Mould 1. Refuses to overwrite an existing file. |
| `slim_mould_thumb.py` | Makes Mould 1's thumb narrower by a set amount on each side, keeping its round tip and its length. Full narrowing from the neck out (the bottom edge fades out toward the wrist). `preview-in-chone` draws options; `write` makes the DXF. Refuses to overwrite. |
| `swap_config_outline.py` | Copies a viewer config and swaps one item's outline (one that came in through the DXF import) for the same piece from another DXF. It finds the import's mirror and shift by matching the old DXF, so the new outline lands in the same place. Bends, poses and the other items are kept. Refuses to overwrite an existing file. |
| `dxf_link.py` | Shared helper: finds which DXF piece a viewer item is and gives its link (file, handle, mirror, turn, shift) and its outline as Bézier curves, for the viewer's Edit pattern tab. |
| `link_configs.py` | Adds those DXF links to viewer configs (the viewer won't load a config without them). Backs each config up first. |
| `serve_viewer.py` | Serves the repo for the viewer (`python3 scripts/serve_viewer.py`, then open http://localhost:8000/viewer/chone-fit-lab.html). The Edit pattern tab reads DXFs and saves edited ones into `dxf/` through it. |
| `scale_palm_thumb.py` | Scales the Front Palm and the Thumb by the same amount, so the Thumb seam stays matched. Refuses to overwrite an existing file. |

## Printing

| Script | What it does |
| --- | --- |
| `print_pdf.py` | True-size A4 PDF of chosen pieces (default: Front Palm and Thumb), with check rulers built from real units. |
| `print_tiled.py` | Tiles a piece too big for one A4 page across a grid of pages, with alignment marks in the overlaps. |
| `print_free.py` | Finds the fewest A4 pages for a large piece. Pages can be portrait or landscape and don't have to form a grid. Pages **butt** together: each page prints only the region it owns, with a solid cut border, and has no overlaps or alignment marks. |

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

python scripts/print_free.py "dxf/Laces Boxing 14OZ (1).dxf" print/moulds-A4-tiled-butt.pdf "Mould 1" "Mould 2"

python scripts/scale_palm.py "dxf/Laces Boxing 14OZ (1).dxf" "dxf/Laces Boxing 14OZ - palm 96%.dxf" 0.96
python scripts/scale_cuff.py "dxf/Laces Boxing 14OZ - palm 96%.dxf" "dxf/Laces Boxing 14OZ - palm 96% cuff matched.dxf"
python scripts/scale_chone.py "dxf/Laces Boxing 14OZ - palm 96% cuff matched.dxf" "dxf/Laces Boxing 14OZ - chone 105%.dxf" 1.05
python scripts/scale_chone.py "dxf/Laces Boxing 14OZ - palm 96% cuff matched.dxf" "dxf/Laces Boxing 14OZ - chone 102%.dxf" 1.02
python scripts/overlay_palm.py "dxf/Laces Boxing 14OZ - chone 102%.dxf" renders/palm-over-chone-with-cuff-102.png
python scripts/scale_chone.py "dxf/Laces Boxing 14OZ - palm 96% cuff matched.dxf" "dxf/Laces Boxing 14OZ - chone 103%.dxf" 1.03
python scripts/overlay_palm.py "dxf/Laces Boxing 14OZ - chone 103%.dxf" renders/palm-over-chone-with-cuff-103.png

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
python scripts/print_free.py "dxf/Laces Boxing 14OZ - chone 105%.dxf" print/chone-105-A4-tiled-butt.pdf "Chone"

python scripts/grow_mould_thumb.py "dxf/Laces Boxing 14OZ - palm 96% cuff matched.dxf" "dxf/Laces Boxing 14OZ - mould1 thumb half gap v2.dxf" renders/mould1-thumb-half-gap-v2.png 0.5
python scripts/turn_mould_thumb.py "dxf/Laces Boxing 14OZ - palm 96% cuff matched.dxf" "dxf/Laces Boxing 14OZ - mould1 thumb chone angle.dxf" renders/mould1-thumb-chone-angle.png
python scripts/mould1_from_chone_scaled.py "dxf/Laces Boxing 14OZ - palm 96% cuff matched.dxf" "dxf/Laces Boxing 14OZ - mould1 minified chone.dxf" renders/mould1-minified-chone.png
python scripts/print_free.py "dxf/Laces Boxing 14OZ - mould1 minified chone.dxf" print/mould1-minified-chone-A4-tiled-butt.pdf "Mould 1"
python scripts/print_free.py "dxf/Laces Boxing 14OZ - mould1 minified chone - edited - smoothed all.dxf" print/mould1-smoothed-A4-tiled-butt.pdf "Mould 1"
python scripts/lengthen_mould_thumb.py preview "dxf/Laces Boxing 14OZ - mould1 minified chone - edited - smoothed all.dxf" renders/mould1-smoothed-thumb-longer-preview.png 0.25 0.5 0.75 --name smoothed
python scripts/lengthen_mould_thumb.py preview-in-chone "dxf/Laces Boxing 14OZ - mould1 minified chone - edited - smoothed all.dxf" renders 0.25 0.5 0.75 --name smoothed
python scripts/lengthen_mould_thumb.py write-smooth "dxf/Laces Boxing 14OZ - mould1 minified chone - edited - smoothed all.dxf" "dxf/Laces Boxing 14OZ - mould1 minified chone - edited - smoothed all thumb +0.25in.dxf" renders/mould1-smoothed-thumb-longer-0.25in.png 0.25 --name smoothed
python scripts/lengthen_mould_thumb.py write-smooth "dxf/Laces Boxing 14OZ - mould1 minified chone - edited - smoothed all.dxf" "dxf/Laces Boxing 14OZ - mould1 minified chone - edited - smoothed all thumb +0.5in.dxf" renders/mould1-smoothed-thumb-longer-0.5in.png 0.5 --name smoothed
python scripts/lengthen_mould_thumb.py write-smooth "dxf/Laces Boxing 14OZ - mould1 minified chone - edited - smoothed all.dxf" "dxf/Laces Boxing 14OZ - mould1 minified chone - edited - smoothed all thumb +0.75in.dxf" renders/mould1-smoothed-thumb-longer-0.75in.png 0.75 --name smoothed
python scripts/print_free.py "dxf/Laces Boxing 14OZ - mould1 minified chone - edited - smoothed all thumb +0.25in.dxf" print/mould1-smoothed-thumb+0.25in-A4-tiled-butt.pdf "Mould 1"
python scripts/print_free.py "dxf/Laces Boxing 14OZ - mould1 minified chone - edited - smoothed all thumb +0.5in.dxf" print/mould1-smoothed-thumb+0.5in-A4-tiled-butt.pdf "Mould 1"
python scripts/print_free.py "dxf/Laces Boxing 14OZ - mould1 minified chone - edited - smoothed all thumb +0.75in.dxf" print/mould1-smoothed-thumb+0.75in-A4-tiled-butt.pdf "Mould 1"
python scripts/lengthen_mould_thumb.py write-smooth "dxf/Laces Boxing 14OZ - mould1 minified chone - edited - smoothed all thumb +0.75in.dxf" "dxf/Laces Boxing 14OZ - mould1 minified chone - edited - smoothed all thumb +0.75in +2cm.dxf" renders/mould1-smoothed-thumb+0.75in-longer-2cm.png 0.7874015748 --name "smoothed +0.75in"
python scripts/print_free.py "dxf/Laces Boxing 14OZ - mould1 minified chone - edited - smoothed all thumb +0.75in +2cm.dxf" print/mould1-smoothed-thumb+0.75in+2cm-A4-tiled-butt.pdf "Mould 1"
python scripts/compare_mould1_outlines.py renders/mould1-smoothed-vs-thumb+0.75in-vs-+0.75in+2cm.png "dxf/Laces Boxing 14OZ - mould1 minified chone - edited - smoothed all.dxf" "Original (smoothed)" "dxf/Laces Boxing 14OZ - mould1 minified chone - edited - smoothed all thumb +0.75in.dxf" "Thumb +0.75in" "dxf/Laces Boxing 14OZ - mould1 minified chone - edited - smoothed all thumb +0.75in +2cm.dxf" "Thumb +0.75in +2cm"
python scripts/measure_thumb_reach.py renders/mould1-thumb-tip-to-wrist-corner-straight.png "dxf/Laces Boxing 14OZ - mould1 minified chone - edited - smoothed all.dxf" "Original (smoothed)" "dxf/Laces Boxing 14OZ - mould1 minified chone - edited - smoothed all thumb +0.75in.dxf" "Thumb +0.75in" "dxf/Laces Boxing 14OZ - mould1 minified chone - edited - smoothed all thumb +0.75in +2cm.dxf" "Thumb +0.75in +2cm"
python scripts/narrow_mould_thumb.py "dxf/Laces Boxing 14OZ - mould1 minified chone.dxf" "dxf/Laces Boxing 14OZ - mould1 minified chone thumb -0.25in.dxf" renders/mould1-minified-chone-thumb-narrow-0.25in.png 0.25
python scripts/lengthen_mould_thumb.py preview-in-chone "dxf/Laces Boxing 14OZ - mould1 minified chone.dxf" renders 0.25 0.5 0.75
python scripts/slim_mould_thumb.py write "dxf/Laces Boxing 14OZ - mould1 minified chone.dxf" "dxf/Laces Boxing 14OZ - mould1 minified chone slim 0.125in each side.dxf" renders/mould1-minified-chone-slim-0.125in-each-side.png 0.125
python scripts/slim_mould_thumb.py write "dxf/Laces Boxing 14OZ - mould1 minified chone.dxf" "dxf/Laces Boxing 14OZ - mould1 minified chone slim 0.25in each side.dxf" renders/mould1-minified-chone-slim-0.25in-each-side.png 0.25
python scripts/slim_mould_thumb.py write "dxf/Laces Boxing 14OZ - mould1 minified chone thumb +0.25in.dxf" "dxf/Laces Boxing 14OZ - mould1 minified chone thumb +0.25in slim 0.125in each side.dxf" renders/mould1-minified-chone-thumb+0.25in-slim-0.125in-each-side.png 0.125
python scripts/slim_mould_thumb.py write "dxf/Laces Boxing 14OZ - mould1 minified chone thumb +0.25in.dxf" "dxf/Laces Boxing 14OZ - mould1 minified chone thumb +0.25in slim 0.25in each side.dxf" renders/mould1-minified-chone-thumb+0.25in-slim-0.25in-each-side.png 0.25
python scripts/slim_mould_thumb.py write "dxf/Laces Boxing 14OZ - mould1 minified chone thumb +0.5in.dxf" "dxf/Laces Boxing 14OZ - mould1 minified chone thumb +0.5in slim 0.125in each side.dxf" renders/mould1-minified-chone-thumb+0.5in-slim-0.125in-each-side.png 0.125
python scripts/slim_mould_thumb.py write "dxf/Laces Boxing 14OZ - mould1 minified chone thumb +0.5in.dxf" "dxf/Laces Boxing 14OZ - mould1 minified chone thumb +0.5in slim 0.25in each side.dxf" renders/mould1-minified-chone-thumb+0.5in-slim-0.25in-each-side.png 0.25
python scripts/slim_mould_thumb.py write "dxf/Laces Boxing 14OZ - mould1 minified chone thumb +0.75in.dxf" "dxf/Laces Boxing 14OZ - mould1 minified chone thumb +0.75in slim 0.125in each side.dxf" renders/mould1-minified-chone-thumb+0.75in-slim-0.125in-each-side.png 0.125
python scripts/slim_mould_thumb.py write "dxf/Laces Boxing 14OZ - mould1 minified chone thumb +0.75in.dxf" "dxf/Laces Boxing 14OZ - mould1 minified chone thumb +0.75in slim 0.25in each side.dxf" renders/mould1-minified-chone-thumb+0.75in-slim-0.25in-each-side.png 0.25
python scripts/lengthen_mould_thumb.py write "dxf/Laces Boxing 14OZ - mould1 minified chone.dxf" "dxf/Laces Boxing 14OZ - mould1 minified chone thumb +0.25in.dxf" renders/mould1-minified-chone-thumb-longer-0.25in.png 0.25
python scripts/lengthen_mould_thumb.py write "dxf/Laces Boxing 14OZ - mould1 minified chone.dxf" "dxf/Laces Boxing 14OZ - mould1 minified chone thumb +0.5in.dxf" renders/mould1-minified-chone-thumb-longer-0.5in.png 0.5
python scripts/lengthen_mould_thumb.py write "dxf/Laces Boxing 14OZ - mould1 minified chone.dxf" "dxf/Laces Boxing 14OZ - mould1 minified chone thumb +0.75in.dxf" renders/mould1-minified-chone-thumb-longer-0.75in.png 0.75

python scripts/export_3d.py "dxf/Laces Boxing 14OZ (1).dxf" viewer/glove-data.js

python scripts/mould_from_chone.py "dxf/Laces Boxing 14OZ (1).dxf" "dxf/Mould from Chone - 1in foam.dxf" --foam 1.0 \
  --config viewer/config/mould-from-chone-flat.json --base viewer/config/chone-fit-config.json
```
