# Chone Fit Lab — TODO

Requested 2026-11-14. Work through these one at a time. Tick each box when it's done and checked in the browser.

## Chone

- [x] **C1. New defaults**
  - Size defaults to 100%.
  - Edge wrap defaults to 0°.
  - Edge rounding defaults to 0".
  - Old saved settings (browser `localStorage`) should not bring back the old values. Bump the storage key.

- [ ] **C2. Edge wrap comes from my lines, not a global slider**
  - The Chone stays flat unless a line I draw wraps or bends it.
  - Remove the global Edge wrap / Edge rounding sliders, or move them onto the line itself, so wrap is set per line.

- [ ] **C3. The Chone never tears: gather it instead of cutting it**
  - Right now a bend line splits the Chone into pieces that pull apart (jagged, torn edges in the 3D view).
  - Leather can't be cut to make it curve. In real life the outer edge is **gather-stitched**, which bunches the leather up so it curves around the foam (like the black back of the glove in the reference photo).
  - The Chone must stay one connected sheet in every pose.

- [ ] **C4. Place gather stitches by clicking on the Chone's outer edge (flat pattern panel)**
  - Click a first point and a last point on the Chone's **outermost edge** (the cut line). Each shows as a dot.
  - Dot 1 is the start of the gather and dot 2 is the end. The stretch of edge between them is the gathered section.
  - Dots snap to the outer edge only. They can't be placed inside the Chone or on the stitch line.
  - Allow several gather sections. Be able to select, move (drag a dot along the edge) and delete one.
  - Show the gathered section in both the flat panel and the 3D view.

- [ ] **C5. Adjustable gather ratio**
  - Each gather section has a ratio I can type in (e.g. 1.5).
  - Final length = edge length between the dots ÷ ratio. Example: 30 cm at 1.5 → 20 cm.
  - Show the original and final length (in inches and cm) next to the ratio.
  - The 3D Chone shortens that stretch of edge to the final length and shows the ruffles/folds. The seam-reach check uses the gathered shape.

## All pieces (Chone, Mould 1, Mould 2)

- [ ] **A1. Move each piece in the flat pattern panel** — built, waiting for your browser test
  - Right now all three outlines are fixed where the auto-fit put them.
  - Be able to pick a piece and drag it (and rotate it) to reposition it.
  - The 3D model, edge wrap and seam reach follow the new position.
  - Add a reset button that puts the pieces back to the auto-fit position.
  - Save positions with the other settings.

- [ ] **A2. Lines belong to one piece** — built, waiting for your browser test
  - Right now drawing a line bends the Chone, Mould 1 and Mould 2 together.
  - When drawing a line, choose which piece it belongs to (Chone, Mould 1 or Mould 2). Colour the line to match its piece.

- [ ] **A3. Bend just one piece** — built, waiting for your browser test
  - In connection with A2, a line bends only the piece(s) it is assigned to.
  - Option to link a line to several pieces, so the old "bend everything together" behaviour is still possible.

- [ ] **A4. Palm faces the viewer** — built, waiting for your browser test
  - The default 3D view shows the glove upright, with the palm toward you and the fingers up.

- [ ] **A5. Adjustable mould size** — built, waiting for your browser test
  - The moulds may be scaled wrong. Give each mould its own size slider (%), scaling about the mould's centre.
  - Show each mould's width × length (inches and cm). Save the sizes with the other settings.

- [ ] **A6. Adjustable mould thickness** — built, waiting for your browser test
  - Each mould gets its own foam thickness (default 1"). The stack, the Chone height and each layer's bend radius follow it.
  - The seam-reach target follows the total foam stack, unless I've set it to something else.

- [ ] **A7. Move tool moves only the picked piece** — built, waiting for your browser test
  - Clicking near another piece's outline no longer switches the moving piece. Only the piece picked in the "Moving" chips moves.

- [ ] **A8. Save / load config as JSON** — built, waiting for your browser test
  - "Save config…" saves everything to a JSON file (into `viewer/` through the save dialog). "Load config…" restores it on another machine or session.

- [ ] **A9. Show hides a piece everywhere** — built, waiting for your browser test
  - A hidden piece disappears from the flat panel too, along with its bend lines (3D, flat panel, bend list).

- [ ] **A10. Bend list grouped by piece** — built, waiting for your browser test
  - Groups for Chone, Mould 1, Mould 2 and Shared, sorted by name. New line names no longer repeat.

- [ ] **A11. Undo** — built, waiting for your browser test
  - An Undo button plus ⌘Z / Ctrl+Z undo the most recent change: moving, adding a line, sliders and so on.

- [ ] **A12. Rotate a bend line** — built, waiting for your browser test
  - Each line has a Rotate slider (±359°). The part past the line rolls about its own length, then the Bend angle curls it.

- [ ] **A13. Type exact values** — built, waiting for your browser test
  - A number box beside every slider. Typed values aren't rounded to the slider's step.

- [ ] **A14. Bend radius down to 0** — built, waiting for your browser test
  - Radius 0 is a sharp crease on the crease face; the outer layers still go round it.

- [ ] **A15. Stop pieces overlapping** — built, waiting for your browser test
  - A checkbox under Bend lines. With it on, Bend angle, Rotate and Bend radius stop just before shown pieces would overlap.
  - Hidden pieces still block, with an alert: "You've bumped into hidden Mould 2." Where pieces already overlap, a change may not make it deeper.

## After each item

- [ ] Update `docs/chone-fit-lab.md` to match.
- [ ] Republish the artifact (https://claude.ai/artifact/Sob4uzRvaSiBrHewQNi3YW) with `glove-data.js` as a supporting file.
