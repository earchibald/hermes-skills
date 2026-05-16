# Cross-Project Agent Orchestrator — Design Artifact

> Designed for Argus (macOS CLI agent) to act as a swarm supervisor across all 25 projects in the Agent-Vault. This reference captures the architecture, not the per-session implementation state.

## Three-Layer Model

### Layer 1 — Observation (cron, every 5 min, script — no LLM tokens)
1. Enumerate all issues across all projects where `status: in-progress` AND `agent:` is set
2. For each, probe tmux: is the window alive? capture last ~100 lines of scrollback
3. Write timestamped snapshot to `Projects/_orchestrator/snapshots/<issue-id>/<ts>.txt`
4. If scrollback differs from previous snapshot, update `orch_heartbeat` on the issue
5. Update `orch_last_check` on the issue

### Layer 2 — Assessment (cron, every 15 min, LLM-powered)
1. Read the latest snapshot for each in-flight issue
2. Classify agent behavior using scrollback analysis:
   - `healthy` — recent output, forward progress, no error loops
   - `stalled` — no output change for >20 min, tmux alive
   - `needs_input` — agent asked a question, blocked on user response
   - `error_loop` — same error repeating, agent retrying futilely
   - `done_pending` — output contains summary/finalize language, no activity >15 min
   - `paused` — user explicitly excluded from watching
3. Write `orch_status` to issue frontmatter
4. Write line to `Projects/_orchestrator/HEARTBEAT.jsonl`
5. Regenerate `DASHBOARD.md` and `STALLED.md`
6. Trigger interventions for issues needing attention

### Layer 3 — Intervention (on-demand or assessment-triggered, LLM-powered)
Escalation ladder per classification:

**Stalled:**
1. Send newline via tmux (agent might be waiting on stdin)
2. If no response in 5 min: contextual nudge — "You appear stalled on {{id}}. Current status?"
3. If still no response in 10 min: escalate to user

**Error loop:**
1. Detect repeating pattern (>3 occurrences)
2. Kill tmux window, update issue to `blocked`
3. Surface to user: what errored, what I did

**Done pending:**
1. Verify completion from scrollback
2. If low-risk (simple + PR merged + tests pass): auto-finalize (version bump, commit backfill, op-resolve)
3. Otherwise: surface with one-click finalize offer

**Needs input:**
1. Extract the agent's question from scrollback
2. Surface to user with context — never answer on behalf of user

### Autonomy Toggle
Single setting: `orchestrator_autonomy: full | hitl`
- `full`: autonomous nudge, contextual prompt, kill/relaunch, auto-finalize low-risk
- `hitl`: surface everything, never act without approval

## Orchestrator Frontmatter Fields

All optional, all orchestrator-managed — agents never write these:

```yaml
orch_status: nominal           # nominal | stalled | needs_input | error_loop | done_pending | paused
orch_last_check: 2026-05-11T18:30:00Z
orch_heartbeat: 2026-05-11T18:28:00Z
orch_priority: med             # low | med | high
orch_interventions: 3          # numeric counter
orch_notes: "Waiting for CI; recheck at 19:00"
```

`orch_priority` is separate from issue `priority:` — it's the orchestrator's attention signal, not the project's urgency. Seeded from issue `priority:` on first observation, manually overridable.

## Vault Workspace

```
Projects/_orchestrator/
  DASHBOARD.md          ← auto-generated cross-project view
  HEARTBEAT.jsonl       ← append-only activity log
  STALLED.md            ← issues currently needing attention
  INTERVENTIONS/        ← per-intervention notes
  snapshots/            ← scrollback captures per issue
  _scratch/             ← temporary files
```

Under `Projects/` so Bases can aggregate. Not a real project — no prefix, no issue lifecycle.

## Notifications
- Discord DM — primary channel
- macOS notification via osascript — immediate visibility
- Vault notes (DASHBOARD.md, STALLED.md) always updated as persistent record

## Build Order
1. Observation cron (script, no tokens)
2. Assessment cron (LLM per in-flight issue)
3. Dashboard generator (script)
4. Intervention playbook (LLM + tmux)
5. Notifications (script)
