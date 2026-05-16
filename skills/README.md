# earchibald/hermes-skills

Personal Hermes Agent skill hub — curated skills for me and collaborators.

## Quick Start

```bash
# Add the tap (one-time)
hermes skills tap add earchibald/hermes-skills

# Search for a skill by keyword
hermes skills search <query>

# Install a skill
hermes skills install earchibald/hermes-skills/skills/<name>
```

## Structure

```
hermes-skills/skills/
├── <skill-name>/
│   ├── SKILL.md            # Required — skill definition (YAML frontmatter + markdown)
│   ├── references/         # Optional — supporting documentation
│   ├── templates/          # Optional — reusable file templates
│   └── scripts/            # Optional — helper scripts
├── LICENSE
└── README.md
```

Each directory under `skills/` is a single installable skill. No nested category directories — the flat structure ensures tap discovery works correctly with Hermes' one-level scan depth.

## Skill Catalog

### agent-icon-design
Design SVG icons/avatars for AI agents: draft SVG concepts, refine, render as HTML galleries.

### hermes-agent-skill-authoring
Write SKILL.md files with correct YAML frontmatter, structure conventions, and validation patterns.

### inter-agent-vault-coordination
Kanban-based coordination between autonomous agents via shared vault.

### interactive-reports
Self-terminating interactive report server with dual-channel browser+chat interaction: build HTML pages with forms, serve from a local HTTP server that auto-scans ports and self-terminates on submission. Output arrives in chat via notify_on_complete. Namespace-scoped for concurrent sessions. Includes server template + CSS toolkit.

### obsidian-projects-system
Operate the obsidian-projects issue tracker and agent orchestration system.

## Skill Format

Each skill requires `SKILL.md` with YAML frontmatter:

```yaml
---
name: skill-name
description: "Use when <trigger>. What it does in one sentence."
version: 1.0.0
author: earchibald
license: MIT
metadata:
  hermes:
    tags: [keyword1, keyword2]
    related_skills: [other-skill-names]
---
```

Body is markdown. Load via `skill_view(name)` — instructions inject into agent context. Reference files accessible via `skill_view(name, file_path=...)`.

## Contributing

PRs welcome. To add a skill:

1. Create `skills/<name>/SKILL.md`
2. Add `references/`, `templates/`, `scripts/` as needed
3. Update the catalog above
4. Open a PR

Skills are auto-discovered by the tap system — no registry registration needed.
