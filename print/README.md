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

On tiled prints, line up the circle-and-cross marks in the overlaps, then tape the pages together.
