# CLAUDE.md

## The "latest" pointer files in `dxf/`

There are exactly two kinds of pointer, and each is a byte-for-byte copy of a named DXF:

- **`dxf/latest.dxf`**: the core pattern, the full glove sheet. Unless the user names a different file, "the latest", "the current pattern" and "latest.dxf" all mean this file.
- **The cutting-machine files**: the current ready-to-cut leather files for the Cameo 4 Plus, one mat per leather colour:
  - `dxf/latest-cutting-machine-chone-colour-12x24.dxf` (Chone body, Chone thumb, Chone Cuff, Thumb Panel; 12"×24" mat)
  - `dxf/latest-cutting-machine-palm-colour-12x24.dxf` or `dxf/latest-cutting-machine-palm-colour-14x15.dxf` (Front Palm, Thumb; whichever mat is loaded)

  "The latest cutting files" (or "latest chone colour" / "latest palm colour") means these.

Rules:

- Refer to them by these names in docs and answers. Don't call any other named file "latest" anywhere, so the pointers live in one place.
- What each pointer is a copy of, and what changed, is written only in its section of [`dxf/README.md`](dxf/README.md): the `latest.dxf` section, or the cutting-machine section.

## After creating a new DXF

1. Save it under its own descriptive name in `dxf/`, and add its row to the table in `dxf/README.md` as usual.
2. Then ask the user, word for word:
   - for a full pattern sheet: **"Do you want to make this the latest.dxf now? If yes, I will start creating a copy."**
   - for ready-to-cut mat files: **"Do you want to make these the latest cutting-machine files now? If yes, I will start creating copies."**
3. Only if they say yes:
   - Copy each new file over its pointer (a plain copy, with no edits), then check the files are identical (`cmp`).
   - Rewrite that pointer's section of `dxf/README.md`. Fill in **Copy of** (the source filename), **Since** (today's date, and which file it replaces), **What's new**, **What was edited**, **What was deleted** (write "nothing" if nothing was) and **A4 print** (if there is one) or the mat images.
4. If they say no, leave the pointers and their README sections alone.
5. When `latest.dxf` changes, the cutting-machine files are not updated automatically; they're rebuilt from it only if the user asks.

## Silhouette Studio (cutting machine)

When the user says "import it on the app" or "open it in Silhouette", follow [`docs/silhouette-studio.md`](docs/silhouette-studio.md): open the right `latest-cutting-machine-*.dxf` with `open -a "Silhouette Studio" <file>`, then ask for a ⌘A screenshot and check the size and position against that doc. Any new mat DXF must be moved for Studio (`layout` does it: top-left 10 mm in from the mat's top-left, y negative), or it opens above the mat. Mats keep 10 mm between pieces and from the edges.
