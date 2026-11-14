# How the Chone Fit Lab works

2026-11-14

The Chone Fit Lab (`viewer/chone-fit-lab.html`) is a 3D model of the 14 oz glove's back. It shows the Chone (the leather back) over the two foam moulds, and lets you bend all three together. It answers one question that the flat pattern can't: **once the glove is curled into a fist, does the Chone still reach far enough down the foam edge to meet the palm seam?**

Published copy: https://claude.ai/artifact/Sob4uzRvaSiBrHewQNi3YW

## Why it's 3D

Comparing the Chone and the moulds flat (see `PATTERN-NOTES.md` and `renders/chone-mould-relation.png`) gives a gap of about 0.9" on average and 1.44" at the fingertips. But the glove isn't flat. The fingers curl and the thumb folds in, and when a stack of layers bends, the outer layer goes around a bigger curve than the inner one.

The Chone is the outermost layer, so it uses up more of its length going around each bend than the foam does. That leaves less leather to wrap down the foam edge. The flat comparison can't show this. The 3D model can.

## Pipeline

```
dxf/Laces Boxing 14OZ (1).dxf
        │  scripts/export_3d.py  (Python: ezdxf, shapely, scipy)
        ▼
viewer/glove-data.js      flat triangle meshes, in inches
        │  loaded by
        ▼
viewer/chone-fit-lab.html (three.js 0.160.0, runs in the browser)
```

To rebuild the data after changing the DXF:

```sh
uv run --with ezdxf --with shapely --with matplotlib --with scipy \
  python scripts/export_3d.py "dxf/Laces Boxing 14OZ (1).dxf" viewer/glove-data.js
```

To view it locally, serve the folder rather than opening the file directly, because the page loads `glove-data.js` and three.js modules:

```sh
cd viewer && python3 -m http.server 8000
# open http://localhost:8000/chone-fit-lab.html
```

To republish, publish `viewer/chone-fit-lab.html` with `glove-data.js` as a supporting file, to the same artifact URL.

## Step 1: exporting the pieces (`export_3d.py`)

### Which outlines

| Piece | DXF handle | Notes |
| --- | --- | --- |
| Chone, cut line | `95` | The outline used for the 3D leather surface |
| Chone, stitch line | `96` | Exported as a separate line, used for the seam-reach check |
| Mould 1 | `320` | Drawn mirrored on the sheet, so it is flipped |
| Mould 2 | `2FE` | Drawn upside down; tried both flipped and unflipped |

### Putting them in one shared frame

The moulds sit in different places on the sheet, so they have to be positioned relative to the Chone before they can be bent together:

1. **Mould 1 goes inside the Chone stitch line.** The script samples 300 points around the stitch line. Then it searches for the rotation and offset of Mould 1 that makes the gap from those points to the mould as **even** as possible (lowest standard deviation). It uses scipy's Nelder-Mead minimiser, started from several angles between −20° and +20°. The best fit turns Mould 1 by about 7.5°. This is the same fit used in `chone_mould_relation.py`.
2. **Mould 2 goes inside Mould 1** the same way. Because Mould 2 is drawn upside down, the search starts from every 20° all the way round, for both the flipped and the unflipped shape, and keeps the best.
3. **Everything moves into the Chone's frame.** The origin is the middle of the Chone stitch line's bottom (wrist) edge. x runs across the glove, y runs from the wrist to the fingertips, and units are inches.

### Turning outlines into meshes

Bending needs points inside the shape, not just around its edge, so each outline becomes a triangle mesh:

- **Edge points** every 0.12" along the outline, counter-clockwise. These come first in the vertex list. Their count is stored as `nBoundary`, so the viewer knows which vertices form the edge.
- **Inside points** on a 0.2" grid, keeping only those at least 0.09" in from the edge.
- **Triangles** from a Delaunay triangulation of all those points (`shapely.delaunay_triangles`). Any triangle that isn't fully inside the outline is dropped. This matters in the thumb notch, where Delaunay would otherwise bridge the gap.
- Each triangle's corners are put in counter-clockwise order, so the faces all point the same way.

Result: about 3,500 points for the Chone, 2,300 for Mould 1 and 2,000 for Mould 2.

### Landmark

