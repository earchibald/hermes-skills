# SVG → PNG Rendering

## Primary: rsvg-convert (librsvg)

**Install:**
```bash
# macOS
brew install librsvg

# Linux
apt install librsvg2-bin

# Verify
rsvg-convert --version
# Expected: "rsvg-convert version 2.62.x"
```

**Commands:**

```bash
# Single file, specific size
rsvg-convert -w 1024 -h 1024 input.svg -o output.png

# Batch render all concepts at preview size
for f in concept*.svg; do
  rsvg-convert -w 512 -h 512 "$f" -o "${f%.svg}.png"
done

# Batch render final icon at all resolutions
for size in 1024 512 128; do
  rsvg-convert -w $size -h $size agent-icon-source.svg \
    -o "agent-icon-${size}.png"
done
```

**PNG size expectations** (512×512, 3 SVG concepts):
- Icon with simple geometry (hexagons, lines): ~40-45KB
- Icon with text, many elements (terminal frame): ~30-35KB
- Icon with gradients, glow filters: ~40-50KB

## Fallback: cairosvg

May fail on pyenv Python 3.12+ (`cffi` import error → `ModuleNotFoundError`). Try only if rsvg-convert is unavailable:

```bash
pip install cairosvg --break-system-packages  # may still fail
cairosvg input.svg -o output.png --output-width 1024
```

**Do not spend time debugging cairosvg.** If it fails, use rsvg-convert.

## Verification

```bash
# Check file sizes and dimensions
file *.png           # Shows dimensions
ls -lh *.png         # Shows file sizes
```
