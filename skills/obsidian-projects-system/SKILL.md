---
name: obsidian-projects-system
description: Operate the obsidian-projects issue tracker and agent orchestrator system — vault structure, issue lifecycle, agent dispatch, workflow modules, and plugin architecture. Load this when working on or with obsidian-projects issues, agent orchestration, or the OP vault workflow.
---

# Obsidian Projects (OP) — System Knowledge

## What it is

obsidian-projects is a two-component system for agentic software development:

1. **`op-obsidian`** — Obsidian plugin at `~/Code/obsidian-projects/plugins/op-obsidian/`. Provides the sidebar UI, schema-safe file operations, ID assignment, agent dispatch (via `openAgent`), orchestrator (iTerm layout management), and the CLI/URI handler surface.

2. **`op`** — Claude Code skill at `~/Code/obsidian-projects/plugins/op/`. Provides slash commands (`/op:scaffold`, `/op:new`, `/op:issue`, `/op:resolve`), workflow modules reference, and agent kickoff prompts.

**Repo:** `~/Code/obsidian-projects/` — git repo with `CLAUDE.md` governing dev workflow (always use worktrees, bump-version → dev-sync → smoke-test cycle).

**User's vault:** `~/work/Agent-Vault/` — the daily-driver vault, consumes op-obsidian via BRAT (not dev syncs). Dev syncs go to OP-Test vault at `~/Documents/OP-Test/OP-Test/`.

## Vault structure

```
Projects/<project-slug>/
  ISSUES/           ← open issues
  RESOLVED ISSUES/  ← closed issues (moved on resolve)
  TASKS/            ← subtask notes (trashed on resolve)
  DOCS/             ← specs, plans, ADRs, runbooks
  <project>.base    ← Bases dashboard (views)
  STATUS.md         ← project metadata (prefix, repo_path, vault)
  WORKFLOW.md       ← optional; SDLC policy, workflow modules config
```

**All projects** (25 active in Agent-Vault): agent-identity-kit, agent-kumite, agent-researchers, agent-utilities, audiobook-prep, callout-comments, cds, claude-code-telemetry, clearance, hide-and-seek, jira-bases, just-for-agents, ml-playground, model-storage-manager, muxiterm, obsidian-plugin-development, obsidian-projects, ollama-model-lab, op-demo, rein, slack-bases, statusline-plugin, tts-me-baby, vibecopd, where-is-it

## Issue lifecycle

**Frontmatter schema (issues):**
```yaml
id: <PREFIX>-<N>
project: <slug>
title: "<full title>"
type: issue
status: open | in-progress | blocked | resolved | wontfix
priority: low | med | high
created: YYYY-MM-DD
resolved:            # date field, set at resolve
agent: <claude|claude-ds|gemini|copilot>
agent_session: <session-id>
flow: evaluate | planning | plan | implementation | implement | review | finalization | finalize | done
complexity: simple | complex
parent: <PARENT-ID>
children: [<ISSUE-ID>, ...]
commits: ["<sha7> <subject>", ...]
pr: <url>
github_issue: <url>
version: <semver>
op_managed: true
```

**Filename:** `<PREFIX>-<N> <short-slug>.md`

**Lifecycle commands:**
- `obsidian vault=Agent-Vault op-scaffold project=<slug> prefix=<PREFIX>` — create project
- `obsidian vault=Agent-Vault op-new project=<slug> title="..."` — create issue
- `obsidian vault=Agent-Vault op-work issue=<ID>` — start work (flips to in-progress)
- `obsidian vault=Agent-Vault op-resolve issue=<ID>` — close (move to RESOLVED ISSUES/)
- `obsidian vault=Agent-Vault op-append-commit issue=<ID> sha=<sha> subject="..."` — log commits
- `obsidian vault=Agent-Vault op-set-pr issue=<ID> url=...` — set PR URL
- `obsidian vault=Agent-Vault op-set-section issue=<ID> name=Plan|Notes|Summary content="..." [append=true]`

**Task notes** live in `TASKS/<ID>.<N> ...md` with `op_managed: true`. Created at work start, auto-trashed on resolve.

## Agent orchestration architecture

### Agent dispatch (`openAgent.ts`)
`openAgent()` is the central launch function. Flow:
1. Resolve agent id (arg override → default → picker modal)
2. Verify binary presence via `AgentDetector`
3. Resolve working directory from settings or `STATUS.md` `repo_path`
4. Write `agent:` frontmatter immediately
5. In work mode, call `workIssue` to flip status → in-progress
6. Build prompt via `buildPrompt` (preamble + workflow modules + issue body + tasks)
7. Launch in terminal via `launchInTerminal` (tmux + iTerm)
8. Dispatch post-launch commands (color, rename, remote-control) via tmux send-keys

