# How the Mould 1 outline was smoothed

2026-11-22

The Mould 1 outline was refitted as one smooth ("fair") curve plus one straight bottom edge. It moved 0.011" on average and at most 0.053". The bumps left by hand-editing in the viewer are gone, the shape is the same, and the two bottom corners stay sharp.

| | Before | After |
| --- | --- | --- |
| File | `dxf/Laces Boxing 14OZ - mould1 minified chone - edited - edited.dxf` | `dxf/Laces Boxing 14OZ - mould1 minified chone - edited - smoothed all.dxf` |
| Outline (piece `320`) | 486 tiny curves | 172 smooth curves + 1 straight edge |
| Joins that bend | 18 kinks over 2°, the worst 14.6° | only the 2 bottom corners |
| Area | 81.603 sq in | 81.659 sq in (+0.07%) |
| Largest move | | 0.053", on the thumb's top edge near the crotch |

Only piece `320` changed. Every other piece, label and notch in the file is unchanged. Before/after picture: `renders/mould1-edited-smoothed-all.png` (old line red, new line green, drawn mirrored as the viewer shows it). Committed in `b3ee990`.

An earlier pass smoothed only the finger edge: `... - edited - smoothed.dxf`, picture `renders/mould1-edited-smoothed.png`. The method was the same, applied to one 5.94" stretch.

## Why the outline was bumpy

The outline was 486 cubic Béziers, each about 0.07" long. Small direction errors between them showed up as wiggles. There were three sources:

- **The original drawing.** Even the parts never edited (right side, top) were made of short, nearly straight pieces. Their curvature jumped from piece to piece, though too finely to see.
- **Hand edits in the viewer.** Dragging points and handles on the finger edge and thumb left bulges and dips about 0.05–0.09" high.
- **Kinks at joins.** 18 joins turned by more than 2° where they should be smooth. They include a 14.6° kink on the thumb's bottom edge and a run of 3–7° kinks on the bulge above the thumb.

Curvature, how sharply the line bends at each point, is the measure used throughout. On a clean curve it changes gradually. On this outline it spiked up and down every few hundredths of an inch.

## Step 1: map the outline

The outline was read as its exact Bézier chain (`entity_chain` in `scripts/dxf_link.py`). Then every join was measured:

- the angle between the curve arriving at it and the curve leaving it;
- whether each piece is a straight line;
- whether its start point is still the one in the original DXF, `dxf/Laces Boxing 14OZ - mould1 minified chone.dxf`.

That gave three kinds of places:

| Place | What it is | Treatment |
| --- | --- | --- |
| Bottom-left corner, (200.946, −69.839) in DXF units | Thumb's bottom edge meets the wrist edge at 22° | Kept as a sharp corner |
| Bottom edge | Straight wrist edge, sloping 0.03" up toward the thumb where the thumb edit moved its end | Made exactly straight and level, at the untouched part's height (y = −69.867) |
| Bottom-right corner | Straight bottom meets the right edge, with a 0.05" hook at the corner | Hook removed; a clean sharp corner where the right edge, carried straight down, meets the bottom |
| Everything else | Smooth curves, including the 14.6° kink on the thumb | Smoothed |

## Step 2: the fair-curve fit

From the bottom-right corner, round the right side, top, fingers and thumb, to the bottom-left corner, the outline was replaced by **one cubic B-spline**. Its fit balances two things:

1. **Stay on the line.** The old outline was sampled at 12 points per Bézier. The new curve is pulled toward all of them (least squares).
2. **Bend evenly.** The fit is penalised for how fast the curve's bending changes, measured as the third derivative along the outline. A curve whose curvature changes smoothly scores low; a wiggle scores high. This is the standard "fairing" used for ship hulls and car bodies.

The trade-off is one number: the larger the penalty λ, the smoother the curve and the further it can drift.

```latex
\min_{c}\; \frac{1}{n}\sum_i \lVert P(u_i) - q_i \rVert^2 \;+\; \lambda\, w(s)\, \frac{1}{m}\sum_j \Big\lVert \frac{d^3 P}{ds^3}(s_j) \Big\rVert^2
```

