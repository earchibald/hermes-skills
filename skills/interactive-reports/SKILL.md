---
name: interactive-reports
description: >-
  Self-terminating interactive report server with dual-channel browser+chat
  interaction — build HTML pages with forms, serve from a local HTTP server
  that auto-scans ports and self-terminates on submission. Output arrives in
  chat via notify_on_complete. Trigger phrases: "let's work with a web server",
  "let's go web", "report server", "dual-channel reporting", "interactive report".
version: 2.0.0
author: Argus
license: MIT
platforms: [macos, linux]
metadata:
  hermes:
    tags: [reports, interactive, html, forms, decision, ui, browser, dual-channel]
    related_skills: [sketch, wireframe-prototyping, claude-design]
---

# Interactive Reports

## TL;DR — How to Use

```
1. plan WHAT decision + what info wall supports it
2. write /tmp/<NS>_page.html  (single file, dark theme, forms, submit → /submit)
3. copy templates/mini-server.py → /tmp/<NS>_server.py, edit PAGES dict
4. terminal(background=true, notify_on_complete=true,
            command="python3 /tmp/<NS>_server.py")
5. read NS + PORT from stdout: ir_ready ns=ir_argus_<ts> port=8899
6. terminal("open http://localhost:{PORT}/")
7. user submits form → server saves JSON, prints it to stdout, exits
8. notify_on_complete fires → read JSON output, continue in chat
```

**Critical rules:**
- Only actual form elements get hover/pointer. Cards, diagrams, steps, tier info = `cursor: default`, no hover. Users will click anything that highlights.
- Server NEVER auto-opens browser. Agent controls `open` explicitly. Remove `webbrowser` from server.
- Namespace ALL artifacts: response file, HTML page, server script, port. Use NS = `ir_{AGENT}_{SESSION}`. All artifacts go under `/tmp/{NS}_*`.
- Scan ports 8899-8920 for the first free port. Never hardcode a single port.
- The self-terminating server (templates/mini-server.py) is the recommended pattern for single-submit pages.

## Self-Terminating Server Pattern (Primary Method)

For one-shot pages (decisions, polls, confirmations), use a self-terminating
server. On first form submission it saves the response, prints JSON to stdout,
and shuts down. Start with `terminal(background=true, notify_on_complete=true)`.
When the server exits, `notify_on_complete` fires with the JSON on stdout.

```python
# In do_POST, after saving the response:
threading.Thread(target=self.server.shutdown, daemon=True).start()
```

**Why this pattern:** No gateway dependency. Response arrives in current chat
via `notify_on_complete`. Ephemeral. No polling. Works offline.
**Trade-off:** One submission per server run. For multi-step workflows, restart
the server.

### How it works

1. The mini-server (`templates/mini-server.py`) is a **generic template** that
   ships with the skill. It is NOT rewritten per session — the agent copies it
   to `/tmp/{NS}_server.py` and edits the `PAGES` dict.
2. On startup, it auto-computes its namespace (NS) from `HERMES_AGENT_NAME`
   and `HERMES_SESSION_ID` (or a timestamp), scans ports 8899-8920 for the
   first free one, and emits a machine-parseable startup signal on stdout:
   ```
   ir_ready ns=ir_argus_1712345678 port=8899
   ```
3. The agent reads NS and PORT from this line, then opens the browser.
4. When the user submits the form (POST /submit), the server:
   - Saves structured JSON to `/tmp/{NS}_response.json`
   - Prints the JSON to stdout (captured by `notify_on_complete`)
   - Responds to the browser with `{"ok": true, "redirect": "/submitted"}`
   - Self-terminates via `threading.Thread(target=server.shutdown).start()`
5. `notify_on_complete` fires the JSON back to the agent's conversation.

## Multi-Agent Namespacing

Multiple Hermes agents can run interactive reports simultaneously. Every
artifact must be scoped to prevent collisions. Derive AGENT from
`HERMES_AGENT_NAME` env var (default: "argus"). Derive SESSION from
`HERMES_SESSION_ID` or `str(int(time.time()))` truncated to 12 chars.
Namespace: `ir_{AGENT}_{SESSION}`.

