# Print

True-size A4 PDFs of pattern pieces, ready to print. **Print at 100% ("actual size"), not "fit to page".** Every page has check rulers made from real units (inches and cm). Measure them with a ruler before you cut.

| File | What it is | Made by |
| --- | --- | --- |
| `thumb-and-palm-A4.pdf` | Page 1: Front Palm at 96%. Page 2: Thumb. | `scripts/print_pdf.py` |
| `thumb-and-palm-95-A4.pdf` (and `-96`, `-97`) | Page 1: Front Palm. Page 2: Thumb. Both at 95% (or 96%, 97%), from the matching `palm+thumb` DXF. | `scripts/print_pdf.py` |
| `chone-cuff-A4.pdf` | The matched Chone Cuff on one page | `scripts/print_pdf.py` |
| `chone-cuff-105-A4.pdf` (and `-110`, `-115`, `-120`) | The Chone Cuff from each scaled Chone test pattern | `scripts/print_pdf.py` |
| `chone-A4-tiled.pdf` | The Chone at 100% on 3 A4 pages, to tape together | `scripts/print_free.py` |
| `chone-105-A4-tiled.pdf` (and `-110`, `-115`, `-120`) | The scaled Chone test patterns, tiled across A4 pages | `scripts/print_free.py` / `scripts/print_tiled.py` |
| `chone-A4-tiled-butt.pdf` | The Chone at 100% on 3 A4 pages with **butt joins**: cut on the solid border, butt the edges, tape | `scripts/print_free.py` |
| `chone-105-A4-tiled-butt.pdf` (and `-110`, `-115`, `-120`) | The scaled Chone test patterns with butt joins (3, 3, 4 and 4 pages) | `scripts/print_free.py` |
| `moulds-A4-tiled-butt.pdf` | Foam Mould 1 (pages 1–2) and Mould 2 (pages 3–4) from the original DXF, true size, butt joins. Mould 2 prints upside down, the way it is drawn on the sheet. | `scripts/print_free.py` |
| `mould1-minified-chone-A4-tiled-butt.pdf` | Foam Mould 1 as the minified Chone (the Chone at 79.3%, from `mould1 minified chone.dxf`), true size on 2 A4 pages, butt joins. | `scripts/print_free.py` |
| `mould1-smoothed-A4-tiled-butt.pdf` | **Latest Mould 1**, from `mould1 minified chone - edited - smoothed all.dxf`: the hand-edited thumb with the whole outline smoothed. True size on 2 A4 pages, butt joins. | `scripts/print_free.py` |
| `mould1-smoothed-thumb+0.25in-A4-tiled-butt.pdf` (and `+0.5in`, `+0.75in`) | The latest Mould 1 with its thumb 0.25" (0.5", 0.75") longer, from the matching `smoothed all thumb` DXF. True size, butt joins: 2 pages (2 pages, 3 pages for `+0.75in`). | `scripts/print_free.py` |
| `mould1-smoothed-thumb+0.75in+2cm-A4-tiled-butt.pdf` | The `+0.75in` Mould 1 with its thumb another 2 cm longer, from `smoothed all thumb +0.75in +2cm.dxf`. True size on 3 A4 pages, butt joins. | `scripts/print_free.py` |

On the `-tiled-butt` prints, each page has a solid border around the part it owns. Cut exactly on that border. Use the small map in the top-right corner to see where the page goes, butt the cut edges together and tape them. There are no overlaps and no alignment marks. Some borders are L-shaped where pages step around each other.

The older `-tiled` prints (without `-butt`) use overlaps with circle-and-cross marks. `print_free.py` now makes butt-join prints only, so those older files come from an earlier version of the script.
