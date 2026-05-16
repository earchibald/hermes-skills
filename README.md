# earchibald/hermes-skills

Personal Hermes Agent skill hub — curated skills for me and collaborators.

## Quick Start

```bash
# Prerequisite: GitHub auth (5,000 req/hr — without it, discovery is rate-limited)
gh auth login        # or: echo "GITHUB_TOKEN=ghp_..." >> ~/.hermes/.env

# Add the tap
hermes skills tap add earchibald/hermes-skills

# Search for a skill
hermes skills search <query> --source github

# Install a skill
hermes skills install earchibald/hermes-skills/skills/<name>
```

## Skills

| Skill | Description |
|---|---|
| `agent-icon-design` | Design SVG icons/avatars for AI agents |
| `hermes-agent-skill-authoring` | Write SKILL.md with correct frontmatter and structure |
| `inter-agent-vault-coordination` | Kanban-based coordination between autonomous agents |
| `interactive-reports` | Dual-channel HTML report server with forms, live polling, decision-tree UX |
| `obsidian-projects-system` | Operate the obsidian-projects issue tracker and agent orchestration |

## Structure

```
skills/<name>/
├── SKILL.md            # Skill definition (YAML frontmatter + markdown)
├── references/         # Supporting docs
├── templates/          # Reusable file templates
└── scripts/            # Helper scripts
```

## Contributing

PRs welcome. Each skill directory is self-contained. See `skills/README.md` for the full format spec.
