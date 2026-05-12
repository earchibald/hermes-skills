# Icon SVG Refinement Techniques

Practical SVG edits for responding to agent review feedback on icon concepts. These patterns came from the Loom icon v1.0→v1.1 refinement round, where 4 modification requests were applied to an already-delivered icon.

## 1. Link Color Priority Swap

**Problem:** A review says the dominant visual line should be color A, not color B (currently reversed).

**Technique:** Swap stroke-width, opacity, and filter assignments between the two colors:

```
Before (blue dominant, cyan accent):
  path stroke="#2979FF" stroke-width="2.5" opacity="0.45"   ← thick = dominant
  path stroke="#84FFFF" stroke-width="1.2" opacity="0.35"   ← thin = accent

After (cyan dominant, blue accent):
  path stroke="#84FFFF" stroke-width="3"   opacity="0.7"    ← now thick + filtered
  path stroke="#2979FF" stroke-width="0.8" opacity="0.35"   ← now thin + dashed
  path stroke="#00E676" stroke-width="0.6" opacity="0.15"   ← added third whisper layer
```

**Key considerations:**
- Don't just flip hex values — stroke-width and blur radii must adjust too
- Add a `feGaussianBlur` filter on the new dominant line if it didn't have one
- If the dominant line is a solid glow but the accent is dashed, you may need to swap dash arrays
- Consider adding gradient fills (`<linearGradient>`) on the dominant line for intensity falloff

**Gradient fill example:**
```xml
<linearGradient id="linkGrad" x1="0%" y1="0%" x2="100%" y2="100%">
  <stop offset="0%" stop-color="#84FFFF" stop-opacity="0.8"/>
  <stop offset="50%" stop-color="#84FFFF" stop-opacity="0.5"/>
  <stop offset="100%" stop-color="#2979FF" stop-opacity="0.2"/>
</linearGradient>
<path ... stroke="url(#linkGrad)" ... />
```

## 2. Triangle Proportion Shifts (Forge Silhouette)

**Problem:** A reviewer wants the equilateral triangle stretched into an isosceles shape to suggest a structural metaphor (anvil, base-heavy, grounded).

**Technique:** Move node centers by small pixel deltas (6-12px):

| Node | v1.0 Position | v1.1 Position | Delta |
|------|--------------|--------------|-------|
| Apex | (200, 98) | (200, 92) | y: -6px (higher) |
| Base-L | (100, 268) | (90, 270) | x: -10px, y: +2px |
| Base-R | (300, 268) | (310, 270) | x: +10px, y: +2px |

Base width change: 200px → 220px (+10%). Ratio change: 1:1.16 → 1:1.23.

**Cascading updates required when moving nodes:**
1. Ambient aura circles — same new center
2. Mesh fill polygon — same new points
3. All data line paths — recalculate end coordinates
4. All hex polygons — recalculate all 6 vertices relative to new center
5. All inner ring polygons — recalculate relative to new center
6. Core dots — same new center
7. Glow filter bounds — if significantly off-center, adjust x/y/width/height

**Pro tip for node repositioning:** Keep the hex vertex geometry relative to center by computing vertex offsets once, then applying them from each center:

```
Hex vertices relative to center (cx, cy), flat-top variant, radius r:
  (cx,     cy - r)           — top
  (cx + r*√3/2, cy - r/2)   — top-right
  (cx + r*√3/2, cy + r/2)   — bottom-right
  (cx,     cy + r)           — bottom
  (cx - r*√3/2, cy + r/2)   — bottom-left
  (cx - r*√3/2, cy - r/2)   — top-left
```

Where √3/2 ≈ 0.866. Round to nearest integer for SVG.

## 3. Nuc-1 Distinction (First Among Equals)

**Problem:** A reviewer wants the primary node to stand out more from the secondary nodes without changing the color scheme.

**Technique — cumulative small enhancements, each subtle, that add up to perceptible prominence:**

| Enhancement | How | Magnitude |
|------------|-----|-----------|
| Larger hex radius | r=36 → r=40 | +11% |
| Added outer glow ring | `circle r=46`, light stroke, 12% opacity, 12px blur | New element |
| Brighter ambient aura | opacity 0.12 → 0.18, radius 55 → 60 | +50% brightness |
| Bigger core dot | r=3.5 → r=4.0, catchlight r=1.5 → r=1.8 | +14% |
| Stronger glow filter | stdDev 5→6, bounds -60%→-80% | +20% spread |
| Lighter node fill | `#252932` → `#2A2E3A` at gradient top | Higher contrast |
| Thicker stroke | 2.8 → 3.0 | +7% |
| Additional inner ring | Add a third concentric hex between existing rings | New element |