| Artifact | Pattern |
|---|---|
| HTML page | `/tmp/{NS}_page.html` |
| Response file | `/tmp/{NS}_response.json` |
| Server script | `/tmp/{NS}_server.py` (copy of template) |
| Port | First free in 8899-8920 (auto-scanned at startup) |

**Port scanning** — scan 8899-8920 at startup to find a free port:
```python
import socket
for try_port in range(8899, 8921):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1)
    try:
        if s.connect_ex(("127.0.0.1", try_port)) != 0:
            PORT = try_port; s.close(); break
    finally:
        s.close()
```
Print the chosen port to stdout so the agent reads it from process output.

**Startup signal format:**
```
ir_ready ns={NS} port={PORT}
```

The agent reads NS and PORT from this line to construct file paths and
the browser URL.

## Use Cases

Use this when:
- You have a **wall of information** to present (comparisons, architectures,
  options, trade-offs) that would overload the chat channel
- The user needs to **make a decision** with multiple interdependent choices
- The user wants to **see visual layouts, diagrams, or wireframes** before
  committing
- The user explicitly asks for HTML, browser, or dual-channel interaction
- The user says "let's work with a web server", "let's go web", "report server",
  "dual-channel reporting", or "interactive report"
- You want to present **live session status** (metrics, decisions, page views)
  in an auto-polling browser page

Do NOT use this for:
- Quick answers or single-option responses (chat is faster)
- Design exploration (use `sketch` for variant comparison)
- One-off visual artifacts (use `claude-design`)
- Wireframes/mockups (use `wireframe-prototyping`)

## Method

```
plan the report  →  build HTML file(s)  →  start Python server  →  open browser  →  wait for submission  →  read response  →  continue in chat
```

### 1. Plan the report structure

Before writing HTML, decide:

1. **What decision is being made?** What choices does the user need to pick from?
2. **What information wall supports it?** Comparisons, weight estimates, architecture diagrams, trade-off matrices.
3. **What form elements are needed?** Radio groups (mutually exclusive choices), checkboxes (multi-select), selects (dropdown options), textareas (free-form comments), submit button.
4. **How many pages?** One comprehensive page, or split into linked pages (e.g., decision page → deployment wireframe).

### 2. Build the HTML file

Write to `/tmp/<NS>_page.html`. Single-file HTML with everything inline:

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Your Title</title>
<style>
  /* Dark theme by default. CSS variables for tokens. */
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
  body {
    background: var(--bg); color: var(--text);
    font-family: system-ui, -apple-system, 'Segoe UI', sans-serif;
    line-height: 1.6;
    max-width: 960px; margin: 0 auto; padding: 0 1.5rem;
  }
  /* Cards, tables, form elements, code blocks — see references/wall-of-information.css */
</style>
</head>
<body>
  <!-- Sections of information: cards, comparison tables, diagrams, dimensions -->
  <!-- Decision blocks with radio groups, selects, textareas -->
  <!-- Sticky submit bar at bottom -->
  <script>
    // Form submission via fetch to /submit
    // Radio group selection handlers
    // Status message display
  </script>
</body>
</html>
```

**Design principles for the information wall:**
- **Dark theme** matching the terminal/agent aesthetic (GitHub-dark inspired)
- **Card grid** for overview items (3-column, auto-fit responsive)
- **Comparison table** for provider/option comparisons (sticky header, color-coded cells)
- **Architecture diagram** — monospace ASCII art or CSS-based visual topology
- **Decision blocks** with colored borders (accent blue for primary choices)
- **Dimension cards** for 3-6 key metrics with color-coded values
- **Tags** for categorical metadata (colored borders: green/ok, yellow/warn, red/bad)
- **Checklist** with checked/unchecked items and strikethrough prefilled items
- **Sticky submit bar** at bottom that appears on scroll
- **Code blocks** with dark background and monospace font for exec-ready commands
- **Navigation bar** between pages at the top when serving multiple pages

**Form element patterns:**

```html
<!-- Radio group (mutually exclusive) -->
<div class="radio-group" id="choice-id">
  <label class="radio-option" onclick="selectRadio(this)">
    <input type="radio" name="group_name" value="option-a" checked>
    <div>
      <div class="label">Option A Label</div>
      <div class="desc">One-line description of this option</div>
    </div>
  </label>
  <!-- Repeat for each option -->
