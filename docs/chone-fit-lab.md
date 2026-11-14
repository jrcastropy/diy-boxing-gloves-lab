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

### The layer stack

| Layer | Height (z, inches) | Bends around (neutral height) |
| --- | --- | --- |
| Mould 2 | 0 to t₂ | t₂ / 2 |
| Mould 1 | t₂ to t₂ + t₁ | t₂ + t₁ / 2 |
| Chone | t₂ + t₁ + 0.04 (a thin sheet on top) | the same |

t₁ and t₂ are the thicknesses of Mould 1 and Mould 2. Both default to 1", which gives the original heights: 0–1, 1–2 and 2.04. Each is set with its own slider in the **Moulds** panel (0.25–2" in 0.05" steps). `applyThickness()` recomputes every layer's heights and neutral height, and the Chone's height (`HTOP`). A slab's render vertices only record whether they're on the top or the bottom face, so changing the thickness never rebuilds the mesh. "Thickness back to 1\"" resets both.

z = 0 is the palm face of the foam, and z goes up toward the back of the hand.

- **Moulds are solid slabs.** Each one is built from its flat mesh three times over: a top face, a bottom face (with its triangles reversed so it faces down), and a side wall made of one strip of quads around the edge points.
- **The Chone is a single sheet.** Every render vertex keeps a link (`src`) back to its point on the flat mesh. The bending is worked out from flat positions, so all copies of a point move together.

### Wrapping the Chone over the foam edge ("Edge wrap")

Before any bending, leather that sticks out past Mould 1 is folded down over the foam edge. For each Chone point, the page precomputes:

- `e`: the distance to Mould 1's outline. It's positive outside the foam and negative inside.
- `q`: the nearest point on that outline, and `n`, the direction pointing outward from it.

Points inside the foam (`e ≤ 0`) stay flat at z = 2.04. Points outside wrap around a rounded corner of radius ρ ("Edge rounding"), then carry on in a straight line at the wrap angle ψ ("Edge wrap"):

```
while e ≤ ρψ (on the rounded corner):
    position = q + n·ρ·sin(e/ρ),     z = 2.04 − ρ + ρ·cos(e/ρ)
after that (straight part, t = e − ρψ):
    position = q + n·(ρ·sin ψ + t·cos ψ),     z = 2.04 − ρ + ρ·cos ψ − t·sin ψ
```

Both sliders start at 0, so the Chone starts flat. At ψ = 90° the leather hangs straight down the side of the foam. The fold uses the flat distance, so the leather never stretches.

### Bend lines

A bend line is a segment `a → b` on the flat pattern, plus:

- an **angle** θ (positive curls toward the palm)
- a **radius** R, measured at the palm face of the foam
- a **flip** flag that chooses which side moves
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
               zc = 2.04 + R      if θ < 0 (curl toward the back)
bend radius    r  = |layer's neutral height − zc|
used length    s  = min(d, |θ|·r)        (the flat length it takes to go round the bend)
turn angle     φ  = sign(θ)·s / r