**Rule of thumb:** Any single enhancement should be almost imperceptible (<15%). The whole set together should read as "that one is brighter" without the viewer being able to say exactly why.

## 4. Particle Systems for "Alive" Mesh

**Problem:** A static icon with 3 data particles looks like a diagram. Reviewers want motion energy.

**Technique:** Distribute particles along each edge path, varied in all dimensions:

```
Before (3 particles, one per edge):
  circle cx=148 cy=165 r=2.5 opacity=0.7
  circle cx=255 cy=165 r=2.0 opacity=0.5
  circle cx=200 cy=268 r=2.0 opacity=0.4

After (10 particles, staggered):
  # Edge 1 (apex→base-L): 4 particles at 25/50/75/85% of path length
  circle cx=148 cy=158 r=2.8 opacity=0.8   — large, bright (near apex)
  circle cx=139 cy=180 r=1.2 opacity=0.4   — small, dim (extranodal)
  circle cx=129 cy=202 r=2.0 opacity=0.55  — medium (midway)
  circle cx=118 cy=226 r=1.5 opacity=0.3   — small, faint (approaching base)

  # Edge 2 (apex→base-R): 4 particles
  ...

  # Edge 3 (base↔base): 3 particles
  circle cx=146 cy=270 r=1.8 opacity=0.5
  circle cx=200 cy=270 r=2.2 opacity=0.6   — center bright (hub)
  circle cx=254 cy=270 r=1.5 opacity=0.4
```

**Varied dimensions to randomize:**
- Radius: 1.0–3.0 (SVG circles)
- Opacity: 0.25–0.8
- Two filter levels: `lineGlow` (stdDev 2.5) for bright particles, `lineGlowSoft` (stdDev 1.5) for dim ones
- Some particles in accent color, most in primary glow color

**Placement heuristic:** Calculate positions at fraction `t` along path from P1 to P2:
- x = P1.x + t*(P2.x - P1.x)
- y = P1.y + t*(P2.y - P1.y)
- Use t = 0.2, 0.4, 0.55, 0.7, 0.85 (non-uniform spacing feels more natural)

## 5. Version Management in index.md

After any refinement round, add a revision history table:

```markdown
## Revision History

| Version | Date | Changes |
|---------|------|---------|
| v1.0 | YYYY-MM-DD | Initial release — concept-name selected |
| v1.1 | YYYY-MM-DD | Refined per {agent}'s vote: {summary of changes} |
```

**Format for change summary:** List each modification request as a short bullet in one line. E.g.: "cyan-white link dominance, wider isosceles base for forge silhouette, 8 data particle trails, enhanced nuc-1 prominence (+outer glow ring, larger hex)"

## 6. Node Size Equalization (Glow-Only Hierarchy)

**Problem:** A reviewer points out that the primary node is geometrically dominant (larger hex, added rings), violating the "no hierarchy" principle. The fix: make all nodes identical size and differentiate by stroke+glow alone.

**This is the inverse of Section 3** (which makes nuc-1 *more* prominent). Here, you *shrink* the primary node's extras and *grow* the secondary nodes to match.

**The key cascade:** Unlike moving centers (Section 2), all node centers stay fixed. But link endpoints change because they connect from **hex-edge midpoints**, not from centers. When hex radius changes, the edge midpoints move, and all paths connecting them need recalculation.

### Step 1: Choose a shared radius

| Starting state | Middle ground | Rationale |
|---------------|---------------|-----------|
| Nuc-1 R=40, Nuc-2/3 R=27 | R=37 for all | Closer to primary (keeps its visual weight) but equalizes geometry |
| Nuc-1 R=40, Nuc-2/3 R=27 | R=27 for all | Shrinks the primary — use if the reviewer is emphatic about identicality |
| Nuc-1 R=36, Nuc-2/3 R=24 | R=30 for all | Even split — useful when the difference is small |

### Step 2: Compute hex vertices from the shared R

Use the flat-top hex formula from Section 2. For a 400×400 viewBox with common centers, precompute offsets once:

