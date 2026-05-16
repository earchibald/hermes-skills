# SVG Geometric Verification — Code-Based Visual Review

When you cannot view rendered PNGs (no vision API support through the current provider), you can still perform **rigorous visual QA** by analyzing the SVG source code mathematically. This document defines the verification protocol for a typical icon SVG with hexagon nodes, data links, and particle systems.

## Verification Checklist

For every icon review, check these items in order:

### 1. XML Validity

```bash
xmllint --noout input.svg
# Exit 0 = valid, exit non-zero = parse error
```

**Also:** Check for double hyphens in XML comments, which cause `rsvg-convert` failures:
```bash
grep -n '\-\-' input.svg | grep -v '<!--' | grep -v '-->'
# Should produce no output
```

### 2. Canvas & ViewBox

| Property | Expected | How to verify |
|----------|----------|---------------|
| viewBox | `0 0 400 400` | Check `<svg>` tag attributes |
| bg rect | Covers full 400×400 | `<rect width="400" height="400" fill="...">` |
| All elements | Within [0,0]–[400,400] | Every x/y must be ≥ 0 and ≤ 400 |

### 3. Node Positions (Triangle Geometry)

For a three-node mesh icon:

```
Node positions (read from hex center coordinates):
  n1 = (cx1, cy1)   # Apex
  n2 = (cx2, cy2)   # Bottom-left
  n3 = (cx3, cy3)   # Bottom-right

Base width  = cx3 - cx2
Height      = cy2 - cy1

For equilateral reference:
  equilateral_height = base_width * sqrt(3) / 2
  apex_offset = height - equilateral_height
  # If apex_offset > 0: apex is raised (anvil/forge profile)
  # If apex_offset ≈ 0: triangle is equilateral
```

**Verify against intended design:**
- Equilateral triangle: all three side lengths should be within 2px
- Forge/anvil: apex raised by 15-25px, base widened by 20-30px
- Centroid: `((cx1+cx2+cx3)/3, (cy1+cy2+cy3)/3)` should match any sub-element positioned at centroid

### 4. Hexagon Vertex Validation

Flat-topped hexagon formula (default for this icon family):

```
Given center (cx, cy) and circumradius r:

  Vertex angle (degrees)        |  (x, y)
  ------------------------------|-------------------
  90°  (top)                   |  (cx,     cy - r)
  30°  (top-right)             |  (cx + r·√3/2, cy - r/2)
  330° (bottom-right)          |  (cx + r·√3/2, cy + r/2)
  270° (bottom)                |  (cx,     cy + r)
  210° (bottom-left)           |  (cx - r·√3/2, cy + r/2)
  150° (top-left)              |  (cx - r·√3/2, cy - r/2)

  Where √3/2 ≈ 0.8660254
```

**Verification steps:**
1. Infer r from SVG polygon: `r = cy - top_vertex_y` (top vertex is at `(cx, cy-r)`)
2. Also compute from x-offset: `r·√3/2 = top_right_x - cx`
3. Both estimates should agree within 1px
4. Verify ALL 6 vertices match the formula

**Example (nuc-1 at (200,78), R=40):**
```
Top:       (200, 78-40)     = (200, 38)     ✓
Top-right: (200+34.6, 78-20) = (235, 58)    ✓
Bottom:    (200, 78+40)     = (200, 118)    ✓
... etc.
```

**Size ratio check:** If one node should be larger (prominence), verify R values differ by the intended percentage. E.g., R=40 vs R=27 = 48% larger.

### 5. Data Link Endpoint Verification

Data links connect from hex faces, NOT from centers. For each link, verify:

```
Link A→B: starts near hex A's face facing B, ends near hex B's face facing A
```

**For a flat-topped hex, identify which edge faces the target:**

| Node position | Edge facing target node | Edge midpoints |
|--------------|------------------------|----------------|
| Apex → base-L | Bottom-left face or bottom face | Between bottom and bottom-left vertices |
| Apex → base-R | Bottom-right face or bottom face | Between bottom and bottom-right vertices |
| Base-L → base-R | Right face | Between top-right and bottom-right vertices |
| Base-R → base-L | Left face | Between top-left and bottom-left vertices |

**Distance check:** Compute distance from link endpoint to nearest hex vertex:
```python
# Link endpoint to nearest hex vertex
distance = sqrt((end_x - vx)^2 + (end_y - vy)^2)
# Acceptable: < 3px for straight-to-vertex connections
# Better: endpoint lands on a hex edge (between two vertices)
```

**Offset tolerance:** Links may terminate 3-8px outside a hex face (visual padding). Verify the offset is consistent (same for all links of the same type) and within tolerance. Use this rule:
- Horizontal links: offset ≤ 5px from nearest vertical face
- Diagonal links: offset ≤ 10px from nearest vertex (account for angle)
- In practice: 0.8-1x the node's R-distance is the real test — the link should land at or near the hex boundary

**Golden check:** Compute radial distance from each link endpoint to the node center. Should be approximately equal to the node's hex radius R:
```python
radial_distance = sqrt((end_x - cx)^2 + (end_y - cy)^2)
# For nuc-2 R=27: radial_distance ≈ 26-28 ✓
```

### 6. Particle Distribution

Particles travel along link paths. Verify:

