# earchibald/hermes-skills

Personal Hermes Agent skill hub — curated skills for me and collaborators.

## Quick Start

```bash
# Add the tap (one-time)
hermes skills tap add earchibald/hermes-skills

# Search for a skill by keyword
hermes skills search <query>

# Install a skill by its full repo path
hermes skills install earchibald/hermes-skills/skills/<category>/<name>
```

## Structure

```
hermes-skills/skills/
├── <category>/
│   ├── <skill-name>/
│   │   ├── SKILL.md            # Required — skill definition (YAML frontmatter + markdown)
│   │   ├── references/         # Optional — supporting documentation
│   │   ├── templates/          # Optional — reusable file templates
│   │   └── scripts/            # Optional — helper scripts
│   └── ...
```

Categories follow the [official Hermes skill taxonomy](https://github.com/NousResearch/hermes-agent):

| Category | Description |
|---|---|
| `autonomous-ai-agents` | Agent orchestration, spawning, multi-agent workflows |
| `creative` | Content generation, visual design, interactive reports |
| `software-development` | Coding workflows, project management, skill authoring |

## Skill Catalog

### autonomous-ai-agents

| Skill | Description |
|---|---|
| `inter-agent-vault-coordination` | Kanban-based coordination between autonomous agents via shared vault |

### creative

| Skill | Description |
|---|---|
| `agent-icon-design` | Design SVG icons/avatars for AI agents |
| `interactive-reports` | Build HTML report pages with forms, served from a local webserver. Enables dual-channel decision-making: information wall in the browser, form submissions come back to the agent. Includes server template + CSS toolkit. |

### software-development

| Skill | Description |
|---|---|
| `hermes-agent-skill-authoring` | Write SKILL.md files with correct frontmatter, structure, and validation |
| `obsidian-projects-system` | Operate the obsidian-projects issue tracker and agent orchestration system |

## Skill Format

Every skill requires a `SKILL.md` with YAML frontmatter:

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

The body is markdown. Skills load via `skill_view(name)` and their instructions are injected into the agent's context. Reference files and templates under `references/` and `templates/` are accessible via `skill_view(name, file_path=...)`.

## Contributing

PRs welcome. To add a skill:

1. Create `skills/<category>/<skill-name>/SKILL.md`
2. Add supporting files under `references/`, `templates/`, or `scripts/` as needed
3. Update the catalog table in this README
4. Open a PR

Skills are auto-discovered by the tap system — no registry registration needed.