</div>

<!-- Select dropdown -->
<select id="select-id">
  <option value="a">Option A</option>
  <option value="b" selected>Option B (default)</option>
</select>

<!-- Multi-line comments -->
<textarea id="comments" placeholder="Free-form text..." rows="4"></textarea>

<!-- Multi-tier form: multiple independent radio groups -->
<div class="decision-block">
  <h3>Tier 1: Homelab Memory Strategy</h3>
  <div class="radio-group">
    <label class="radio-option" onclick="selectRadio(this)">
      <input type="radio" name="tier1" value="hindsight-docker" checked>
      <div>
        <div class="label">Hindsight in Docker</div>
        <div class="desc">Docker container with PostgreSQL volume</div>
      </div>
    </label>
    <label class="radio-option" onclick="selectRadio(this)">
      <input type="radio" name="tier1" value="none">
      <div>
        <div class="label">Skip memory provider</div>
        <div class="desc">Stick with pure chat interaction only</div>
      </div>
    </label>
  </div>
</div>

<div class="decision-block">
  <h3>Tier 2: Argus (Standalone, Travels)</h3>
  <div class="radio-group">
    <label class="radio-option" onclick="selectRadio(this)">
      <input type="radio" name="tier2" value="local-embedded" checked>
      <div>
        <div class="label">Hindsight local-embedded</div>
        <div class="desc">Self-contained daemon, works offline</div>
      </div>
    </label>
  </div>
</div>

<!-- Then collect all in submit handler: -->
<script>
function submitForm() {
  const data = {
    page: 'multi-tier-decision',
    tier1: document.querySelector('input[name="tier1"]:checked')?.value,
    tier2: document.querySelector('input[name="tier2"]:checked')?.value,
    comments: document.getElementById('comments').value
  };
  fetch('/submit', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data) })
    .then(r => r.json())
    .then(resp => { if (resp.ok) window.location.href = '/submitted'; });
}
</script>
```

**Submit JS pattern:**

```javascript
function submitForm() {
  const data = {
    page: 'page-name',
    timestamp: new Date().toISOString(),
    field_name: document.querySelector('input[name="x"]:checked')?.value,
    comments: document.getElementById('comments').value,
    // ... collect all form fields
  };
  fetch('/submit', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  }).then(r => r.json()).then(resp => {
    if (resp.ok) window.location.href = '/submitted';
  });
}
```

**Radio group handler:**
```javascript
function selectRadio(el) {
  el.querySelector('input[type="radio"]').checked = true;
  el.parentElement.querySelectorAll('.radio-option')
    .forEach(o => o.classList.remove('selected'));
  el.classList.add('selected');
}
// Init on load:
document.querySelectorAll('.radio-option input:checked')
  .forEach(r => r.closest('.radio-option').classList.add('selected'));
