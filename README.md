# earchibald/hermes-skills

Personal Hermes Agent skill hub — curated skills.

## For Humans: Quick Start

```bash
gh auth login                            # 5,000 req/hr (required for discovery)
hermes skills tap add earchibald/hermes-skills
hermes skills search <query> --source github
hermes skills install earchibald/hermes-skills/skills/<name>
```

## For Agents: Skill Index

When asked "what's in earchibald/hermes-skills?" load this README and scan the catalog below. Each entry describes the skill, when to trigger it, what files it ships, and its install identifier.

---

### agent-icon-design

**Install:** `earchibald/hermes-skills/skills/agent-icon-design`

**Description:** Design SVG icons/avatars for AI agents. Draft SVG concepts, refine via iterative feedback, render as HTML galleries for comparison.

**Use when:** User asks to design an icon, avatar, or visual identity for an agent. User wants SVG output or gallery-style comparison.

**Ships with:** SKILL.md, references/ (4 files: icon-refinement-techniques.md, loom-icon-case-study.md, rendering.md, svg-geometric-verification.md), templates/ (gallery.html, icon-sketch.svg)

---

### hermes-agent-skill-authoring

**Install:** `earchibald/hermes-skills/skills/hermes-agent-skill-authoring`

**Description:** Write SKILL.md files with correct YAML frontmatter, structure conventions, validation patterns, and category placement.

**Use when:** User says "save this as a skill" or asks to create a new SKILL.md.

**Ships with:** SKILL.md only.

---

### inter-agent-vault-coordination

**Install:** `earchibald/hermes-skills/skills/inter-agent-vault-coordination`

**Description:** Kanban-based coordination between autonomous agents via shared vault. Task handoff, status tracking, dependency resolution across agent sessions.

**Use when:** Multiple agents need to coordinate work through a shared project board. User mentions multi-agent task management.

**Ships with:** SKILL.md, references/ (test-harness-design.md), scripts/ (vault-test.py)

---

### interactive-reports (v2.3.0) ⚠️ `--force` required

**Install:** `earchibald/hermes-skills/creative/interactive-reports`

**Description:** Durable interactive report server — build HTML dashboards with forms, serve from a local HTTP server that stays alive for repeated submissions. Dedicated port range 9100-9199 avoids sibling agent collisions. Standalone poller script — no bash pipes, no permission prompts.

**⚠️ Requires `--force`:** The skill starts a local HTTP server, creates/cleans up temp directories, and reads environment variables for session namespacing. The Hermes skill scanner correctly flags these patterns. They are legitimate — install with `hermes skills install earchibald/hermes-skills/creative/interactive-reports --force`.

**Use when:** User has a "wall of information" to decide on (comparisons, architectures, trade-offs). User asks for HTML, browser, or interactive report. Trigger phrases: "interactive report", "let's go web", "report server", "dual-channel reporting".

**Ships with:** SKILL.md, templates/mini-server.py (v2 durable — no `self.server.shutdown()`), scripts/poller.py (standalone, no permission prompts), references/ (8 files: wall-of-information-css.md, ux-patterns.md, static-asset-serving.md, hardware-verification-before-rendering.md, screenshot-capture-technique.md, webhook-delivery-types.md, api-proxy-endpoints.md, server-pattern.py)

---

### obsidian-projects-system

**Install:** `earchibald/hermes-skills/skills/obsidian-projects-system`

**Description:** Operate the obsidian-projects issue tracker and agent orchestration system. Manage issues, projects, kanban boards, and cross-agent workstreams.

**Use when:** User references Agent-Vault, obsidian projects, issue tracking, or project orchestration.

**Ships with:** SKILL.md, references/ (3 files: design-feedback-pattern.md, orchestrator-design.md, orchestrator-observation.md)

---

## Repo Structure

```
skills/<name>/
├── SKILL.md            # Skill definition loaded by Hermes
├── references/         # Supporting docs (load via skill_view)
├── templates/          # Reusable file templates
└── scripts/            # Helper scripts
```

## Contributing

PRs welcome. Each skill directory is self-contained. See `skills/README.md` for format spec.
