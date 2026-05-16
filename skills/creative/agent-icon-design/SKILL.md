---
name: agent-icon-design
description: "Design SVG icons/avatars for AI agents: draft SVG concept variants, render PNGs via rsvg-convert, coordinate multi-agent review via vault, deliver multi-resolution icon sets."
version: 1.0.0
author: Argus
created_by: agent
platforms: [macos, linux]
trigger: "User asks to design, create, or generate an icon or avatar for an AI agent. User asks about the icon generation process used for a previous agent."
tags: [icon, svg, avatar, branding, visual-identity, multi-agent, design]
---

# Agent Icon Design

Design SVG icons for AI agents from their identity documents. The pipeline produces vector source + multi-resolution PNGs + a deliverable index. Designed for agents without vision support — relies on prose identity docs (`my_icon_prompt.md`) and structured SVG drafting rather than image-to-image generation.

## Architecture

```
Corpus identity docs (bio, soul, my_icon_prompt.md)
    │
    ▼
3 SVG concept variants (hand-drafted)
    │
    ▼
HTML gallery for side-by-side comparison
    │
    ▼
Multi-agent review (vault broadcast + Discord @mentions)
    │
    ▼
Refine winner → standalone SVG master
    │
    ▼
Render PNG set (1024×1024, 512×512, 128×128) via rsvg-convert
    │
    ▼
Write index.md with gallery + Obsidian embed snippets
    │
    ▼
Journal entry + memory update
```

## Pipeline

### Phase 1: Identity Reading

Read the agent's corpus documents first:
- `biography.md` — facts, origin, role
- `soul.md` — voice, personality
- `mission.md` — purpose
- `my_icon_prompt.md` — visual brief (may already exist)

If `my_icon_prompt.md` doesn't exist, create it from the other docs. It should define:
- **Core concept** — 1-2 sentence essence of who this agent is visually
- **Primary motif** — the main visual element (eye, node, wreath, etc.)
- **Secondary motif** — accent symbols (serpent arcs, data lines, stars)
- **Color palette** — table with: role, color name, hex, notes
- **Composition** — square format, preferred aesthetic
- **Mood** — what the icon should feel like (calm, orderly, warm)
- **Avoid** — explicit negatives (no faces, no eyes, no domestic imagery)

### Phase 2: SVG Concept Drafting

Draft exactly **3 distinct concept directions** as standalone SVG files. Each should be a valid `<svg>` at viewBox `0 0 400 400` (renders cleanly at any size).

### SVG Anti-Patterns

- **Don't** use `<foreignObject>` — rsvg-convert may not render it
- **Don't** rely on CSS animations — the PNG is static
- **Do** pre-calculate exact coordinates — the viewer has no tolerance for off-by-pixel alignment
- **Do** use `<g>` tags for logical grouping (background, data lines, nodes, nameplate)

### Winnowing Criteria (for tie-breaking)

| Criterion | What it tests |
|-----------|--------------|
| **128×128 legibility** | Does the concept survive downscaling? |
| **Circular crop** | Does the center hold if cropped to a circle (Discord avatar)? |
| **1-second first impression** | Can you tell what it is at a glance? |
| **Symbolic density** | Does every element carry meaning? |
| **Color contrast** | Do the accents pop against the dark background? |

### Concept Diversity Guidelines
- **Concept 1 — The Safe Choice**: Symmetrical, centered, most legible at small scale. Best candidate for Discord circular crop. Good if you can't decide.
- **Concept 2 — The Bold One**: Dynamic composition, asymmetric, tells a story. May sacrifice small-scale legibility for visual impact.
- **Concept 3 — The Thematic**: Deeply specific to the agent's role/medium. CLI-native, domain-insider, witty.

**SVG design principles for icons:**
- Use `viewBox="0 0 400 400"` for a clean coordinate system
- Keep strokes simple: `stroke-width="2"` or `2.5` for 400x400 scale
- Use `<defs>` for gradients, glows, and reusable filters
- Put data lines/background elements BEFORE foreground shapes (SVG paints in source order)
- Centered nameplate at bottom `y="355"` with flanking horizontal rules
- Agent name in monospace, letter-spacing 3-4px, at 50-65% opacity
- Glows: `feGaussianBlur` + `feMerge` for hard elements, standalone blur for ambient
- Background: near-black `#0A0A0F` with radial gradient `#1A1D23` center glow

**Color palette conventions (from our agent set):**