```

### 3. Copy and configure the server

Use Python's built-in `http.server` with the self-terminating template.
The template ships as `templates/mini-server.py` — a generic server that is
**not rewritten per session**. The agent copies it to a namespaced path.

```bash
cp templates/mini-server.py /tmp/<NS>_server.py
```

Then edit the `PAGES` dict in `/tmp/<NS>_server.py` to point to your HTML
file(s). The default uses the namespace: `"/" : "/tmp/{NS}_page.html"`.

The server automatically:
- Computes NS from `HERMES_AGENT_NAME` and `HERMES_SESSION_ID`
- Scans ports 8899-8920 for a free port
- Emits `ir_ready ns={NS} port={PORT}` on stdout
- Serves files from the PAGES dict
- Saves form submissions to `/tmp/{NS}_response.json`
- Prints submission JSON to stdout and self-terminates

**Example PAGES configuration for multi-page reports:**
```python
PAGES = {
    "/": "/tmp/ir_argus_abc123_page.html",
    "/wireframe": "/tmp/ir_argus_abc123_wireframe.html",
    "/session": "/tmp/ir_argus_abc123_session.html",
}
```

### 4. Track session metrics (optional)

For live dashboards that auto-poll, add metrics tracking to the server:

```python
pvs = 0        # page view counter
form_count = 0 # form submission counter
chat_turns = 0 # update via curl or chat callback
last_agent_msg = "Session started."

# In do_GET, increment the page counter
# In do_POST /submit, increment form_count

# Add a /session-status endpoint in do_GET:
if path == "/session-status":
    elapsed = int(time.time() - SESSION_START)
    status = {
        "pages_served": pvs,
        "form_responses": form_count,
        "chat_turns": chat_turns,
        "elapsed": f"{elapsed//60}m{elapsed%60}s",
        "last_agent_message": last_agent_msg,
        "active_decision": "decide-provider",
        "uptime_seconds": elapsed,
    }
    self._serve_json(status)
```

Then build a **live session page** (`/session`) that auto-polls `/session-status`:

```html
<script>
function pollStatus() {
  fetch('/session-status')
    .then(r => r.json())
    .then(d => {
      document.getElementById('pages').textContent = d.pages_served;
      document.getElementById('responses').textContent = d.form_responses;
      document.getElementById('turns').textContent = d.chat_turns;
      document.getElementById('elapsed').textContent = d.elapsed;
    });
}
setInterval(pollStatus, 2000);
pollStatus();
</script>
```

You can update `chat_turns` and `last_agent_msg` from the agent side:

```bash
curl -s -X POST -d '{"chat_turns":5,"last_agent_msg":"working on X"}' http://localhost:8899/update-status
```

Or expose a PUT/POST `/update-status` endpoint on the server.

### 5. Start the server and open the browser

**For single-submit (self-terminating pattern — recommended):**

Start the self-terminating server (from `templates/mini-server.py`) with
`notify_on_complete=True`. The server auto-scans ports 8899-8920, prints
the chosen port to stdout on startup:

```python
terminal(background=True, notify_on_complete=True,
         command="python3 /tmp/<NS>_server.py")

# Read PORT from stdout line: ir_ready ns=... port=...
# Then open browser
terminal("open http://localhost:{PORT}/")
```

On form submit: saves JSON, prints to stdout, exits.
`notify_on_complete` fires with the JSON. Read it and continue.

**For multi-page / persistent server (non-terminating):**

For workflows needing multiple submissions, use a persistent pattern:

```python
# Kill any old server on the port first
terminal(background=True, command="python3 /tmp/<NS>_server.py")
terminal("sleep 1 && curl -so /dev/null -w '%{http_code}' http://localhost:{PORT}/")
terminal("open http://localhost:{PORT}/")
```

For the persistent pattern, modify the server's do_POST to NOT call
`self.server.shutdown()` — keep it alive for repeated submissions.
Read responses from the file instead of stdout.

### 6. Wait for submission and read the response

After telling the user the page is up, wait for them to interact.

**Self-terminating path:** `notify_on_complete` fires automatically with
the submission JSON on stdout. Read and process it.

**Persistent server path:** Check for submission periodically:

```bash
cat /tmp/<NS>_response.json 2>/dev/null || echo "NO_RESPONSE_YET"
```

When a response appears, read it and continue the session based on the user's
choices. Clear the response file after processing to accept fresh submissions.

**Agent-side pattern when the user says "Continue" or doesn't engage:**
If the user says "Continue toward the goal" or similar without submitting the
form, check the response file first. If empty, the user is pushing the
experiment forward — advance the capability (add pages, fix UX, fill data
gaps). Do not ask them to submit the form again or explain the page again.

**Multi-session isolation:** All artifacts live at `/tmp/{NS}_*` and are
machine-local. If the server was started in a prior session, its namespacing
prevents collisions. Kill and restart the server for a fresh session. Always
delete the old response file before starting a new session.

### 7. Server lifecycle

```python
# Kill existing server
process(action="kill", session_id="proc_xxx")