```python
# For R=37 (example from v1.1→v2.1)
r = 37
dx = int(r * 0.866)  # 32
dy = int(r * 0.5)    # 18 (or 19 for precision)

vertices = [
    (0, -r),          # top
    (dx, -dy),        # top-right
    (dx, dy),         # bottom-right
    (0, r),           # bottom
    (-dx, dy),        # bottom-left
    (-dx, -dy),       # top-left
]
# Apply from each center
```

### Step 3: Identify link endpoints at hex-edge midpoints

Links connect from edge-to-edge, not center-to-center. For each node pair, identify which hex edge faces the target node, then use that edge's midpoint:

```
For a flat-top hex (6 edges indexed clockwise from top):
  Edge 0 — top:          (cx,     cy-r) → (cx+dx, cy-dy)
  Edge 1 — top-right:    (cx+dx, cy-dy) → (cx+dx, cy+dy)
  Edge 2 — bottom-right: (cx+dx, cy+dy) → (cx,   cy+r)
  Edge 3 — bottom:       (cx,   cy+r) → (cx-dx, cy+dy)
  Edge 4 — bottom-left:  (cx-dx, cy+dy) → (cx-dx, cy-dy)
  Edge 5 — top-left:     (cx-dx, cy-dy) → (cx,   cy-r)

Edge midpoint: ((x1+x2)/2, (y1+y2)/2)
```

Which edge faces the target? The edge(s) whose outward normal points toward the other node:
- **Apex→Base-L** (nuc-1 at 200,78 → nuc-2 at 88,268): use Edge 3 (bottom) or Edge 4 (bottom-left)
- **Apex→Base-R** (nuc-1 at 200,78 → nuc-3 at 312,268): use Edge 2 (bottom-right) or Edge 3 (bottom)
- **Base↔Base** (nuc-2 at 88,268 → nuc-3 at 312,268): use Edge 1 (right) for nuc-2, Edge 5 (left) for nuc-3

### Step 4: Remap particles proportionally to new path lengths

When link endpoints shift, existing particles (placed at fractions `t` along the old path) must be remapped to the new path. This is purely arithmetic — the problem looks like this:

```
Old path: P1=(x1,y1), P2=(x2,y2), length = L
Particle at (px, py): t = distance(P1, particle) / L

New path: P1'=(x1',y1'), P2'=(x2',y2'), length = L'
New particle: (P1'.x + t*(P2'.x-P1'.x),  P1'.y + t*(P2'.y-P1'.y))
```

**Important:** Compute `t` from the original fraction, not from re-measuring the distance in the new geometry. Particles anchored at irregular `t` values (0.204, 0.335, 0.471, ...) should keep those exact fractions on the new path.

Particle color, radius, opacity, and filter should all be preserved as-is — only x,y change.

### Step 5: Remove separated ornamentation

After equalizing sizes, strip any elements that now violate the "identical geometry" rule:

| Element to check | If present on nuc-1 only | What to do |
|-----------------|--------------------------|------------|
| Outer corona rings | `circle` with R>hex, dashed stroke | Remove entirely (corona ≠ identical) |
| Orbiting ellipses | `<ellipse>` with transform rotation | Remove entirely (extra geometry) |
| Inner concentric rings | Inner hex polygons | Remove from all nodes (they were a size-based hierarchy tool) |
| Animations | `<animate>` on rings | Remove entirely (animation is extra) |
| Heartbeat pulse ring | Animated expanding circle | Remove entirely |
| Triskelion/centroid marks | Extra symbols at triangle center | Remove unless reviewer explicitly okays it |

### Example: v1.1→v2.1 delta (Loom icon)

| Aspect | v1.1 (hierarchical) | v2.1 (equalized) |
|--------|---------------------|-------------------|
| Nuc-1 radius | R=40 | R=37 |
| Nuc-2/3 radius | R=27 | R=37 |
| Nuc-1 extras | 2 corona rings, 2 orbiting ellipses, animated heartbeat, 2 inner rings | None — just hex + core dot |
| Nuc-2/3 extras | 1 inner ring each, extra glow aura dot | Removed inner rings for consistency |
| Distinction | Size + rings + glow + animation | Stroke color + filter only |
| Triskelion | 3-arrow rotation at centroid | Removed |
| Link to nuc-2 | `180,108→105,248` | `184,105.5→104,240.5` |
| Link to nuc-3 | `220,108→295,248` | `216,105.5→296,240.5` |
| Base↔base | `115,268→285,268` | `120,268→280,268` |

