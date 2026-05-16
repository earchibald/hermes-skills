# Wall of Information — CSS Toolkit for Interactive Reports

Complete CSS for dark-themed interactive report pages. Paste into `<style>` blocks.

## Base Theme

```css
:root {
  --bg: #0d1117;
  --surface: #161b22;
  --surface2: #21262d;
  --border: #30363d;
  --accent: #58a6ff;
  --accent2: #bc8cff;
  --green: #3fb950;
  --yellow: #d29922;
  --red: #f85149;
  --text: #e6edf3;
  --text2: #8b949e;
  --text3: #6e7681;
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  background: var(--bg);
  color: var(--text);
  font-family: system-ui, -apple-system, 'Segoe UI', sans-serif;
  line-height: 1.6;
}
.container { max-width: 960px; margin: 0 auto; padding: 0 1.5rem; }
```

## Header

```css
header {
  background: linear-gradient(135deg, #0d1117 0%, #1a1a2e 100%);
  border-bottom: 1px solid var(--border);
  padding: 2.5rem 0 2rem;
}
header h1 { font-size: 1.8rem; font-weight: 600; letter-spacing: -0.02em; }
header .subtitle { color: var(--text2); font-size: 0.95rem; margin-top: 0.3rem; }
header .meta {
  display: flex; gap: 1rem; margin-top: 0.75rem;
  font-size: 0.8rem; color: var(--text3);
}
```

## Navigation Bar (multi-page)

```css
header .nav { display: flex; gap: 0.5rem; align-items: center; font-size: 0.85rem; }
header .nav a { color: var(--text2); text-decoration: none; padding: 0.3rem 0.6rem; border-radius: 4px; }
header .nav a:hover { color: var(--accent); background: var(--surface2); }
header .nav a.active { color: var(--accent); background: rgba(88,166,255,0.1); }
header .nav .sep { color: var(--text3); }
```

## Section Headers

```css
section { padding: 2rem 0; border-bottom: 1px solid var(--border); }
h2 {
  font-size: 1.3rem; font-weight: 600; margin-bottom: 1rem;
  display: flex; align-items: center; gap: 0.5rem;
}
h2 .badge {
  font-size: 0.65rem; font-weight: 500;
  padding: 0.15rem 0.5rem; border-radius: 4px;
  background: var(--surface2); color: var(--text2);
}
```

## Card Grid

```css
.card-grid {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1rem; margin-bottom: 1.5rem;
}
.card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 8px; padding: 1.25rem;
}
/* Only add transition + hover for clickable cards (selectable grids, option cards).
   For display-only cards use .info-card or .tier-card (see sections below).
   Golden rule: if it doesn't respond to click, no hover effect. */
.card.clickable { cursor: pointer; transition: border-color 0.15s; }
.card.clickable:hover { border-color: var(--accent); }
.card h3 { font-size: 1rem; font-weight: 600; margin-bottom: 0.5rem; }
.card .stat { font-size: 1.5rem; font-weight: 700; }
.card .stat.green { color: var(--green); }
.card .stat.yellow { color: var(--yellow); }
.card .stat.accent { color: var(--accent); }
.card .desc { font-size: 0.85rem; color: var(--text2); margin-top: 0.3rem; }
.card .tags { display: flex; flex-wrap: wrap; gap: 0.4rem; margin-top: 0.75rem; }
```

## Tags

```css
.tag {
  font-size: 0.7rem; padding: 0.15rem 0.5rem; border-radius: 3px;
  background: var(--surface2); color: var(--text2); border: 1px solid var(--border);
}
.tag.green { border-color: var(--green); color: var(--green); }
.tag.yellow { border-color: var(--yellow); color: var(--yellow); }
.tag.red { border-color: var(--red); color: var(--red); }
```

## Comparison Table

```css
.comparison { width: 100%; border-collapse: collapse; margin: 1rem 0; font-size: 0.85rem; }
.comparison th, .comparison td {
  padding: 0.65rem 0.75rem; text-align: left;
  border-bottom: 1px solid var(--border);
}
.comparison th {
  background: var(--surface); font-weight: 600;
  color: var(--text2); position: sticky; top: 0;
}
.comparison tr:hover td { background: var(--surface); }
.comparison .check { color: var(--green); }
.comparison .cross { color: var(--red); }
.comparison .mid { color: var(--yellow); }
```