| Role | Example | Usage |
|------|---------|-------|
| Background | `#0A0A0F` | Terminal darkness, infinite void |
| Structure | `#1A1A2E` / `#1A1D23` | Deep indigo / graphite — depth & framing |
| Primary accent | `#00E5FF` (cyan) / `#00E676` (green) | The active signal, agent's core color |
| Secondary accent | `#2979FF` / `#4A6FA5` | Supporting data, sibling nodes, secondary elements |
| Warm accent | `#FFB347` → `#FF8C00` / `#FFAB00` | Mythological warmth, alert sparingly |
| Data glow | `#84FFFF` | Data lines, particle streams, active connections |
| Pure highlight | `#FFFFFF` | Catchlight, pupil spark, status dot |

### Phase 3: HTML Gallery

Create an HTML gallery that shows all 3 concepts side-by-side for visual comparison:

```html
<!DOCTYPE html>
<html>
<head>
  <style>
    body { background: #0A0A0F; font-family: monospace; padding: 40px; }
    .gallery { display: flex; gap: 30px; justify-content: center; flex-wrap: wrap; }
    .card { background: #111114; border: 1px solid #1A1D23; padding: 24px; width: 300px; }
    .card svg, .card object { width: 100%; height: auto; }
    .tag { font-size: 10px; padding: 2px 8px; background: #1A1D23; }
  </style>
</head>
<body>
  <!-- 3 .card elements with .svg rendered via <object> tags -->
</body>
</html>
```

The gallery HTML should include:
- Concept title + short code name
- Embedded SVG via `<object>` tag (works with local files)
- Tags/keywords
- Description (2-3 sentences on what the concept communicates)
- Pros/notes section for voting guidance
- A vote area at the bottom for agents

### Phase 4: SVG→PNG Rendering

Use `rsvg-convert` from `librsvg`:

```bash
# Install if needed
brew install librsvg  # macOS
apt install librsvg2-bin  # Linux

# Render single resolution
rsvg-convert -w 1024 -h 1024 input.svg -o output.png

# Render all 3 concepts at preview size
for f in concept*.svg; do
  rsvg-convert -w 512 -h 512 "$f" -o "${f%.svg}.png"
done
```

**⚠️ XML comment gotcha:** Before rendering, verify that NO SVG comment contains `--` (double hyphen). Even well-formed-looking comments like `<!-- nuc-3 -- wider base -->` will fail. Use the `--` search:
```bash
grep -n '\--' input.svg
# Review hits — only `<!--` openers and `-->` closers should appear
```
Or use `xmllint` to validate before rendering:
```bash
xmllint --noout input.svg
```

**Fallback:** `cairosvg` (`pip install cairosvg`) — may fail on pyenv Python 3.12+ due to `cffi` import issues. Prefer `rsvg-convert`.

### Phase 5: Multi-Agent Coordination

After drafting concepts, initiate multi-agent review:

1. Write a **goal document** to `Agent-Share/broadcast/loom-icon-goal.md` (or target agent's name)
2. Write a detailed **inbox note** to `Agent-Vault/{target}/inbox/icon-review-from-{sender}.md`
3. Send **Discord message** to `#agent-round-table` tagging both agents with bot IDs:
   - Hermes: `<@1502772996606263397>`
   - Loom: `<@1503436035693215774>`
   - Argus: `<@1503266917798903901>`
4. Include in the Discord post: concept names, short descriptions, PNG locations (vault path), and voting instructions
5. Set a **deadline** — "by morning" for overnight work, "by next session" otherwise

**Voting format for agents:**
```
**Pick:** concept-XX
**Notes:** <what works, what to change>
```

**Vision proxy note:** Some agents may not have vision support (e.g., deepseek v4 pro → no vision). Those agents can read SVG source directly to evaluate composition but cannot visually review PNGs. Agents with vision (deepseek v4 flash) should proxy image review. Document this in the broadcast.

**⚠️ Vision capability is provider-dependent.** Even a "vision-capable" model (e.g., deepseek v4 flash) may not have image input support through all providers. The `image_url` content type may be rejected by some API endpoints. When the designated vision proxy cannot actually receive images, fall back to:
- **Coordinate-level SVG analysis** — read the SVG source text directly and describe what the geometry produces. You know what you built.
- **Delegation to a known-working vision agent** — in this agent family, Hermes (nuc-1, always-on) has confirmed working vision through its provider. Request visual QA via vault inbox + Discord ping.
- **Transparent capability disclosure** — If you cannot see images, say so clearly. Never claim "the icon looks good" if you can't verify it visually.

**Vision proxy correction pattern:** A no-vision agent requesting visual review may mistakenly address the wrong agent (e.g., asking Hermes when Argus is the designated proxy). When this happens, don't just forward the request — note the confusion in your response, clarify which agent handles visual QA, and still perform the action that's yours to own (SVG refinement, re-rendering, vault sync). The correction is a gentle informational note, not a blocking issue.

**Selection criteria (for tie-breaking):**
1. Legibility at 128×128 (favicon size) — if motif disappears, it's not the winner
2. Discord circular crop test — main element should be centered
3. Distinctiveness from sibling agents' icons
4. Symbolic alignment with identity document

#### Asynchronous Voting & Late-Vote Handling

In a distributed multi-agent system with different availability models (always-on vs session-based), votes may arrive after a deadline or after an executive decision was already made. Handle late votes constructively:

1. **Acknowledge immediately** — Don't ignore late votes just because v1.0 already shipped. The voter invested thought.
2. **Treat as refinement, not restart** — Late-arriving votes become v1.1 against the already-completed v1.0. Do NOT discard finished work. Map each modification request to a surgical SVG edit.
3. **Respond point-by-point** — Every modification request gets its own section in the response with explicit status: "Done ✅", "Already present ✅", "Deferred to future version", or "Clarification needed ❓". Show the specific delta (coordinates changed, colors swapped, filters added).
4. **Version the output** — Add a Revision History table to `index.md` with version numbers (v1.0 → v1.1 → v1.2). Each entry documents what changed and why.
5. **Re-render all PNGs** — From the updated SVG master. The 1024, 512, and 128 builds must all be regenerated from the same source.
6. **Sync and notify** — Copy updated files to remote vaults (scp to NUC if one-way rsync), write response to the voter's inbox, and ping Discord #agent-round-table.

### Phase 6: Final Refinement

Once a concept is selected (or user chooses), create the final SVG master:

- **Canvas:** 1024×1024, viewBox `0 0 400 400`
- **Refinements to make during finalization:**
  - Increase stroke contrast for small-scale legibility
  - Add or strengthen the nameplate
  - Tidy <defs> — remove unused gradients/filters from concept exploration
  - Add a glow layer behind the primary motif for depth
  - Center the composition for Discord circular crop (center is 200,200)

**File naming convention:**
```
{agent-name}-icon-source.svg    # Vector master
{agent-name}-icon-1024.png      # General purpose (131-200KB)
{agent-name}-icon-512.png       # Discord bot avatar (40-60KB)
{agent-name}-icon-128.png       # Favicon (5-10KB)
index.md                        # Gallery + embed snippets
```

### Phase 7: Deliverables

Create `index.md` in `corpus/icons/`:

```markdown
# {Agent Name} Icons

| Size | File | Preview |
|------|------|---------|
| 1024×1024 | [`{agent}-icon-1024.png`]({agent}-icon-1024.png) | <img src="{agent}-icon-1024.png" width="200"/> |
| 512×512 | [`{agent}-icon-512.png`]({agent}-icon-512.png) | <img src="{agent}-icon-512.png" width="128"/> |
| 128×128 | [`{agent}-icon-128.png`]({agent}-icon-128.png) | <img src="{agent}-icon-128.png" width="64"/> |

## SVG Source

[`{agent}-icon-source.svg`]({agent}-icon-source.svg) — vector master. Re-render with:
```bash
rsvg-convert -w 1024 -h 1024 {agent}-icon-source.svg -o {agent}-icon-1024.png
```

## Obsidian Embedding
```markdown
![[corpus/icons/{agent}-icon-1024.png|200]]
```

## Design Notes
**Concept** — <1-2 sentence essence>

**Colors:**
- Background: `#0A0A0F`
- Primary accent: `#XXXXXX`
- Secondary: `#XXXXXX`

**Symbolism:**
- <motif> — <what it means>
- <motif> — <what it means>
```

### Phase 8: Cleanup

After final delivery:
- Remove the gallery HTML (`gallery.html`) — it was an interim tool
- Remove temporary concept PNGs (concept01-*.png, etc.) — only keep the winner's final set
- Keep the non-winning SVGs? Optional. They're small files and document the exploration. Consider archiving to a `concepts/` subdirectory if the user wants to keep them.
- Write a journal entry
- Update memory with icon design facts

## Pitfalls

- **SVG viewBox vs width/height mismatch.** The `viewBox` defines the coordinate system; `width`/`height` define display size. Use viewBox `0 0 400 400` for sanity, render PNGs at target resolution regardless.
- **Double-hyphen in XML comments kills `rsvg-convert`.** SVG comments (`<!-- ... -->`) MUST NOT contain `--` (double hyphen) anywhere inside — even between em dashes or as sentence separators. `rsvg-convert` returns: `XML parse error: Comment must not contain '--' (double-hyphen)`. Always check comments for accidental double hyphens before attempting a render. Use `~` or `—` (em dash U+2014) as separators instead.
- **Vision unavailable on this model/provider.** If the `vision_analyze` tool fails with `unknown variant 'image_url', expected 'text'` (or similar), the provider does not support image input even if the model is nominally vision-capable. Do NOT claim you can see the icon. Instead, perform a **SVG code-based visual review** — the most rigorous alternative to seeing: verify every coordinate, every hex vertex, every link endpoint, every particle position, filter bounds, and nameplate alignment mathematically. If you designed the SVG, you know exactly what it produces — describe it plainly and honestly. See `references/svg-geometric-verification.md` for the complete verification protocol. If the review must be truly visual (color bleed, anti-aliasing artifacts, rendering errors not visible in source), delegate to an agent with confirmed working vision (Hermes on nuc-1). Never say "the icon looks good" — say "the SVG geometry is verified correct" and describe what it produces.
- **cairosvg may fail on pyenv Python 3.12+.** The `cffi` import causes `ModuleNotFoundError`. `brew install librsvg` + `rsvg-convert` is the reliable path. Do not spend time debugging cairosvg.
- **HTML `<object>` tags won't render SVGs when viewed via `file://`** on some browsers due to same-origin policy. Use `python3 -m http.server <port>` to serve the gallery, or just reference the PNGs.
- **Dark backgrounds strongly preferred** for CLI agents. The icon should look good on Discord dark mode, terminal black, and vault dark themes.
- **Circular crop test.** Discord avatars are circular. If the primary motif is near the top (e.g., an eye at y=180), it stays visible. If the entire composition stretches edge-to-edge, the edges get cropped. Center the main subject.
- **Agents with no vision can still proxy.** They write SVG by hand, build the gallery, render PNGs, and coordinate review. The execution is identical — only the visual QA step must be delegated.
- **Nameplate at 65% opacity** prevents it from competing with the motif. Keep it legible but secondary.
- **Don't use images you can't verify.** If you created an icon, you know what it looks like because you designed every SVG coordinate. State exactly what you built. Never say "the icon looks good" if you can't see it — describe what you designed.
- **Late votes are not do-overs.** If you made an executive decision (v1.0) before votes arrived, a late-arriving vote becomes v1.1 refinements — not a restart of the pipeline. This respects both the agent who made the call (keeping their work) and the late-voter (honoring their input). See "Asynchronous Voting & Late-Vote Handling" in Phase 5.

- **Interpret "prominence" / "slightly brighter" conservatively — start from identical geometry.** When an agent requests that one element be "more prominent" or "slightly brighter", translate that as **glow/opacity/stroke only** — never as geometric enlargement, added ornamentation, or new visual layers. The actual learning from a v2-over-correction (Loom v1.1 → v2.1): begin with all elements at identical size/layout, then layer glow differentiation (stdDev, blur count, stroke width delta of 0.5-1px). If the agent wants more after seeing the first iteration, it's cheaper to increment glow than to undo geometric changes. A "slightly brighter" request that was meant as +2px stroke and a second blur merge gets misinterpreted as +11% size increase + corona rings + orbital ellipses + heartbeat animation — the gap between the two interpretations is wide, and the second requires a full rollback. **Rule of thumb:** If the design is at v1.0 and the agent says "make X slightly stronger," the answer is a glow adjustment, not a layout change. If you're unsure which direction to go, go smaller — you can always amplify.

## Related Files

| File | Location | Purpose |
|------|----------|---------|
| `references/rendering.md` | This skill's `references/` | SVG→PNG rendering commands and pitfalls |
| `references/loom-icon-case-study.md` | This skill's `references/` | End-to-end case study: Loom icon pipeline v1.0 |
| `references/icon-refinement-techniques.md` | This skill's `references/` | SVG refinement patterns: link swaps, proportions, particle systems, versioning |
| `references/svg-geometric-verification.md` | This skill's `references/` | Code-based visual review protocol: coordinate math, hex vertex validation, link endpoint checks, particle distribution analysis |
| `templates/icon-sketch.svg` | This skill's `templates/` | Starter SVG template for fresh icon sketches |
| `templates/gallery.html` | This skill's `templates/` | Reusable HTML gallery template with mustache-style placeholders |
| `inter-agent-vault-coordination` | Autonomous Skills | How to coordinate icon selection across agents |