## Testing Refinements

After any set of SVG edits, re-render all three PNG sizes and verify:
1. **rsvg-convert succeeds** — no parse errors, no clipping
2. **File sizes are reasonable:** 1024=130-160KB, 512=45-65KB, 128=8-12KB
3. **The 128×128 output is legible** — the primary motif (data mesh, hexagons, nameplate) should still be identifiable
4. **Circular crop test** — the main subject is centered and not clipped at edges

## 7. Opacity Floors and Legibility Boundaries

From pixel-level PNG analysis (Hermes's visual review of Loom v2.1), concrete thresholds for what's perceptible at various sizes.

### Opacity floor by background contrast

On `#0A0A0F` background (near-black — our standard):

| Opacity | Element type | Visible at 1024px? | Visible at 512px? | Visible at 128px? | Verdict |
|---------|-------------|-------------------|-------------------|-------------------|---------|
| 1-2% | Stroke/subtle trace | No | No | No | Invisible everywhere |
| 4% | Thin stroke (#84FFFF) | Marginal | No | No | Invisible at practical sizes |
| 8% | Filled shape | Yes (faint) | Barely | No | Too subtle for icons |
| 15-25% | Filled shape | Yes | Yes | Marginal | OK for ambient/secondary |
| 25% | Text (#4A6FA5 on #0A0A0F) | Yes | Faint | No | Use 40%+ for text |
| 50% | Same-color stroke (#1A1D23) | No | No | No | Same-as-bg = invisible |
| 60% | Text | Yes | Yes | OK | Good floor for labels |
| 70%+ | Text | Yes | Yes | Yes | Readable at all sizes |

**General rules of thumb:**
- **Ambient/background elements:** 12-15% minimum. Below 10% is dead weight — add SVG complexity for zero visual return.
- **Secondary text (subtitles, version strings):** 45-60% on dark background. Below 40% disappears at any size below 512px.
- **Structural lines (terminal rules, dividers):** Use a CONTRASTING color, not a dim version of the background. `#2979FF@25%` works where `#1A1D23@50%` (same-as-bg) is invisible.
- **Ghost elements (forge traces, silhouette echoes):** 20-25% minimum with visible stroke width (0.5px+). Below 15% adds SVG nodes with zero-pixel ROI.
- **Nameplate in 24pt at 400px viewBox:** 50-70% opacity, but the font-size-to-viewBox ratio is the real limiter at 128px (see below).

### The 128px legibility math

When an icon's viewBox is 400×400 and it's rendered at 128×128px, the effective scale factor is:

```
128 / 400 = 0.32 (32%)
```

A 24pt font at 400px → **24 × 0.32 = 7.68pt effective** at 128px. That's below the 8pt threshold for legible text on most displays — individual characters become blobs.

**To make 128px text legible, you need:**
- A dedicated 128px-only SVG source with **larger text** (e.g., 72pt instead of 24pt)
- Or use icon-only at 128px (no text)
- Or design for the nameplate to be unreadable at 128px and accept that

**The 128px variant decision matrix:**

| What the icon contains | 128px approach | When to create a variant |
|------------------------|---------------|--------------------------|
| Only geometric shapes | Single SVG, no variant needed | Always — shapes scale fine |
| Nameplate text | Dedicated 128px SVG with enlarged text | Required for readability |
| Subtitle + nameplate | Dedicated 128px SVG with text-only (drop subtitle) | Recommended |
| Complex multi-layer glows | Simplify glow passes for 128px | Optional — glow clipping is acceptable |

### Creating a dedicated 128px variant

```bash
# Create a separate SVG with enlarged viewBox coordinates
# Scale factor: 128/400 = 0.32, so adjust by ~3x for viewBox matching

# Original: viewBox="0 0 400 400", font-size="24", letter-spacing="6"
# 128px:   viewBox="0 0 400 400", font-size="72", letter-spacing="4"
#          (24 / 0.32 ≈ 75 → use 72 for roundness)
```

The dedicated variant goes in the same `corpus/icons/` directory as `{agent}-icon-128-source.svg`.

### SVG comment gotcha for opacity debugging

When an agent reports "element X is invisible at 4% opacity" and you want to confirm, search the SVG for all opacity values below 0.15:

```bash
grep -n 'opacity="0\.0[0-9]' input.svg
grep -n 'opacity="0\.1[0-4]' input.svg
```

These are suspicious elements that should be reviewed for visibility.

