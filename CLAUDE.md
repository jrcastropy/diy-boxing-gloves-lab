# CLAUDE.md

## `dxf/latest.dxf` is the current pattern

- `dxf/latest.dxf` is always a byte-for-byte copy of the current working DXF. Unless the user names a different file, "the latest", "the current pattern" and "latest.dxf" all mean this file.
- Refer to it as `latest.dxf` in docs and answers. Don't call any other named file "latest" anywhere, so the pointer lives in one place.
- What `latest.dxf` is a copy of, and what changed in it, is written only in the `latest.dxf` section of [`dxf/README.md`](dxf/README.md).

## After creating a new DXF

1. Save it under its own descriptive name in `dxf/`, and add its row to the table in `dxf/README.md` as usual.
2. Then ask the user, word for word: **"Do you want to make this the latest.dxf now? If yes, I will start creating a copy."**
3. Only if they say yes:
   - Copy the new file over `dxf/latest.dxf` (a plain copy, with no edits), then check the two files are identical (`cmp`).
   - Rewrite the `latest.dxf` section of `dxf/README.md`. Fill in **Copy of** (the source filename), **Since** (today's date, and which file it replaces), **What's new**, **What was edited**, **What was deleted** (write "nothing" if nothing was) and **A4 print** (if there is one).
4. If they say no, leave `latest.dxf` and its README section alone.
