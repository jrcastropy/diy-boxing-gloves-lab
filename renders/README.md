# Renders

PNG images of the pattern made by the scripts in [`../scripts/`](../scripts/). They're outputs, so re-run the script to update one rather than editing it.

| Image | What it shows | Made by |
| --- | --- | --- |
| `chone.png`, `chone-cuff.png`, `front-palm.png`, `thumb.png`, `thumb-panel.png`, `mould-1.png`, `mould-2.png`, `cuff-mould.png`, `scale-bar.png` | One pattern piece each, on its own | `render_pieces.py` |
| `full-layout.png` | The whole pattern sheet, from the original DXF | not made by a script in this repo |
| `chone-with-cuff.png` | The Chone Cuff joined to the bottom of the Chone | `join_chone_cuff.py` |
| `palm-over-chone-with-cuff.png` | The Front Palm laid over the joined back | `overlay_palm.py` |
| `palm-over-chone-with-cuff-105.png` (and `-110`, `-115`, `-120`) | The same, using the scaled Chone test patterns | `overlay_palm.py` |
| `thumb-seam-compare.png` | The two edges of the Thumb seam, straightened side by side | `compare_thumb_seam.py` |
| `chone-vs-mould1.png` | Mould 1 inside the Chone at 100/110/115/120%, coloured by how much room is left to wrap the foam | `chone_vs_mould.py` |
| `chone-mould-relation.png` | The gap between each mould and the leather that covers it, after the even-gap fit | `chone_mould_relation.py` |

[`../scripts/README.md`](../scripts/README.md) has the exact commands.