## Architecture / Topology Diagram

```css
.diagram {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 8px; padding: 1.5rem; margin: 1rem 0;
  font-family: 'SF Mono', 'Cascadia Code', monospace;
  font-size: 0.75rem; line-height: 1.5; white-space: pre;
  overflow-x: auto; color: var(--text2);
}
.diagram .node { color: var(--accent); font-weight: 600; }
.diagram .conn { color: var(--text3); }
.diagram .label { color: var(--text2); }
```

## Decision Block

```css
.decision-block {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 8px; padding: 1.5rem; margin: 1.5rem 0;
}
.decision-block h3 { font-size: 1.1rem; margin-bottom: 0.75rem; }
```

Highlighted version (for primary decision section):
```css
.decision-block.highlighted {
  border-color: var(--accent);
}
.decision-block.highlighted h3 { color: var(--accent); }
```

## Radio Groups

```css
.radio-group { display: flex; flex-direction: column; gap: 0.6rem; margin: 1rem 0; }
.radio-option {
  display: flex; align-items: flex-start; gap: 0.75rem;
  padding: 0.75rem 1rem; border: 1px solid var(--border);
  border-radius: 6px; background: var(--surface); cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
}
.radio-option:hover { border-color: var(--accent); background: var(--surface2); }
.radio-option.selected {
  border-color: var(--accent);
  background: rgba(88, 166, 255, 0.08);
}
.radio-option input[type="radio"] { margin-top: 0.15rem; accent-color: var(--accent); flex-shrink: 0; }
.radio-option .label { font-weight: 500; }
.radio-option .desc { font-size: 0.8rem; color: var(--text2); margin-top: 0.15rem; }
```

## Textarea / Select

```css
textarea {
  width: 100%; min-height: 80px;
  padding: 0.75rem; background: var(--surface);
  border: 1px solid var(--border); border-radius: 6px;
  color: var(--text); font-family: inherit; font-size: 0.9rem;
  resize: vertical; margin: 0.5rem 0;
}
textarea:focus { outline: none; border-color: var(--accent); }

select {
  width: 100%; padding: 0.6rem 0.75rem;
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 6px; color: var(--text); font-size: 0.9rem; cursor: pointer;
}
select:focus { outline: none; border-color: var(--accent); }
```

## Buttons

```css
button {
  padding: 0.7rem 1.5rem; border: none; border-radius: 6px;
  font-size: 0.95rem; font-weight: 600; cursor: pointer;
  transition: opacity 0.15s, transform 0.1s;
}
button:active { transform: scale(0.97); }
.btn-primary { background: var(--accent); color: #fff; }
.btn-primary:hover { opacity: 0.9; }
.btn-secondary {
  background: var(--surface2); color: var(--text);
  border: 1px solid var(--border);
}
.btn-secondary:hover { background: var(--border); }
button:disabled { opacity: 0.5; cursor: not-allowed; }
```

## Sticky Submit Bar

```css
.submit-bar {
  position: sticky; bottom: 0;
  background: linear-gradient(180deg, transparent 0%, var(--bg) 30%);
  padding: 1.5rem 0 1rem;
  display: flex; gap: 1rem; align-items: center;
}
```

## Status Message

```css
.status-msg { padding: 0.5rem 1rem; border-radius: 4px; font-size: 0.85rem; display: none; }
.status-msg.sent {
  display: block; background: rgba(63,185,80,0.15);
  color: var(--green); border: 1px solid rgba(63,185,80,0.3);
}
.status-msg.error {
  display: block; background: rgba(248,81,73,0.15);
  color: var(--red); border: 1px solid rgba(248,81,73,0.3);
}
```

## Code Block

```css
.code-block {
  background: #0d1117; border: 1px solid var(--border);
  border-radius: 4px; padding: 0.5rem 0.75rem; margin-top: 0.5rem;
  font-family: 'SF Mono', 'Cascadia Code', monospace;
  font-size: 0.75rem; line-height: 1.5;
  white-space: pre; overflow-x: auto;
}
```

## Dimension Cards (3-column metrics)