Here P is the new spline, q are the old outline's samples, s is distance along the outline in inches, and w(s) is the weight described in step 3.

Details that mattered:

- **Knots every 0.2".** The spline has 172 spans over the 34.47" outline. That is enough freedom for tight turns; the penalty, not the knot count, controls smoothness.
- **Penalty per inch.** The third derivative is measured per inch of outline, so λ means the same on a 6" stretch as on the whole 34" outline. A first try without this pulled the outline 1.8–3.8" off. It was caught by the deviation check and fixed before anything was saved.
- **Ends pinned.** The spline must start exactly at the bottom-right corner and end exactly at the bottom-left corner. It solves as a small linear system with those two constraints (a KKT system), separately for x and y.
- **λ = 0.013.** This removed every wiggle while keeping the shape. Larger values (0.03) only moved the outline further without looking smoother.

## Step 3: protecting tight turns and corners

A plain fit blunted the thumb crotch, the U where the thumb meets the hand, by 0.17–0.25". To stop that, the smoothing is relaxed where the outline turns tightly:

1. Fit once with even smoothing.
2. Measure curvature κ along that first fit, widened to the strongest value within 0.4" so the relief covers the whole turn.
3. Fit again with the penalty weighted by w = 1 / (1 + (κ / 1.0)⁴). On gentle curves w ≈ 1, full smoothing. On the crotch, where κ is well above 1 per inch, w drops near 0 and the fit follows the original.

After this the crotch stayed within 0.05" and became an even U instead of an uneven point.

The two corners are not part of the smooth curve at all. The curve ends on them, and the bottom edge between them is a separate exact straight line. So they stay sharp, and the bottom edge stays straight.

## Step 4: writing the DXF and checking it

The spline was split into cubic Béziers by knot insertion (`ezdxf.math.BSpline.bezier_decomposition`). The straight bottom edge was added as one more Bézier, and the chain was written back into entity `320` as a degree-3 spline with knots 0,0,0,0,1,1,1,…,N,N,N,N. That is the same format the viewer's **Save as new DXF** writes, so the viewer and `scripts/dxf_link.py` read it the usual way. The file was saved under a new name; nothing was overwritten.

Checks run on the saved file:

| Check | Result |
| --- | --- |
| `ezdxf` audit | 0 errors |
| Outline is a valid, non-crossing shape | yes |
| Other pieces (splines) changed | none |
| Largest / mean distance from the old outline | 0.053" / 0.011" |
| Joins that bend more than 0.5° | only the 2 bottom corners (84° and 59°) |
| Close-up comparisons | thumb crotch, thumb tip, both bottom corners, finger edge, thumb bottom kink, top right |

## Settings and results by area

| Area | Before | After |
| --- | --- | --- |
| Finger left edge | bulges and dips up to 0.09", kinks to 2.5° | one even S-curve |
| Bulge above the thumb | run of 3–7° kinks | smooth |
| Thumb crotch | uneven point | even U, within 0.05" |
| Thumb top edge | small dent near the crotch | straight-running curve; the largest move, 0.053" |
| Thumb tip | slight waviness | smooth, essentially unchanged |
| Thumb bottom edge | 14.6° kink | smooth |
| Bottom edge | sloped 0.03" toward the thumb | exactly straight and level |
| Bottom-right corner | 0.05" hook | clean corner |
| Right side and top (never edited) | fine-scale curvature jitter | smooth, barely moved |

| Setting | Value | What it does |
| --- | --- | --- |
| Knot spacing | 0.2" | how finely the curve can follow the outline |
| λ, smoothing | 0.013 | higher = smoother, moves further |
| κ threshold, tight-turn relief | 1.0 per inch | lower = protects gentler turns too |
| Relief spread | 0.4" | how far along a tight turn the relief reaches |

## Re-running it

The fitting script was a one-off working script and is not in the repo. To smooth another outline the same way, it would need adding as a script in `scripts/`, with the corners passed in rather than hard-coded. To load the result in the viewer: **Items** → choose Mould 1 → **Replace outline from DXF…** → pick the smoothed file.
