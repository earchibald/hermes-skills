# Hermes Skills — Personal Hub

A curated Hermes Agent skill hub, hosted by [earchibald](https://github.com/earchibald).

## Usage

Add this repo as a Hermes skill tap:

```bash
hermes skills tap add earchibald/hermes-skills
```

Then browse and install:

```bash
hermes skills browse        # see available skills
hermes skills install <id>  # install one
```

## Structure

```
hermes-skills/
├── <category>/
│   ├── <skill-name>/
│   │   ├── SKILL.md       # Required — the skill definition
│   │   ├── references/    # Supporting docs (optional)
│   │   └── scripts/       # Helper scripts (optional)
│   └── ...
├── README.md
└── LICENSE
```

Categories follow the [official Hermes skill conventions](https://github.com/NousResearch/hermes-agent):

`apple`, `autonomous-ai-agents`, `creative`, `data-science`, `devops`, `email`, `gaming`, `github`, `mcp`, `media`, `mlops`, `note-taking`, `productivity`, `research`, `smart-home`, `social-media`, `software-development`

## Contributing

Skills follow the standard SKILL.md format:

```yaml
---
name: skill-name
description: "Use when <trigger>. What it does in one line."
version: 1.0.0
author: earchibald
license: MIT
metadata:
  hermes:
    tags: [relevant, tags]
    related_skills: [other-skills]
---
```

PRs welcome. Brian can patch us.