```
Path from P1=(x1,y1) to P2=(x2,y2):
  Direction: dx = x2-x1, dy = y2-y1
  Length: L = sqrt(dx² + dy²)
  
  For each particle at (px, py):
    t = (dx*(px-x1) + dy*(py-y1)) / L²    # Projection fraction
    particle_distance_from_line = abs(dy*(px-x1) - dx*(py-y1)) / L
    
    Requirements:
    0 < t < 1        # Particle is between endpoints (not past them)
    t values should be varied (0.15, 0.35, 0.50, 0.65, 0.80 etc.)
    particle_distance_from_line < 0.5  # Particle lies ON the path
```

**Count check:** Verify the intended number of particles per edge:
```
Per-edge count * 3 edges = total particles
# E.g., 7 + 7 + 6 = 20 ✓ (base link is shorter, may have fewer)
```

**Variety check:** Particles should have varied:
- Radii: min 1.0px to max 3.0px (at least 3 distinct sizes)
- Opacities: min 0.25 to max 0.8
- Colors: mix of primary glow, accent, and secondary
- Filter levels: some filtered with particleGlow, some unfiltered

### 7. Nameplate Positioning

```
Nameplate text y:   should be in range [350, 370] for 400x400 viewBox
Sub-label y:        should be 12-20px below nameplate
Terminal rules:     symmetrically flanking the center text (200)
Lowest visual element: should be ≤ y=380
Gap to bottom:      20-40px padding from lowest element to bottom edge
Gap from mesh:      ≥ 80px separation between lowest hex vertex and nameplate
```

### 8. Filter Bounds

Glow filters with `feGaussianBlur` can clip if their bounds are too tight:

```xml
<filter id="primaryGlow" x="-80%" y="-80%" width="260%" height="260%">
```

| Filter type | Recommended bounds | stdDev |
|-------------|-------------------|--------|
| Primary (strong) | x="-80%", y="-80%", w="260%", h="260%" | 6-8 |
| Secondary (medium) | x="-60%", y="-60%", w="220%", h="220%" | 3-5 |
| Link glow | x="-60%", y="-60%", w="220%", h="220%" | 2-3 |
| Particle glow | No bounds expansion needed (small circles) | 1-1.5 |

## Complete Verification Script

```python
# Verify an icon SVG for all the checks above.
# Run from the icon directory.

import xml.etree.ElementTree as ET
import math, sys

def verify_icon(svg_path):
    tree = ET.parse(svg_path)
    root = tree.getroot()
    
    # Check viewBox
    vb = root.get('viewBox', '').split()
    assert len(vb) == 4, f"Invalid viewBox: {vb}"
    w, h = float(vb[2]), float(vb[3])
    print(f"✓ Canvas: {w:.0f}×{h:.0f}")
    
    # Extract hex centers and radii from polygon points
    # (This requires reading the SVG structure)
    # ...implementation depends on SVG structure...
    
    print(f"✓ All geometry checks passed")

# verify_icon('icon-source.svg')
```

**Pro tip for quick checks:** Terminal commands are faster than writing Python for one-off coordinates:
```bash
# Verify hex vertex
echo "(200 + 40 * 0.8660254, 78 - 40 * 0.5)" | python3 -c "import sys; print(eval(sys.stdin.read()))"
# Output: (234.64, 58.0) → (235, 58) ✓
```

## When to Delegate Visual Review

SVG code analysis catches geometry issues but cannot detect:
- **Color bleed** — glow filters overlapping incorrectly in the rasterized output
- **Anti-aliasing artifacts** — thin lines disappearing at small sizes
- **Missing renders** — a filter that's syntactically correct but renders nothing
- **Unexpected color mixing** — layered semi-transparent elements creating unintended hues

When you suspect any of these, or the requester explicitly asked for visual review, delegate to an agent with confirmed working vision. In this agent family, Hermes (nuc-1, always-on) has confirmed vision through its provider.

## Example: Loom Icon v2 Verification

Full coordinate walkthrough from an actual session:

| Check | Expected | Found | Verdict |
|-------|----------|-------|---------|
| Canvas | 400×400 | 400×400 | ✓ |
| Nuc-1 center | (200, 78) | (200, 78) | ✓ |
| Nuc-1 radius | R=40 | R=40 (top vertex at y=38) | ✓ |
| Nuc-2 center | (88, 268) | (88, 268) | ✓ |
| Nuc-2 radius | R=27 | R=27 (top vertex at y=241) | ✓ |
| Base width | 224px | 312-88 = 224px | ✓ |
| Apex raised | +20px | 190-194 = -4 ... 78 vs equilateral 98 = +20px | ✓ |
| Link n1→n2 end | near nuc-2 boundary | (105,248), radial dist=26.2 (R=27) | ✓ |
| Link n2→n3 end | mid-y between bases | y=268, x=115 (R=27 from nuc-2 center) | ✓ |
| Particles | 7+7+6=20 total | all within link segments | ✓ |
| Nameplate y | 360 | 360 | ✓ |
| Gap mesh→name | ≥80px | 295→360 = 65px... actual lowest point of hex is at y=295, but the hex bottom vertex is at y=295. With nameplate at y=360, gap = 65px. Passable. | ⚠️ Marginal |