```css
.dim-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.7rem; margin: 1rem 0; }
.dim-card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 6px; padding: 0.75rem;
}
.dim-card .label { font-size: 0.75rem; color: var(--text2); }
.dim-card .value { font-size: 1rem; font-weight: 600; margin-top: 0.2rem; }
.dim-card .note { font-size: 0.7rem; color: var(--text3); margin-top: 0.2rem; }
```

## Information & Tier Cards (display only — no hover)

```css
.info-card, .tier-card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 8px; padding: 1rem;
  cursor: default; transition: none;
}
.tier-card:hover { border-color: var(--border); }  /* no visual change on hover */
.info-card .icon { font-size: 1.3rem; }
.info-card .title { font-weight: 600; font-size: 1rem; }
.info-card .desc { font-size: 0.85rem; color: var(--text2); }
```

## Target Cards (per-machine weight)

```css
.target-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin: 1rem 0; }
.target-card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 8px; padding: 1rem; text-align: center;
}
.target-card h4 { font-size: 0.9rem; margin-bottom: 0.3rem; }
.target-card .weight { font-size: 1.2rem; font-weight: 700; margin: 0.4rem 0; }
.target-card .verdict {
  font-size: 0.75rem; padding: 0.2rem 0.5rem;
  border-radius: 3px; display: inline-block;
}
.verdict.trivial { background: rgba(63,185,80,0.15); color: var(--green); }
.verdict.fine { background: rgba(88,166,255,0.15); color: var(--accent); }
.verdict.tight { background: rgba(210,153,34,0.15); color: var(--yellow); }
```

## Steps (deployment plan)

```css
.steps { display: flex; flex-direction: column; gap: 0.7rem; }
.step {
  display: flex; gap: 1rem;
  padding: 0.75rem 1rem; background: var(--surface);
  border: 1px solid var(--border); border-radius: 8px;
  cursor: default; /* NOT interactive — display only */
  transition: none;  /* No hover effect — display only */
}
.step:hover { border-color: var(--border); }  /* Keep original border on hover */
.step .num {
  width: 28px; height: 28px; border-radius: 50%;
  background: var(--surface2);
  display: flex; align-items: center; justify-content: center;
  font-size: 0.8rem; font-weight: 600; flex-shrink: 0; margin-top: 0.15rem;
}
.step.done .num { background: var(--green); color: #000; }
.step.active .num { background: var(--accent); color: #000; }
.step .body .title { font-weight: 500; }
.step .body .desc { font-size: 0.8rem; color: var(--text2); margin-top: 0.15rem; }
```

## Checklist

```css
.checklist { list-style: none; padding: 0; }
.checklist li {
  padding: 0.4rem 0; padding-left: 1.5rem;
  position: relative; font-size: 0.9rem;
}
.checklist li::before { content: "□"; position: absolute; left: 0; color: var(--text3); }
.checklist li.done::before { content: "☑"; color: var(--green); }
```

## Two-column layout

```css
.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin: 1rem 0; }
```

## Responsive

```css
@media (max-width: 640px) {
  .target-grid, .dim-grid { grid-template-columns: 1fr; }
  .card-grid { grid-template-columns: 1fr; }
  header h1 { font-size: 1.4rem; }
  .comparison { font-size: 0.75rem; }
  .comparison th, .comparison td { padding: 0.4rem 0.5rem; }
  .two-col { grid-template-columns: 1fr; }
}
```

## Confirmation page (inline in server)

```html
<style>
body{font-family:system-ui,-apple-system,sans-serif;max-width:600px;margin:3rem auto;padding:0 1rem;text-align:center;background:#0d1117;color:#e6edf3}
.card{padding:2rem;border-radius:12px;background:#161b22;border:1px solid #30363d}
h1{color:#3fb950;font-size:1.5rem}
p{color:#8b949e;margin:0.75rem 0}
.btn{display:inline-block;margin-top:1rem;padding:0.6rem 1.25rem;background:#21262d;color:#e6edf3;text-decoration:none;border-radius:6px;border:1px solid #30363d;font-size:0.9rem}
.btn:hover{background:#30363d}
small{display:block;margin-top:1.5rem;color:#6e7681;font-size:0.8rem}
</style>
```
