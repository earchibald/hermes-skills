# Config State Verification

Before building an interactive report that recommends changes to the user's
Hermes configuration (enabling toolsets, installing skills, changing settings),
scrape the actual live state first. Assumptions about what's enabled are
often wrong and waste trust when the user corrects you.

## Commands

```bash
# Full config (keys + values)
hermes config show

# Toolsets with enable/disable status
hermes tools list

# All installed skills with source and status
hermes skills list

# Find skill SKILL.md files (deep listing)
find ~/.hermes/skills -name "SKILL.md" -maxdepth 3 2>/dev/null

# Quick category listing of skill directories
ls -1 ~/.hermes/skills/ 2>/dev/null
```

## When to Verify

Verify state BEFORE rendering if your report includes ANY of these:

| Claim Type | Example | Verify With |
|------------|---------|-------------|
| Toolset is disabled | "Enable moa for Mixture of Agents" | `hermes tools list` |
| Skill not installed | "Install kanban-orchestrator" | `hermes skills list` |
| Config value is wrong | "Your disabled_toolsets is empty" | `hermes config show` |
| Something is missing | "You don't have X enabled" | grep config.yaml for the key |
| Recommendation to install | Any "you should add" statement | Cross-check with installed state first |

## Common Traps

- **Don't assume skills aren't installed.** The user may have 127+ skills
  already. Always check `hermes skills list` before recommending installation.
- **`hermes tools list` vs `hermes config show`.** The tools list shows
  runtime enable/disable state. The config shows stored configuration values.
  They may disagree if a value was set but not used.
- **Skills can have nested categories.** `ls ~/.hermes/skills/` shows
  category directories like `devops/`, `mlops/`, `creative/`. Use
  `find -maxdepth 3` to find actual SKILL.md files inside categories.
- **The user's profile (from memory) is NOT a config source.** User profile
  tells you who they are; config/tool listings tell you what's actually
  set up. Don't substitute one for the other.
