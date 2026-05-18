# Concept Lab Pattern

For creative/design exploration where the user needs to make multiple interdependent decisions, build a **multi-page concept lab** through interactive-reports. This pattern was proven on the agent-kumite redesign (May 17, 2026).

## Pages

### Page 1: Concept Lab (decisions)
The primary form page. Radio groups for every forkable decision. Checkboxes for mechanisms where multiple can be selected. Textareas for freeform input. Section nav at top for quick scrolling. One "Submit Concept Choices" button.

### Page 2: Wireframe (what it looks like)
A live animated mockup of the game/product using default selections. Spectator/operator view. Animated elements (horses on a track, thought streams rotating, prediction market prices pulsing). Gives the user something concrete to react to — often sparks new decisions.

### Page 3: Deep Dive (comparison + mechanics)
Comparison matrices, specific mechanics, emergent scenario examples, "why this fixes the old problems" autopsy. Validates the default genre choice with evidence. Emergent scenario examples are crucial — they show the user WHAT EMERGENCE LOOKS LIKE in this framework, not just abstract descriptions.

## Anti-Pattern: Waiting Idle

Do NOT wait for form submission before building pages 2 and 3. Build them proactively while the user considers page 1. The user's memory says they prefer forward progress and hate dead air. When the "continue toward your standing goal" prompt fires and the form isn't submitted yet, advance — add a page, write a reference doc, sketch an architecture diagram.

## Implementation Notes

- All pages use the same dark theme CSS (GitHub-dark inspired)
- `cursor: default` on all static elements; only radio options, buttons, checkboxes get hover
- PAGES dict in mini-server maps all routes before server start
- Server auto-scans 9100-9199 for free port; hardcode NS to prevent drift on restart
- Use execute_code + subprocess.Popen with SIGHUP ignore for server launch

## CRITICAL: Echo Parsed Choices Before Acting

After the user submits the concept lab form and you read latest.json, echo a plain-text summary of the parsed choices back to the user. Ask "Is this correct?" before spending cycles on architecture, API specs, or wireframes. Form data can be corrupted by JS bugs, stale page state, or reading a different submission. This session: JSON appeared to select Betrayal Race when user had actually chosen Social Deduction. Full Phase 2 API spec was built for the wrong game type before the user corrected it. A 10-second echo saves a 10-minute rebuild.