The script also finds the **thumb notch tip** on the Chone cut line: the rightmost point of the outline in the box x −4.6 to −3.2, y 4.6 to 5.8. It comes out at (−3.92, 5.23). The viewer starts its Thumb bend line from this point, so the line ends exactly at the notch instead of cutting into the finger side above it.

### Output format

`glove-data.js` sets one global, `window.GLOVE_DATA`:

```js
{
  units: "inch",
  chone:  { verts: [[x, y], …], tris: [[i, j, k], …], nBoundary, stitch: [[x, y], …] },
  mould1: { verts, tris, nBoundary },
  mould2: { verts, tris, nBoundary },
  landmarks: { thumbNotch: [x, y] }
}
```

It's a script that sets a global, not a JSON file, so the page can load it with a plain `<script src>` without fetching.

## Step 2: building the 3D model

### Items and the layer stack

Every piece is an **item**: a flat outline meshed into triangles, of one **kind**:

- **Mould:** a foam slab. Default thickness 1" (slider 0.25–3").
- **Leather:** a thin slab. Default thickness 1 mm (slider 0.5–6 mm). It can wrap over the edge of the item under it (Edge wrap) and, if it has a stitch line, has a seam reach.

Items stack in list order from the palm face up (z = 0 is the palm face, z goes up toward the back of the hand). Each sits on the one below it; a leather item sits 0.02" above the item under it, so the faces don't fight. `applyStack()` sets every item's z0, z1 and neutral height (its mid-thickness, which it bends around), and the top of the stack (`HTOP`). By default the stack is:

| Layer | Height (z, inches) | Bends around |
| --- | --- | --- |
| Mould 2 | 0 to t₂ | t₂ / 2 |
| Mould 1 | t₂ to t₂ + t₁ | t₂ + t₁ / 2 |
| Chone | t₂ + t₁ + 0.02, 1 mm thick | its mid-thickness |

Every item is built from its flat mesh three times over: a top face, a bottom face (triangles reversed so it faces down), and a side wall made of one strip of quads around the edge points. Every render vertex keeps a link (`src`) back to its flat point, and only records whether it's on the top or the bottom face, so changing a thickness never rebuilds the mesh.

The code is modular: everything loops over the item list (`PIECES`), and the kinds are described once in `KINDS`. The Chone, Mould 1 and Mould 2 are built-in items (their meshes come from `glove-data.js`); added items carry their own outline.

### The panel

Three tabs: **Items**, **Pattern & bends** (the flat pattern with the bend lines right under it, so you can see both at once) and **Config**. The last tab you used is remembered in this browser.