1. move the point back toward the line by s   (p −= s·n)
2. turn it by φ about the axis through (a, zc), pointing along z × n
```

Points still inside the bend (`d < |θ|·r`) end up on the curve. Points beyond it turn by the full θ as one solid piece.

**Why each layer uses its own radius:** the radius `r` includes the layer's own neutral height. So for the same bend line and angle, the Chone (at 2.04) needs a longer stretch of flat material to go round the bend than Mould 1 (at 1.5) or Mould 2 (at 0.5). That difference is the 3D effect the flat comparison misses.

The turn uses Rodrigues' rotation formula, written out by hand in `bendPoint()`.

#### Several bends at once

Each piece takes only the bend lines it's given, sorted by how far they are from that piece's fixed point. For each vertex, they're applied from the farthest to the nearest:

```
final position = B_nearest( … B_farthest(starting position) )
```

Each bend is worked out on the flat pattern, so the farthest one (for example, the fingertips) is applied while everything is still in place. The nearer bends (the knuckles) then carry the already-bent part along with them. Each bend moves a point as a solid motion, so the bends combine correctly. This works when lines are nested, like the knuckles then the fingertips, or when they cover separate areas, like the thumb and the knuckles.

### Seam reach

This is the number the page is built for. For each point on the Chone stitch line:

- **Finding it on the bent Chone:** it is located in a Chone triangle on the flat pattern (a 0.5" grid makes the search fast). Its bent position is then worked out from that triangle's bent corners, and it is lifted 0.03" off the surface so it draws on top.
- **Measuring:** the script takes the nearest edge point of Mould 1 (from the flat pattern), at both its top and its bottom on the bent model. That gives the direction down the foam side. The reach is how far the stitch point lies along that direction, starting from the top of Mould 1:

  ```
  reach = (S − T) · normalize(B − T)
  ```

  S is the stitch point, T the top of the foam edge, B the bottom of Mould 1's edge. Past 1" the line continues in the same direction, approximately down Mould 2's side.
- **Colour:** green if it reaches the target (2" by default, the full foam stack). If the target equals the full stack when you change a mould's thickness, the target follows the new total. A target you've set to something else stays as it is, amber if within 0.5" of it, red if shorter. The wrist edge is shown grey and left out, because it's sewn to the cuff.
- **Badge:** shows the shortest reach, roughly where it is (fingertips, knuckle side, thumb, index-finger side, wrist), and the percentage of the seam that reaches the target.

### Chone size

The size slider scales the Chone's flat points and stitch line about the origin (the middle of the wrist edge). This is the same pivot `scale_chone.py` uses, so the sizes match the 105–120% DXFs. Changing it re-runs the Chone setup: the edge-wrap distances, the triangle lookup grid, the stitch-point positions and the moving part of every bend line that bends the Chone.

### Placing the pieces

The exporter's fit (Step 1) is only a starting position. In the panel, each piece can be scaled, moved and turned. Each piece has a scale s, an offset (x, y) and a rotation about the centre c of its outline. A placed point is:

```
placed = R(rot) · (point − c) · s + pivot + (x, y)
pivot  = c · s   for the Chone (so it scales about the wrist-edge origin, like scale_chone.py)
pivot  = c       for a mould   (so it scales about its own centre and stays put under the Chone)
```

The Chone's s comes from the Chone Size slider. Each mould's s comes from its own slider in the **Moulds** section (75–125% in 0.5% steps). Each slider shows the mould's width and length in inches and cm. **Moulds back to 100%** resets both sizes and leaves positions alone. "Reset all positions" leaves sizes alone.

All three pieces start at 100%, offset 0 and rotation 0, which is the auto-fit position. Scaling or moving a piece re-runs everything that depends on where it is:

- its triangle lookup grid and texture coordinates
- the moving part of every line that bends it
- the Chone setup (edge wrap and seam-reach lookups), if the piece is the Chone or Mould 1

Lines given only the moved piece move, turn and scale with it, so they stay in the same place on that piece. (Lines on the Chone don't follow the Chone Size slider, which was already the behaviour before.) Lines shared with other pieces stay where they are. While you drag, the move is applied at most once per animation frame.

### Interaction

- **3D picking:** each render vertex's flat (x, y) position is stored in its texture coordinates. A click therefore gives the point on the flat pattern directly, even when the model is bent.
- **Dragging a part:** a click listener that runs before the camera controls finds the part under the pointer. It then picks the bend that moves that point, preferring the bend farthest from the fixed point. Next it turns off the camera controls and changes that bend's angle by 0.6° per pixel of vertical drag. Holding Shift or Alt skips this, so the camera turns instead.
- **Highlighting:** the part that the hovered bend would move is lightened by 18% in each piece it bends, and the selected bend's part by 32%. The selected line is drawn at full colour in 3D, and the other lines are dimmed.
- **Flat pattern panel:** a 2D canvas over a 1" grid, with two tools:
  - **Draw lines:** pick which pieces new lines bend, using the "New lines bend" chips. Dragging draws a new line. Tapping picks the bend that moves that spot, checking the pieces picked for new lines first. Dragging an end dot moves the selected line. The part the selected bend moves is shaded in each piece's colour.
  - **Move pieces:** pick a piece with the "Moving" chips. Only that piece moves. Clicking near another piece's outline doesn't switch to it. Dragging moves it. Shift-drag, or the Rotation slider (±45°), turns it about its centre, which is marked +. "Reset this piece" and "Reset all positions" put pieces back at the auto-fit position.
- **Selected line's pieces:** the "Bends" chips in the line's box choose which pieces it bends. The last chip can't be switched off.
- **Saving:** bend lines (with their pieces), piece positions, the "New lines bend" choice and slider settings are saved in the browser (`localStorage`, key `chone-fit-lab-v2`; the key was changed from `v1` when the defaults changed, so old saved settings are ignored), and only after the page has finished loading. If storage isn't available, the page still works and just doesn't remember anything.
- **Show:** hiding a piece hides it in 3D and in the flat pattern panel (its outline, and the stitch line for the Chone). It also hides its bend lines in 3D, in the flat panel and in the bend list, and they can't be picked by tapping. A line shared with a piece that's still shown stays visible and is drawn on that piece. If the selected line gets hidden, nothing is selected. The bend count says how many lines are hidden.
- **Bend list:** lines are grouped under Chone, Mould 1, Mould 2 and Shared (lines that bend more than one piece, shown with a colour dot for each of their pieces). Each group is sorted by name in number order (Bend 2 before Bend 10). New lines are named one more than the highest "Bend N" already there, so names never repeat. (They used to come from a counter that reset on load, which made duplicates.)
- **Undo:** the **↶ Undo** button at the top of the 3D view, or ⌘Z / Ctrl+Z, steps back through changes. These are: adding, deleting, flipping or flattening lines; dragging a line's ends; bending in 3D; changing a line's pieces, angle or radius; moving, turning, resizing or thickening pieces; the Chone size, edge-wrap and target sliders; "Reset…" buttons; and loading a config. Before each change, the page pushes a full snapshot (up to 100). Continuous input from one control within a second, like dragging a slider, is one step. A click that doesn't actually change anything doesn't add a step. Undo leaves the view settings as they are now: Show, see-through and "New lines bend". The undo history lives only in the open page and is cleared when it reloads.
- **Config files:** **Save config…** writes everything as JSON: the bend lines and their pieces, piece positions, mould sizes and thicknesses, the "New lines bend" choice, and all sliders. In Chrome and Edge it opens a save dialog. Pick the `viewer/` folder, and the next save opens in the same folder. Where that dialog isn't available (Safari, Firefox, some embedded pages), the file is downloaded as `chone-fit-config.json` instead, and you move it into `viewer/` yourself. **Load config…** reads a file back. The page checks it first: bad lines are skipped, and missing fields get their defaults. The browser's own saved copy and config files go through the same `applyConfig()`, so they behave the same. A page can't write into a folder without asking you first, which is why there's a dialog.
- **Redrawing:** changes mark the model as out of date, and the next animation frame recomputes everything. The amount of work is small: about 13,000 vertices times a few bend lines.

### Starting bends

| Name | Line | Angle | Radius |
| --- | --- | --- | --- |
| Thumb | From the thumb notch tip toward (−2.9, 0.6) | 55° | 1.5" |
| Knuckles | y = 9.6, from x −5 to 3 | 70° | 1.5" |
| Fingertips | y = 12.4, from x −4.5 to 3 | 55° | 1.2" |

These are reasonable starting points, not measured from a real glove. Adjust them to match how your foam actually sits.

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
- **Bending pieces separately can make them pass through each other.** Nothing stops a bent mould from passing through an unbent Chone. Pieces don't collide.
- **Not included:** the Chone Cuff, the Cuff Mould and the Front Palm.
- **Untested in a browser here.** It was published after only a syntax check, because the headless-browser screenshot was blocked in this setup.

## Files

| File | Role |
| --- | --- |
| `scripts/export_3d.py` | DXF to `viewer/glove-data.js`: fits the moulds and builds the meshes |
| `viewer/glove-data.js` | Generated mesh data (about 370 KB) |
| `viewer/chone-fit-lab.html` | The viewer: one HTML page with all the code inside it |
| `scripts/chone_mould_relation.py` | The flat 2D comparison this builds on (`renders/chone-mould-relation.png`) |
| `scripts/render_pieces.py`, `scripts/join_chone_cuff.py` | Shared helpers `poly()` and `horizontal_edge()` used by the exporter |
