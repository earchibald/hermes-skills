# Orchestrator Observation — Implementation Pattern

How the orchestrator observation layer works. The cron script lives at `~/.hermes/scripts/orchestrator-observe.py`.

## Architecture

A Python script (`no_agent` cron, every 5 minutes) that:

### 1. Enumerate in-flight issues
Uses `obsidian-cli eval` to run a single JavaScript expression against the vault's metadata cache. The expression walks every `Projects/**/*.md` file, checks frontmatter for `type: issue` + `status: in-progress` + `agent:` set, and returns a JSON array. This is one CLI call regardless of vault size.

Key pattern — the eval code uses `??` (nullish coalescing) for numeric fields and `||` for string fields:
```javascript
priority: fm.priority || null,              // empty string → null
orch_status: fm.orch_status || null,         // empty string → null
orch_interventions: fm.orch_interventions ?? null,  // 0 is valid, only null means unset
```

Mistake to avoid: `fm.orch_interventions || 0` turns both unset AND zero into 0, making it impossible to detect "needs seeding."

### 2. Probe tmux liveness
The op-obsidian plugin spawns agent sessions in tmux under sessions named `op-agents`, `op-agents-1`, `op-agents-2`, etc. (one per iTerm window). Issue windows are named by `tmuxWindowName(issueId)` — the issue ID slugified with underscores allowed, case preserved. For "OP-271" the window name is "OP-271".

To find an issue's window: iterate all `op-agents*` sessions, list windows in each, match by window name.

### 3. Capture scrollback
`tmux capture-pane -t <session>:<window> -p -S -100` grabs the last 100 lines. Granular enough to detect activity changes; small enough to store densely.

### 4. Write snapshot
Timestamped files at `Projects/_orchestrator/snapshots/<issue-id>/<timestamp>.txt`. ISO 8601 UTC timestamps (`2026-05-11T18:30:00Z`).

### 5. Detect heartbeat
Compare the newly captured scrollback against the previous snapshot. If content differs (or no previous snapshot exists), the agent is active — update `orch_heartbeat` on the issue note. If content is identical, skip the heartbeat update.

### 6. Update frontmatter
- `orch_last_check` — always updated (ISO timestamp)
- `orch_heartbeat` — updated only on content change
- `orch_priority` — seeded from issue `priority:` if unset
- `orch_interventions` — seeded to 0 if unset

Uses `obsidian property:set` — works for both existing and new properties (creates them if absent).

### 7. Prune old snapshots
Keep last 48 snapshots per issue (~4 hours at 5-min intervals). Delete older ones.

## CLI Binary Paths

The observation script runs from cron with a minimal PATH. Use absolute paths:
- **obsidian CLI**: `/Applications/Obsidian.app/Contents/MacOS/obsidian-cli`
- **tmux**: `/opt/homebrew/bin/tmux`

## CLI Output Parsing

`obsidian-cli eval` prefixes its JSON output with `=> `. Strip this before parsing:
```python
if stdout.startswith("=> "):
    stdout = stdout[3:]
return json.loads(stdout)
```

`obsidian property:read` and `property:set` do NOT use the `=>` prefix — their output is plain text.

## Edge Cases

- **Obsidian not running**: `obsidian-cli` returns non-zero. Treat as soft failure — exit 0 so cron doesn't alert. The agent isn't available but that's expected when the user is away.
- **No in-flight issues**: exit cleanly, log count = 0.
- **Tmux session missing**: the agent session ended (user closed it, agent exited). Still update `orch_last_check`; skip snapshot and heartbeat.
- **Scrollback capture fails**: tmux pane may have been killed mid-capture. Update `orch_last_check` only.
- **First run on an issue**: no previous snapshot → content always differs → heartbeat always updates. Correct behavior.
