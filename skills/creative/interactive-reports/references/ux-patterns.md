# UX Patterns for Interactive Report Pages

## Golden Rule: Only Interactive Elements Get Hover States

This was explicitly called out by the user as a problem. **Elements that look clickable but aren't cause confusion and frustration.**

### What counts as interactive (add hover/pointer):
- Radio options (`<label class="radio-option">`)
- Checkbox options (`<label class="checkbox-option">`)
- Buttons (`<button>` or `<a>`)
- Nav links
- Tree/decision nodes (if clicking advances state)
- Tab switchers
- Dropdown selects

### What does NOT get hover/pointer:
- Information cards that only display data
- Architecture diagram blocks (unless they expand/collapse)
- Metric/dimension displays (`dim-card`, `target-card`)
- Step-numbered deployment plans (`step` class — display only)
- Tier/info cards (`tier-card`, `info-card`)
- Pure text sections
- Any element where `click` does nothing

### CSS implementation:

```css
/* Interactive elements — get hover state + pointer */
.radio-option { cursor: pointer; transition: border-color 0.12s; }
.radio-option:hover { border-color: var(--accent); }

/* Non-interactive information cards — NO hover effects */
.tier-card, .info-card, .dim-card, .target-card {
  cursor: default;
  transition: none;
}
```

## Submit Button Placement

Always use a **sticky submit bar** at the bottom of the page. As the user scrolls through a long wall of information, the submit button stays visible. Implementation:

```css
.submit-bar {
  position: sticky;
  bottom: 0;
  background: linear-gradient(180deg, transparent 0%, var(--bg) 30%);
  padding: 1.5rem 0 1rem;
  display: flex;
  gap: 1rem;
  align-items: center;
}
```

## Confirmation After Submit

After a successful form submission, redirect to `/submitted` without waiting. This:
- Prevents accidental double-submissions
- Shows the user their input was received
- Provides nav links to explore other pages
- Closes the feedback loop visually

## Form Design Patterns

### Single-tier decision: One radio group
Group all related options under a shared `name` attribute. The first option should be checked by default (the agent's recommendation).

### Multi-tier decision: Multiple radio groups
Each decision dimension gets its own radio group with a shared prefix or ID. Collect all values in the submit handler.

### Open-ended input: Textareas always
Every decision page should include at least one textarea for comments, questions, or corrections. Not everything fits in radio buttons.

### Pre-flight checklists
Use a simple list with checkboxes or visual `☐`/`☑` markers for multi-step verification lists. Pre-fill known-done items with `class="done"`.

## Color Semantics

| Color | Meaning | Used for |
|-------|---------|----------|
| Green `#3fb950` | Good, OK, available | Sufficient capacity, resolved items, check marks |
| Yellow `#d29922` | Warning, tight, limited | Near-limits, borderline, caution |
| Red `#f85149` | Bad, blocked, insufficient | Below threshold, prevented, failures |
| Blue `#58a6ff` | Primary, recommended | Agent's recommendation, active state |
| Purple `#bc8cff` | Secondary, alternative | Non-primary options, highlights |

## Page Structure Template

```
┌─────────────────────────────────────────────┐
│  HEADER                                      │
│  Title + subtitle + metadata line            │
│  Nav bar: [Decision] · [Wireframe] · [Live]  │
├─────────────────────────────────────────────┤
│                                              │
│  SECTION 1: Context / Overview               │
│  Architecture diagram or topology            │
│                                              │
│  SECTION 2: Comparison / Options             │
│  Card grid or comparison table               │
│                                              │
│  SECTION 3: Weight / Impact per target       │
│  Per-machine cards with color-coded verdicts │
│                                              │
│  SECTION 4: Decision blocks                  │
│  Radio groups with clear labels + descs      │
│                                              │
│  SECTION 5: Open questions / notes           │
│  Yellow- bordered question block              │
│                                              │
│  SECTION 6: Overall direction                 │
│  Final submit bar (sticky)                    │
├═════════════════════════════════════════════┤
│  STICKY SUBMIT BAR                           │
│  [Submit] [Reset] [Status message]           │
└─────────────────────────────────────────────┘
```

## Mistakes to Avoid

1. **Hover on everything** — The user will click things that do nothing and get frustrated. Be surgical about what gets interactive styling.

2. **Too many pages** — Two pages max for a single session. Three+ and the user loses context.

3. **No default selections** — Always set `checked` or `selected` on one option per group so the submit handler has a value even if the user just hits submit.

4. **No way back** — After submission, provide nav links to return to the decision pages. The `/submitted` page should link back.

5. **Forgetting CORS** — The server needs `Access-Control-Allow-Origin: *` on POST responses, or the browser will reject the fetch.

6. **Asking for decisions you haven't provided enough context for** — The "wall of information" comes before the "make a choice." If the user isn't ready to decide, the form is wasted.
