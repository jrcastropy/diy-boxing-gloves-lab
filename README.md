# DIY Boxing Gloves Lab

Tools for making a 14 oz lace-up boxing glove by hand.

The project has three parts:

- **Patterns.** DXF pattern files for the glove, plus scaled test versions.
- **Scripts.** Python scripts that measure, scale, render and print the pattern pieces.
- **Chone Fit Lab.** A 3D viewer in the browser. It bends the Chone (the leather back) over the foam moulds, so you can check that the leather still reaches the palm seam once the glove is curled into a fist.

## Folder layout

| Folder | What's in it |
| --- | --- |
| [`dxf/`](dxf/) | Pattern files (DXF, in inches): the original, the scaled test versions and `latest.dxf` |
| [`scripts/`](scripts/) | Python scripts that read the DXFs and make renders, prints, scaled DXFs and the 3D data |
| [`viewer/`](viewer/) | The Chone Fit Lab: one HTML page and its mesh data |
| [`renders/`](renders/) | PNG images made by the scripts |
| [`print/`](print/) | True-size A4 PDFs for printing pattern pieces |
| [`docs/`](docs/) | Longer write-ups |

[`PATTERN-NOTES.md`](PATTERN-NOTES.md) explains what's wrong with the original pattern, and what has been changed and why.

## The current pattern: `dxf/latest.dxf`

**[`dxf/latest.dxf`](dxf/latest.dxf) is always the current working pattern.** It's an exact copy of one of the named DXFs in `dxf/`. Use it whenever you want "the latest" without looking up a filename. The [`latest.dxf` section of `dxf/README.md`](dxf/README.md#latestdxf) says which file it's a copy of, and what's new, edited or deleted in it.

When a new DXF becomes the latest, it's copied over `latest.dxf` and that section is rewritten. The filename never changes, so links to `latest.dxf` always stay correct.

## Quick start

The scripts need Python 3.10+ and [uv](https://docs.astral.sh/uv/). Run them from the repo root. `uv run --with …` installs the libraries for that one run.

Render each pattern piece on its own (swap in `dxf/latest.dxf` for the current pattern):

```sh
uv run --with ezdxf --with matplotlib python scripts/render_pieces.py "dxf/Laces Boxing 14OZ (1).dxf" renders/
```

Rebuild the 3D viewer's data from the pattern:

```sh
uv run --with ezdxf --with shapely --with matplotlib --with scipy \
  python scripts/export_3d.py "dxf/Laces Boxing 14OZ (1).dxf" viewer/glove-data.js
```

Open the 3D viewer. Serve the folder instead of opening the file directly, because the page loads `glove-data.js` and three.js modules:

```sh
cd viewer && python3 -m http.server 8000
# then open http://localhost:8000/chone-fit-lab.html
```

[`scripts/README.md`](scripts/README.md) has the command for every script.

## Documentation

- [`docs/chone-fit-lab.md`](docs/chone-fit-lab.md): how the Chone Fit Lab works
- [`viewer/TODO.md`](viewer/TODO.md): planned and in-progress viewer features
- [`PATTERN-NOTES.md`](PATTERN-NOTES.md): pattern analysis, the palm rescale and the Chone tests
- [`dxf/README.md`](dxf/README.md): every DXF, and what's in `latest.dxf`

## Contributing

Anyone can contribute. These are the rules:

1. **Put each new feature on its own branch.** Don't commit to `main`. Name the branch after the change, for example `feature/gather-stitch`.
2. **Open a pull request into `main`.** Anyone can open one, including from a fork.
3. **Only the maintainer ([jrcastropy](https://github.com/jrcastropy)) can merge into `main`**, and only after the pull request is approved.
4. **No direct pushes to `main`.** The branch is protected.

When you change a script or the viewer, update the matching doc in the same pull request. If a pull request makes a new DXF the latest, it should also update `dxf/latest.dxf` and the `latest.dxf` section of `dxf/README.md`.