### Supported agents (`agentProfiles.ts`)
- **claude**: `claude`, `--permission-mode auto`, `/op:issue {{id}}` trigger
- **claude-ds**: `claude-ds`, same flags/triggers (transparent wrapper)
- **gemini**: `gemini`, empty flags, best-effort (untested)
- **copilot**: `copilot`, `--autopilot --allow-all`, best-effort (untested)

### Launch modes
`evaluate` → `plan` → `implement` → `review` → `finalize`
Each mode gets its own preamble, launch flags (Claude: inline agent JSON), and post-launch commands.

### Orchestrator (`orchestrator.ts`)
Lays out multiple agent sessions in iTerm panes using a grid layout. Each pane runs a tmux session with the agent process. Supports window creation, cell splitting, session reattachment, and dead-session cleanup. Registry persisted in plugin settings.

### Workflow modules system
- `WORKFLOW.md` can define multi-step workflows with `steps[]` referencing composable modules
- Variables resolve through precedence: Launch > Global > Project > Module > Default
- `promptBuild.ts` composes the final prompt: preamble → workflow section → issue header → body → tasks → commits
- OP-208 cutover: workflow modules are now the only path (no legacy inline fallback)

## Current obsidian-projects project state

**STATUS.md:** prefix=OP, repo_path=`~/Code/obsidian-projects`

**Open issues (ISSUES/):**
- OP-181: migration from WORKFLOW.md to composable workflow modules
- OP-192: Skill emission for lazy true modules
- OP-225: Worktree branch construction includes {{slug}} tail
- OP-226: docs update workflow-library example for local copilot CLI review
- OP-227: modules resolve `default_branch` var collision
- OP-228: Prefer loop for monitoring waits when agent is claude
- OP-229: Remove Obsidian focus-bounce on agent exit
- OP-237: op_issue tag missing on iTerm-restart reattach
- OP-240: op-dashboard release pipeline
- OP-241: Settings port-input inline error feedback
- OP-242: op-dashboard daemon regenerate-token + restart
- OP-257: Orchestrator Phases 2-6 managed-note discipline rollout
- OP-258: Fix iTerm tmux tracking loss after manual rearrange
- OP-271: Plugin-driven agent guidance via note append (in-progress)

## Key invariants

1. **Always target the vault explicitly:** `obsidian vault=Agent-Vault <cmd>` — never rely on focus
2. **Use `op-*` endpoints,** not raw Edit/Write on `op_managed: true` notes
3. **Work in git worktrees** per the project's `CLAUDE.md` — the delegating agent may still hold main
4. **op-resolve is atomic:** move to RESOLVED ISSUES/ + trash TASKS + set resolved date + optionally close github issue
5. **Agent-Vault is BRAT-only** — never dev-sync into it; dev syncs go to OP-Test
6. **Audit trail** lives at `Projects/_scratch/op-audit.jsonl` — every mutating op-* call logs a JSONL line
7. **Response payload** at `Projects/_scratch/op-last-response.md` — structured JSON from every CLI/URI op-* call

## Obsidian CLI pitfalls

### Binary location

The `obsidian` CLI is at `/Applications/Obsidian.app/Contents/MacOS/obsidian-cli`. It is NOT on the default PATH in cron or non-interactive environments. Always use the absolute path in scripts.

### Eval output has `=> ` prefix

`obsidian-cli eval code='...'` prefixes its output with `=> `. Strip this before JSON parsing:
```
=> {"ok": true}
```
The prefix is 3 characters (`=> `). `property:read` and `property:set` do NOT have this prefix.

### `property:set` creates properties

`obsidian property:set name=<new_field> type=string value=...` will create a frontmatter property that doesn't exist yet. No error, no precondition needed. Useful for seeding new orchestrator fields on existing issues.

### `||` vs `??` in eval JavaScript

When writing eval code that returns frontmatter values to Python:
- Use `||` for strings: `fm.field || null` — empty string and undefined both become null
- Use `??` for numbers: `fm.field ?? null` — 0 is a valid value, only undefined/null should signal "unset"

`fm.orch_interventions || 0` is a bug — it coerces both "not set" AND "set to 0" into 0, making seeding logic impossible.

## References

- [`references/orchestrator-design.md`](references/orchestrator-design.md) — cross-project agent orchestrator architecture (three-layer observation/assessment/intervention model, frontmatter fields, autonomy model, vault workspace layout)
- [`references/orchestrator-observation.md`](references/orchestrator-observation.md) — observation cron implementation: enumeration pattern, tmux probing, snapshot management, heartbeat detection, CLI binary paths, output parsing edge cases
- [`references/design-feedback-pattern.md`](references/design-feedback-pattern.md) — structured user feedback docs with checkboxes + comment fields, delivered via obsidian:// links
