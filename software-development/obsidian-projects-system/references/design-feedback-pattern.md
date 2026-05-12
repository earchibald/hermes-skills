# Design Feedback — Document Pattern

When proposing a significant design decision that needs user input, create a structured feedback doc in the vault with checkboxes and comment fields. Deliver it to the user with an obsidian:// link.

## Structure

1. **Header** — who proposed it, what it's about, one-line context
2. **Numbered sections** — each covering one decision axis
3. **Per-section** — one sentence framing the question, then:
   - Checkbox list (`- [ ]`) with mutually exclusive options, each with a one-line description
   - A **Comments:** field (bold, blank line) for the user's free-form input
4. **Wildcard section** — "Anything else? Ideas I missed?"
5. **Sign-off section** — "Approved → build", "Approved with changes → revise", "Needs discussion → talk"

## Rules

- **Each checkbox line must be a complete, standalone option.** The user should understand what they're choosing without cross-referencing.
- **One blank line between Comments: label and the comment area.** Obsidian won't render the blank line, but it gives the user a clear insertion point.
- **Mutually exclusive options in the same subsection.** Don't mix independent axes.
- **Wildcard is always section N-1** (before sign-off). Never skip it.
- **Sign-off is always last.** Always three options: approved, approved-with-changes, needs-discussion.
- **Finish with an obsidian:// link.** The user should be one click away from the doc.

## Example skeleton

```markdown
# Thing Design — Feedback

> Who proposed it and why. This doc collects your decisions before we build.

## 1. Decision Axis

Frame the question.

- [ ] **Option A** — one-line description
- [ ] **Option B** — one-line description

**Comments:**


## N-1. Wildcard

Anything else?

**Comments:**


## N. Sign-off

- [ ] **Design approved — start building**
- [ ] **Design approved with changes noted above — build after revisions**
- [ ] **Needs discussion — let's talk**

**Comments:**
```

## Delivery

After writing the file to the vault, output:
- A plain-text summary of the sections (user may not open the doc immediately)
- The file path on disk
- An obsidian:// link: `obsidian://open?vault=<vault-name>&file=<url-encoded-path>`