# Clear old response
terminal("rm -f /tmp/<NS>_response.json")

# Restart
terminal(background=True, notify_on_complete=True,
         command="python3 /tmp/<NS>_server.py")
```

## Confirmation page

After a successful form submission, redirect to `/submitted`. Show a simple
confirmation card with:
- "✓ Response Sent" header (green)
- Text confirming delivery to the agent
- Option to submit again (by reloading the page)

## File locations

| Item | Path |
|---|---|
| HTML reports | `/tmp/{NS}_page.html` (single page) or `/tmp/{NS}_<name>.html` (multi-page) |
| Self-terminating server | `templates/mini-server.py` (copy to `/tmp/{NS}_server.py`) |
| Response file | `/tmp/{NS}_response.json` |

Where NS = `ir_{AGENT}_{SESSION}`. All under `/tmp/` — disposable.

## Port conventions

- **8899-8920**: Interactive report server (auto-scanned, first free wins)
- **8090**: Wireframe prototyping (see `wireframe-prototyping` skill)
- **8910**: Metis dashboard / Dolos server

Use port scanning at startup — never hardcode a single port.

## References

- `references/wall-of-information-css.md` — Complete CSS toolkit for dark-themed interactive reports: cards, comparison tables, diagram blocks, radio groups, form elements, sticky submit bar, confirmation page, responsive breakpoints.
- `references/ux-patterns.md` — UX patterns, interactive-vs-static rules, form design, color semantics
- `references/hardware-verification-before-rendering.md` — Before building a report that depends on machine specs, SSH into hosts for real data. Commands, examples, pitfalls.
- `references/server-pattern.py` — Full copy-paste-ready self-terminating server example with namespacing, port scanning, CORS, and metrics tracking.
- `templates/mini-server.py` — Generic self-terminating server template. Ships with the skill, not rewritten per session. Auto-computes NS, scans ports, emits `ir_ready`, self-terminates on first submit.

## Live Status Polling (Session Dashboard)

For pages that track session state, add a `/session-status` JSON endpoint to
the server and have the page poll it every 2 seconds:

**Server-side** — add a module-level stats tracker:
```python
pvs = 0        # page view counter
form_count = 0  # form submission counter
chat_turns = 0  # conversational turns (manually update from agent)
last_agent_msg = "Session started."
SESSION_START = time.time()
```

Serve as JSON at `/session-status`:
```python
elif path == "/session-status":
    elapsed = int(time.time() - SESSION_START)
    status = {
        "pages_served": pvs,
        "form_responses": form_count,
        "chat_turns": chat_turns,
        "elapsed": f"{elapsed}s",
        "last_agent_message": last_agent_msg,
        "active_decision": "current-decision-node-id",
    }
    self._serve_json(status)