**Items** lists the items, top of the stack first, each with its colour, kind, thickness and a Shown/Hidden toggle. Clicking one chooses it (it's drawn heavier in the flat pattern, and the seam-reach box shows it if it has a stitch line) and shows its settings:

- **Name**, and whether it's **Shown**.
- **See-through** (15–100%). Leather starts at 55%, moulds at 100%.
- **Size** (50–150%), with its width and length in inches and cm. The Chone scales about its wrist edge, everything else about its own centre.
- **Thickness**, in inches for a mould and mm for leather.
- Where it sits in the stack, with **↑ Up the stack** / **↓ Down** to reorder it.
- Leather only: **Edge wrap**, **Edge rounding** and the **Seam reach** target. A leather item without a stitch line says so.
- **Delete item** (red). Lines that bent only that item are deleted; it's taken off shared lines. The last item can't be deleted. Undo brings it back.

**Add item from DXF…** opens a dialog:

1. **Choose DXF file…** reads the file in the browser. Closed SPLINE (any degree, rational or not, evaluated with de Boor's algorithm), LWPOLYLINE and POLYLINE (with bulge arcs) and CIRCLE outlines are traced into polylines and converted to inches from the file's `$INSUNITS`. Outlines smaller than 0.5 sq in (lettering, notches) are drawn faintly and can't be picked. The pattern file `Laces Boxing 14OZ (1).dxf` gives 19 pickable outlines.
2. Click an outline to pick it. Pick its **Kind**. For leather you can also switch to **Stitch line** and click a second outline inside the first, which gives the item a seam reach.
3. Optionally **Mirror it** (flip left–right), give it a **Name**, and **Add item**.

The new item goes on top of the stack, centred on the Chone (or on the chosen item if there's no Chone), with the next colour from a fixed palette. Move it into place in Flat pattern. The outline is resampled every 0.12" (the stitch line every 0.1") and meshed like the Python exporter does: the outline points plus a 0.2" grid inside it, Delaunay-triangulated (the `delaunator` library, 5.0.1), keeping only triangles inside the outline. For the Chone's cut line this gives 412 outline points and 3,530 points in all, about the same as `glove-data.js`. The outline and stitch line are saved in the config, so the item comes back on load.

### Wrapping leather over the edge of the item under it ("Edge wrap")

Before any bending, leather that sticks out past the item under it (Mould 1, for the Chone) is folded down over that item's edge. For each leather point, the page precomputes:

- `e`: the distance to that item's outline. It's positive outside the foam and negative inside.
- `q`: the nearest point on that outline, and `n`, the direction pointing outward from it.

Points inside (`e ≤ 0`) stay flat in their stack slot. Points outside wrap around a rounded corner of radius ρ ("Edge rounding"), then carry on in a straight line at the wrap angle ψ ("Edge wrap"). This is the leather's bottom face, starting 0.02" off the edge (the same gap as above the top), with z₀ the bottom of its slot; the top face is the leather's thickness out from it, along the wrapped surface's normal:

```
while e ≤ ρψ (on the rounded corner):
    position = q + n·ρ·sin(e/ρ),     z = z₀ − ρ + ρ·cos(e/ρ)
after that (straight part, t = e − ρψ):
    position = q + n·(ρ·sin ψ + t·cos ψ),     z = z₀ − ρ + ρ·cos ψ − t·sin ψ
```

Both sliders start at 0, so leather starts flat. They're in each leather item's settings in **Items**. At ψ = 90° the leather hangs straight down the side of the foam. The fold uses the flat distance, so the leather never stretches.

### Bend lines

A bend line is a segment `a → b` on the flat pattern, plus:

- an **angle** θ (positive curls toward the palm)
- a **radius** R (0–5"), measured at the crease face of the stack: the palm face of the foam when curling toward the palm, or the Chone when curling toward the back
- a **flip** flag that chooses which side moves
- a **rotate** angle τ (−359° to +359°), which rolls the moving part about its own length before it's bent
- **pieces**: which of Chone, Mould 1 and Mould 2 it bends. At least one.

A line bends only the pieces it's given. Pieces it isn't given ignore it completely, so you can bend just the Chone, just one mould, or several pieces together. New lines are given the pieces picked under "New lines bend" (the Chone by default). The three starting lines bend all three pieces, which is the old "fold as one" behaviour. In the panel, a line given one piece is drawn in that piece's colour (Chone red, Mould 1 yellow, Mould 2 blue). A line given several pieces is drawn in the text colour. In 3D, a line is drawn on the top-most piece it bends.

#### Which side moves

The part that never moves is a fixed point in the middle of the back of the hand, (−0.5, 4.0). Each piece carries this point with it when it is moved or turned (see "Placing the pieces"). For each line:

1. `u` is the direction along the line, and `n` is the direction across it, pointed away from the fixed point of the line's top-most piece (or toward it if flipped). Each point gets `d`, its distance across the line, and `t`, its position along it.
2. **The cut is stretched to the piece's edges.** The script finds where the infinite line crosses the piece's outline and pairs the crossings into in-and-out stretches. The cut is the stretch(es) that overlap the segment you drew, plus 0.05". So you don't have to click exactly on the edge, and a line from the thumb notch stops at the notch instead of running on into the fingers.
3. **Flood fill.** Starting from points just past the line (`0 < d < 0.5`, within the cut), the fill spreads along mesh edges, but not across any edge that crosses the cut. What it reaches is the part that moves.
4. **Fallback.** If the fill reaches the fixed point, the line doesn't cut the piece all the way through. The fill is then redone using only points on the moving side of the line.

This runs separately for each piece the line bends, because the moulds are smaller than the Chone and their edges are in different places. It's done once whenever a line is added, moved or given different pieces, or whenever one of its pieces is resized or moved, and the result is stored with the line.

#### The bend itself

Each bend is a cylinder bend: within the bend, points wrap around an axis parallel to the line, and beyond it they turn as one solid piece. For a point on the moving side, a distance `d` past the line:

```
center height  zc = −R            if θ > 0 (curl toward the palm)
               zc = HTOP + R      if θ < 0 (curl toward the back; HTOP = top of the stack, 2.06" by default)
bend radius    r  = |layer's neutral height − zc|
used length    s  = min(d, |θ|·r)        (the flat length it takes to go round the bend)
turn angle     φ  = sign(θ)·s / r

1. move the point back toward the line by s   (p −= s·n)
2. turn it by φ about the axis through (a, zc), pointing along z × n
```

**Radius 0** puts a sharp crease on the crease face, a true right angle there at 90°. The other layers can't fold sharply, because the stack has thickness. Each one still goes round the crease, with a radius equal to its distance from it. Curling toward the palm, Mould 2 goes round at about 0.5", Mould 1 at 1.5" and the Chone at about 2.04". So even at R = 0, the Chone's corner is rounded. Curling toward the back, the crease is on the top of the stack, so the Chone (now 1 mm thick) goes round at half its thickness. If the crease were exactly on a layer's middle (`r = 0`), that layer folds as a plain hinge: `s = 0` and `φ = θ`. This avoids dividing by zero.

Points still inside the bend (`d < |θ|·r`) end up on the curve. Points beyond it turn by the full θ as one solid piece.

**Why each layer uses its own radius:** the radius `r` includes the layer's own neutral height. So for the same bend line and angle, the Chone (at about 2.04) needs a longer stretch of flat material to go round the bend than Mould 1 (at 1.5) or Mould 2 (at 0.5). That difference is the 3D effect the flat comparison misses.

The turn uses Rodrigues' rotation formula, written out by hand in `bendPoint()`.

#### Rotate (before the bend)

If a line's rotate angle τ isn't 0, the moving part is first rolled about an axis that runs across the line. The axis points along `n` (the arrow in the flat panel) and passes through the middle of the cut, at height `HTOP / 2` (the middle of the stack). Every piece on the line turns about this same axis, so the layers stay stacked. The roll builds up over the first inch past the line, so the piece doesn't tear at the line:

```
roll angle  = τ · min(1, d / 1")
```

Turning about `n` doesn't change a point's distance `d` across the line, so the bend is then applied exactly as before: **rotate first, then bend**. Within that first inch the roll twists the material a little. Like the rest of the model, this is a rough guide, not cloth. `twistPoint()` holds the maths. The bend list shows a rotated line as `Bend 3 · 30° ↻45°`. **Flatten all** zeroes both the bend angle and the rotate.

#### Several bends at once

Each piece takes only the bend lines it's given, sorted by how far they are from that piece's fixed point. For each vertex, they're applied from the farthest to the nearest:

```
final position = B_nearest( … B_farthest(starting position) )
```

Each bend is worked out on the flat pattern, so the farthest one (for example, the fingertips) is applied while everything is still in place. The nearer bends (the knuckles) then carry the already-bent part along with them. Each bend moves a point as a solid motion, so the bends combine correctly. This works when lines are nested, like the knuckles then the fingertips, or when they cover separate areas, like the thumb and the knuckles.

#### Stop pieces overlapping

With **Stop pieces overlapping** ticked (under Bend lines), the Bend angle, Rotate and Bend radius controls of the selected line (and dragging a bend in the 3D view) stop just before the change would push one piece into another. The note under the checkbox says where it stopped and which pieces met.

- **What's checked:** the bent 3D meshes of all three pieces, pair by pair (Chone/Mould 1, Chone/Mould 2, Mould 1/Mould 2). Two pieces overlap when any triangle of one crosses a triangle of the other. A grid of buckets keeps that fast. Only pairs that include a piece the line bends are checked; the others haven't moved.
- **Hidden pieces still count.** They're still there, just not drawn, so you can't push a piece through one by hiding it. When a hidden piece is what stops you, a red alert pops up over the 3D view ("You've bumped into hidden Mould 2.") for 3 seconds, and the note names it as hidden.
- **A small margin.** For the check, each mould's top and bottom faces are pulled in by 0.05". The moulds are meshed separately, so their flat triangles bend slightly differently and would otherwise "touch" falsely where they're stacked. So the stop comes about 0.1" before the surfaces really meet.
- **Stepping, then narrowing down.** A change is walked through in steps of 2° (0.1" for radius), so a thin Chone can't jump straight through a mould between two slider positions. At the first overlap, it halves the gap 7 times and keeps the last clear value, rounded back toward where you started (0.1°, 0.01").
- **Overlap that's already there.** Where pieces already overlap, the depth is measured: the faces are pulled in further (0.1", 0.15", 0.2", 0.3", 0.4", but never past half a mould's thickness) until they come apart. A change may not make it deeper than that. If they never come apart (deep overlap, or a thin mould), the number of crossing triangles at the deepest level is held instead (plus 5% slack for mesh noise). Moving a bend or Rotate back toward 0 is always allowed for a pair that already overlaps, so you can always ease it apart. It's measured once at the start of each slider gesture.
- **Red marks.** With the box ticked, every triangle that crosses another piece is tinted red in the 3D view, so you can see where existing overlap is.
- **Not checked:** a piece passing into itself (folding past 180°), and changes other than angle, Rotate and radius (moving, resizing, thickness, Flip, adding lines). After those, the note just reports any overlap.

**Bends on all layers at once can overlap a little at the far line.** For example, knuckles at 70° plus fingertips on all three pieces: Chone/Mould 1 about 0.2", Mould 1/Mould 2 about 0.1". Each layer keeps its own length, so bending the knuckles makes the outer layers slide back against the inner ones, by about the angle × the gap between layers (70° × 1" ≈ 1.2"). Each layer then curls at its own fingertip line, and those lines no longer line up, so the curls cross. Real foam would squash or shift instead. With the box ticked, the stop catches this as you bend.

### Seam reach

This is the number the page is built for. It's worked out for every leather item that has a stitch line (the Chone, or an added leather item given one), against the item under it. For each point on the stitch line:

- **Finding it on the bent Chone:** it is located in a Chone triangle on the flat pattern (a 0.5" grid makes the search fast). Its bent position is then worked out from that triangle's bent corners, and it is lifted 0.03" off the surface so it draws on top.
- **Measuring:** the script takes the nearest edge point of the item under it (Mould 1, for the Chone), from the flat pattern, at both its top and its bottom on the bent model. That gives the direction down the foam side. The reach is how far the stitch point lies along that direction, starting from the top of that item:

  ```
  reach = (S − T) · normalize(B − T)
  ```

  S is the stitch point, T the top of the foam edge, B the bottom of Mould 1's edge. Past 1" the line continues in the same direction, approximately down Mould 2's side.
- **Colour:** green if it reaches the target (by default the moulds under that leather, 2" for the Chone). If the target equals the moulds under it when you change a thickness, the target follows the new total. A target you've set to something else stays as it is, amber if within 0.5" of it, red if shorter. The wrist edge is shown grey and left out, because it's sewn to the cuff.
- **Badge:** over the 3D view, for the chosen item if it has a seam reach, otherwise the first shown one that does. It shows the shortest reach, roughly where it is (fingertips, knuckle side, thumb, index-finger side, wrist), and the percentage of the seam that reaches the target.

### Chone size

The Chone's **Size** (in Items) scales its flat points and stitch line about the origin (the middle of the wrist edge). This is the same pivot `scale_chone.py` uses, so the sizes match the 105–120% DXFs. Changing it re-runs the Chone setup: the edge-wrap distances, the triangle lookup grid, the stitch-point positions and the moving part of every bend line that bends the Chone.

### Placing the pieces

The exporter's fit (Step 1) is only a starting position. In the panel, each piece can be scaled, moved and turned. Each piece has a scale s, an offset (x, y) and a rotation about the centre c of its outline. A placed point is:

```
placed = R(rot) · (point − c) · s + pivot + (x, y)
pivot  = c · s   for the Chone (so it scales about the wrist-edge origin, like scale_chone.py)
pivot  = c       for every other item (so it scales about its own centre and stays put)
```

Each item's s comes from its **Size** slider in Items (50–150% in 0.5% steps), which shows its width and length in inches and cm. "Reset all positions" leaves sizes alone.

Every item starts at 100%, offset 0 and rotation 0 (the auto-fit position for the built-in three). Scaling or moving a piece re-runs everything that depends on where it is:

- its triangle lookup grid and texture coordinates
- the moving part of every line that bends it
- the leather setup (edge wrap and seam-reach lookups) of the piece, if it's leather, and of a leather item sitting on it

Lines given only the moved piece move, turn and scale with it, so they stay in the same place on that piece. (Lines on an item move with it when you move or turn it, and scale with its Size slider.) Lines shared with other pieces stay where they are. While you drag, the move is applied at most once per animation frame.

### Interaction

- **3D picking:** each render vertex's flat (x, y) position is stored in its texture coordinates. A click therefore gives the point on the flat pattern directly, even when the model is bent.
- **Dragging a part:** a click listener that runs before the camera controls finds the part under the pointer. It then picks the bend that moves that point, preferring the bend farthest from the fixed point. Next it turns off the camera controls and changes that bend's angle by 0.6° per pixel of vertical drag. Holding Shift or Alt skips this, so the camera turns instead.
- **Highlighting:** the part that the hovered bend would move is lightened by 18% in each piece it bends, and the selected bend's part by 32%. The selected line is drawn at full colour in 3D, and the other lines are dimmed.
- **Flat pattern panel:** a 2D canvas over a 1" grid, with two tools:
  - **Draw lines:** pick which pieces new lines bend, using the "New lines bend" chips. Dragging draws a new line. Tapping picks the bend that moves that spot, checking the pieces picked for new lines first. Dragging an end dot moves the selected line. The part the selected bend moves is shaded in each piece's colour.
  - **Move pieces:** pick a piece with the "Moving" chips. Only that piece moves. Clicking near another piece's outline doesn't switch to it. Dragging moves it. Shift-drag, or the Rotation slider (±45°), turns it about its centre, which is marked +. "Reset this piece" and "Reset all positions" put pieces back at the auto-fit position.
- **Selected line's pieces:** the "Bends" chips in the line's box choose which pieces it bends. The last chip can't be switched off.
- **Saving:** the items (with added items' outlines), their settings, bend lines (with their pieces), positions, the chosen item and the "New lines bend" choice are saved in the browser (`localStorage`, key `chone-fit-lab-v2`), and only after the page has finished loading. Settings saved before items existed are converted when they're loaded. If storage isn't available, the page still works and just doesn't remember anything.
- **Shown / Hidden** (in Items): hiding a piece hides it in 3D and in the flat pattern panel (its outline, and its stitch line). It also hides its bend lines in 3D, in the flat panel and in the bend list, and they can't be picked by tapping. A line shared with a piece that's still shown stays visible and is drawn on that piece. If the selected line gets hidden, nothing is selected. The bend count says how many lines are hidden. A hidden piece is also greyed out and can't be clicked in every piece picker. In **New lines bend**, new lines go only on pieces that are picked and shown. If all the picked pieces are hidden, drawing in the flat panel does nothing, **Draw on 3D** is switched off, and a note says why. In a line's **Bends**, you can't add a hidden piece to the line or take it off. In **Moving**, a hidden piece can't be moved. If the piece being moved gets hidden, the first shown piece is picked instead.
- **Bend list:** lines are grouped under each item (top of the stack first) and Shared (lines that bend more than one piece, shown with a colour dot for each of their pieces). Each group is sorted by name in number order (Bend 2 before Bend 10). New lines are named one more than the highest "Bend N" already there, so names never repeat. (They used to come from a counter that reset on load, which made duplicates.)
- **Undo:** the **↶ Undo** button at the top of the 3D view, or ⌘Z / Ctrl+Z, steps back through changes. These are: adding, deleting, flipping or flattening lines; dragging a line's ends; bending in 3D; changing a line's pieces, angle or radius; moving, turning, resizing, thickening, renaming, reordering, adding or deleting items; the edge-wrap and target sliders; "Reset…" buttons; and loading a config. Before each change, the page pushes a full snapshot (up to 100). Continuous input from one control within a second, like dragging a slider, is one step. A click that doesn't actually change anything doesn't add a step. Undo leaves the view settings as they are now: shown/hidden, see-through, the chosen item and "New lines bend". The undo history lives only in the open page and is cleared when it reloads.
- **See-through:** each item has its own see-through slider in Items (15–100%): leather starts at 55%, moulds at 100% (solid). It's a view setting: saved with the config, but undo leaves it as it is.
- **Number boxes:** every slider in the panel has a box beside it for typing an exact value, with its unit (°, ", mm, %; see-through is in %). The box and the slider follow each other both ways. A typed value applies when you press Enter or click away, and Esc cancels. It's kept inside the slider's range, but it isn't rounded to the slider's step. A 1.37" thickness stays 1.37" instead of becoming 1.35". To allow that, the slider accepts any value until you drag or key it again. The piece Rotation slider now goes from −180° to +180° (it was ±45°), to match what Shift-drag can do.
- **Config files:** **Save config…** writes everything as JSON (version 2): the items (added ones with their outlines) and their settings, the bend lines and their pieces, the "New lines bend" choice and the chosen item. Version 1 configs (before items) still load. Configs belong in `viewer/config/`, which is git-ignored so they stay on your machine. A web page can't open a dialog at a fixed path, so in Chrome and Edge both the save and the open dialog use one remembered-folder id (`chone-fit-config`). You browse to `viewer/config/` the first time, and after that both dialogs open there by themselves, even after a reload. The folder is remembered for each origin, such as `localhost:8000`. Where those dialogs aren't available (Safari, Firefox, some embedded pages), Save downloads `chone-fit-config.json` for you to move into `viewer/config/`, and Load uses a plain file picker. **Load config…** reads a file back. The page checks it first: bad lines are skipped, and missing fields get their defaults. The browser's own saved copy and config files go through the same `applyConfig()`, so they behave the same. A page can't write into a folder without asking you first, which is why there's a dialog.
- **Redrawing:** changes mark the model as out of date, and the next animation frame recomputes everything. The amount of work is small: about 13,000 vertices times a few bend lines.

### Starting state

There are no starting lines: the pieces start flat. A new line also starts flat (angle 0°, Rotate 0°, radius 1.5"), so drawing one doesn't change the model until you bend it. **Delete all lines** (red, under the bend list) removes every line; Undo brings them back.

### Look and libraries

- three.js 0.160.0 and its OrbitControls camera, loaded from jsDelivr through an import map.
- The camera's up direction is +y (toward the fingertips), so the glove stands upright. The default view, "3/4 palm", looks at the palm side (−z), like a hand held up with the palm facing you. The camera orbits around the finger axis. The main light is on the palm side, and the floor grid sits under the wrist.
- Fonts: Barlow Condensed for headings, Inter for text and JetBrains Mono for numbers, from Google Fonts.
- Colors are defined once for light mode and once for dark mode. The 3D scene reads them at runtime and redraws when the theme changes.
- On narrow screens the panel moves below the 3D view.

## Limitations

- **It isn't a cloth simulation.** The leather bends exactly along your lines and never stretches, wrinkles or gathers. The real Chone is gathered onto the palm seam, and the model doesn't show that.
- **Foam bends around its middle.** Each slab keeps its length at mid-thickness and stretches or squashes evenly above and below. Real foam compresses unevenly.
- **Edge wrap uses the nearest edge point.** At inward corners (the thumb notch), the nearest point on the foam outline can jump, so the wrapped leather may kink there.
- **The moulds start at the even-gap fit.** If the foam actually sits differently under the Chone, move it with the Move pieces tool.
- **Bending pieces separately can make them pass through each other** unless **Stop pieces overlapping** is ticked, and even then only the bend controls are stopped (see above).
- **Layers slide at the far bends.** After a nearer bend, each layer's later bend lines sit at different places, so curls at the fingertips cross a little.
- **Not included as built-in items:** the Chone Cuff, the Cuff Mould and the Front Palm. Add them from the DXF with **Add item from DXF…**.
- **Stacking is simple.** Each item sits flat on the one below it across its whole outline, even where they don't overlap on the flat pattern.
- **Untested in a browser here.** It was published after only a syntax check, because the headless-browser screenshot was blocked in this setup.

## Files

| File | Role |
| --- | --- |
| `scripts/export_3d.py` | DXF to `viewer/glove-data.js`: fits the moulds and builds the meshes |
| `viewer/glove-data.js` | Generated mesh data (about 370 KB) |
| `viewer/chone-fit-lab.html` | The viewer: one HTML page with all the code inside it, including the DXF reader for added items |
| `scripts/chone_mould_relation.py` | The flat 2D comparison this builds on (`renders/chone-mould-relation.png`) |
| `scripts/render_pieces.py`, `scripts/join_chone_cuff.py` | Shared helpers `poly()` and `horizontal_edge()` used by the exporter |