```

**Client-side** — poll from the page:
```javascript
async function pollStatus() {
  const resp = await fetch('/session-status');
  const data = await resp.json();
  // Update DOM elements with data.pages_served, data.form_responses, etc.
  // Optionally add new chat messages if last_agent_message changed
}
setInterval(pollStatus, 2000);
```

## Quick-Action Buttons

For decision pages, include pre-configured action buttons that submit common
intents with a single click. Place them between the decision tree and the
freeform textarea:

```html
<div class="action-btn" onclick="quickSubmit('Go ahead and execute the plan')">🚀 Execute</div>
<div class="action-btn" onclick="quickSubmit('I need a different approach')">🔄 Rethink</div>
<div class="action-btn" onclick="quickSubmit('Show me the comparison again')">📊 Compare</div>
```

Where `quickSubmit` sends a named message to the agent:
```javascript
function quickSubmit(msg) {
  fetch('/submit', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({page:'session', source:'quick-action', message: msg})
  });
}
```

## Decision Tree Display

A live session page can show the session's decision flow as a visual tree.
Each node has: icon, label, and status (`pending` / `active` / `done`). The
server's `/session-status` endpoint reports `active_decision` to highlight
the current node:

```html
<div class="tree" id="decision-tree"></div>
<script>
const DECISIONS = [
  { id: 'phase-1', icon: '🔍', label: 'Research options', status: 'done' },
  { id: 'phase-2', icon: '🏗️', label: 'Choose approach', status: 'active' },
  { id: 'phase-3', icon: '📋', label: 'Deploy', status: 'pending' },
];
function renderTree(activeId) {
  // Each node: clickable, polls status, highlights active
}
</script>
```

## Pitfalls

- **CRITICAL: Only interactive elements get hover states and pointer cursors.** Static information cards, description blocks, diagram sections, metric displays, step-numbered deployment plans, and tier cards must have `cursor: default` with no hover transition. Users interpret hover highlighting as "this is clickable" — fake interactivity is confusing and was explicitly called out as a problem. Radio options, checkboxes, buttons, nav links, and checkable tree nodes are interactive. Everything else is not. This applies to the `steps` CSS and any `tier-card` or `info-card` — they present data, they do not respond to clicks.
- **Do NOT auto-open the browser from the server's `__main__` block.** The agent opens the browser deliberately once. Remove `webbrowser.open` from the server template entirely — the agent controls browser lifecycle via `terminal("open http://...")`.
- **Don't build the HTML and the server as a single script.** Keep them separate. The server script serves files; the HTML files change per report. Separation makes iteration faster.
- **Auto-scan ports 8899-8920.** The self-terminating server template (`templates/mini-server.py`) scans for the first free port at startup. Never hardcode a single port — concurrent sessions collide.
- **Kill the old server before restarting.** Two servers on the same port fail silently (address reuse means the second one might crash the first). Always kill first.
- **Clear the response file on restart.** Stale responses from a prior run get read as if the user just submitted. Delete the file when starting fresh.
- **The confirmation page `/submitted` is served by the server script**, not an HTML file. It's included as inline HTML in the server template.
- **Keep HTML files under `/tmp/`** — the user didn't ask for these to be saved. If they want to keep a report, they'll tell you.
- **Don't use `fetch` with `No 'Access-Control-Allow-Origin'` issues** — the server must include the CORS header for POST to work from a file:// page or cross-origin.
- **After submitting, redirect to `/submitted`** so the user doesn't resubmit accidentally (double-submission of the same form corrupts the intent).
- **If the user submits multiple times (persistent server), the response file is overwritten each time.** The last submission wins. This is intentional — the user can change their mind.
- **For the self-terminating server, only one submission is accepted.** After that, the server shuts down. For multi-submit workflows, remove the `self.server.shutdown()` call or use a fresh server instance.
- **Avoid excessive complexity.** One page or two linked pages is enough. More than that and the user loses track of what they're deciding.
- **When the user corrects an assumption, verify before rendering.** If they say your architecture is wrong, SSH into the machines, run real commands, and build the corrected page from real data — don't just write a new HTML page based on the correction without independent verification.
- **Live session page polls do NOT inflate page counters.** The `/session-status` endpoint is handled in its own branch and doesn't increment `pvs`. Only actual page visits (GET on a PAGES-registered route) increment the counter. The dashboard's JS polls `/session-status` every 2s — those don't count as page views.
- **Reset counters when restarting the server.** If you're reusing an old server process, its global counters (pvs, form_count) carry over from the previous session. Kill and restart fresh.
- **`/update-status` collides with `/submit` if both save to the same file.** Keep status updates and form submissions on separate endpoints or separate response files.
