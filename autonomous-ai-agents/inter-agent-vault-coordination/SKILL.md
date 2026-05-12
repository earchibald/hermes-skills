---
name: inter-agent-vault-coordination
description: "Set up vault-based inter-agent coordination: inbox/broadcast/pool directories, watchdog crons, and webhook notification mesh for multi-agent ecosystems."
version: 1.10.0
author: Argus
created_by: agent
platforms: [macos, linux]
trigger: "User asks to set up agent-to-agent communication, vault-based coordination, or multi-agent notification mesh. User asks about inbox/broadcast/pool patterns, vault-watchdog cron, or agent webhook mesh."
tags: [multi-agent, coordination, vault, webhook, cron, inbox]
---

# Inter-Agent Vault Coordination

A vault-based communication system for coordinating multiple Hermes agents sharing a single Obsidian vault.

## Architecture

```
Eugene ──> Agent-Share/broadcast/  (announcements to all agents)
Eugene ──> Agent-Share/pool/       (tasks for whoever claims them)
Eugene ──> <agent>/inbox/          (items for a specific agent)

Agent ──> Agent's own inbox/       (reads on cron — every 10 min)
Agent ──> Webhook POST ──> Other agent (notifies via webhook, NOT Discord)
```

**Key principle:** Notifications between agents use direct webhooks, not Discord. This saves tokens and avoids cluttering #agent-round-table with routine "check your inbox" pings.

---

## Phase-1 Development Pattern

When building multi-agent coordination tooling, develop and validate from **one agent's perspective first** before generalizing. This session's pattern:

1. **Phase 1** — Build and test from Argus (macOS, session-based). Prove the watchdog detects files, the webhook POST works, the cron fires.
2. **Phase 2** — Deploy to Hermes (nuc-1, always-on). Copy scripts, adjust vault path, register webhook route, create cron.
3. **Phase 3** — Deploy to Loom (k8s, container). Set up LoadBalancer, exec into pod to register routes, adjust vault path if mounted differently.

Never try to build for all three simultaneously. The first agent's working setup reveals the edge cases you'd miss designing from scratch.

---

## Components

### 1. Vault Directories

| Directory | Purpose | Reader |
|-----------|---------|--------|
| `Agent-Share/broadcast/` | Announcements to all agents | All |
| `Agent-Share/pool/` | Shared task pool (first claimer wins) | All |
| `<agent>/inbox/` | Items for a specific agent | That agent only |

### 2. Watchdog Script (`~/.hermes/scripts/vault-watchdog.py`)

A Python script that runs on a `no_agent=true` cron (every 10 min):
- Scans all agent inbox/ + broadcast/ + pool/ directories
- Tracks seen files via `~/.hermes/vault-watchdog-state.json` (checksum-based: mtime + size + first 80 bytes as SHA256 hex prefix)
- Stays **silent** (no output) when nothing is new — zero token cost since `no_agent=true` + empty stdout = no delivery
- When new items found:
  - Items for the local agent → outputs to stdout (delivered to that agent)
  - Items for other agents → POSTs to their webhook endpoint with HMAC-SHA256
  - Broadcast/pool items → POSTs to all reachable agents

**Per-agent webhook targets** are defined in the script as a `WEBHOOKS` dict with `url`, `secret`, and `event_type` per agent. When adding a new agent, add their webhook target here.

**Two variants exist:**
- `vault-watchdog.py` — full version (Argus on macOS). Scans all inboxes + shared dirs. POSTs to Hermes, Loom, and any other reachable agent.
- `hermes-watchdog.py` — deployed to nuc-1 as `vault-watchdog.py`. Scans all inboxes + shared dirs. Notifies Argus about broadcast/pool/argus-inbox items. (Named differently to avoid collision with Argus's local copy.)

### 3. Webhook Routes Per Agent

Each agent needs:
- An **incoming** webhook route that other agents POST to
- The route's event type must match what the watchdog sends

| Agent | Incoming Route | Event Type | Secret | Always reachable? |
|-------|---------------|------------|--------|-------------------|
| Argus (macOS) | `vault-cron` | `vault-update` | `vaultBridgeSecure2026` | ❌ Session-based |
| Hermes (nuc-1) | `agent-argus` | `agent-message` | `wcZgCe...LjIg` | ✅ 24/7 gateway |
| Loom (k8s) | `vault-cron` | `vault-update` | `vaultBridgeSecure2026` | ✅ 24/7 pod |

**Registration command:**
```bash
hermes webhook subscribe vault-cron \
  --events "vault-update" \
  --secret "<secret>" \
  --deliver discord
```

**Route names for Hermes (nuc-1):**
- `agent-argus` — receives `agent-message` events from other agents (Argus, Loom), delivers to **Discord DM to Hermes** (not round-table). See "Webhook Route Design Rationale" below for why DM vs round-table depends on the receiving agent's availability model.
- `agent-homelab` — **DEPRECATED.** Log-only route (no agent triggered). This was a pre-Loom placeholder. Remove when confident Loom's routes are stable.

### Webhook Route Design Rationale

The mesh uses two different event types and delivery destinations depending on the receiving agent's availability model:

| Agent type | Examples | Incoming route | Event type | Delivers to | Rationale |
|------------|----------|---------------|------------|-------------|-----------|
| **Always-on** (24/7 gateway) | Hermes (nuc-1), Loom (k8s) | `agent-argus` | `agent-message` | **DM** | Has a persistent gateway — will receive the DM immediately. No risk of missed delivery. DM keeps #agent-round-table clean. |
| **Session-based** (no 24/7 gateway) | Argus (macOS) | `vault-cron` | `vault-update` | **#agent-round-table** | No persistent gateway to receive DMs. Round-table guarantees visibility — Eugene or another agent sees the notice even if the target agent is offline. The vault file persists regardless. |

**Key insight:** The event type determines delivery, not the route name. Both routes accept both event types, but only one pairing makes sense per agent:
- `agent-message` → DM works for always-on agents that can receive immediately
- `vault-update` → round-table works for session-based agents where Discord visibility is the fallback

This is why Loom→Hermes (DM via `agent-argus`) and Loom→Argus (round-table via `vault-cron`) use different routes — they target fundamentally different availability models. Documenting this prevents a future agent from "simplifying" the routes into a single delivery rule that would break one of the two models.

**Caveat:** The `agent-argus` route is named for the Argus→Hermes direction. It's reused for Loom→Hermes because both senders target the same always-on receiver. The name is historical (pre-dates Loom's existence) but functional.

### 4. Cron Jobs

Every agent runs a `no_agent=true` cron every 10 minutes:

```bash
hermes cron create "every 10 minutes" \
  --script vault-watchdog.py \
  --no-agent \
  --name "vault-watchdog (<agent>)" \
  --deliver local
```

**How silent watchdog works:**
- `no_agent=true` means stdout is delivered verbatim
- Script produces NO output when nothing is new → cron delivers nothing → zero tokens used
- Script produces output only when new items detected → delivery happens automatically
- State file at `~/.hermes/vault-watchdog-state.json` (SHA256 checksum of mtime+size+first-80-bytes) prevents re-notification

**Manual trigger (for testing, skip the 10-min cron wait):**
```bash
python3 ~/.hermes/scripts/vault-watchdog.py
```
This is the same script the cron runs. Useful for debugging detection and webhook delivery. Run after writing a test file to verify the pipeline fires instantly.

**The webhook message includes a 2,000-char file content preview.** When the watchdog detects a new file, it reads the first 2,000 characters and includes them in the webhook message body. The receiving agent gets enough context to understand the request without needing to read the file separately. This is especially important for cross-machine scenarios where the vault may not be synced yet. The preview size is set in two places in `vault-watchdog.py`: (a) `f.read(2000)` in the `notify_via_webhook` function for webhook payloads, and (b) `f.read(2000)` in the main loop for local stdout previews. If the preview truncates important content, bump this value in both spots.

### 5. K8s LoadBalancer (for Loom webhook reachability)

Loom runs in a k8s pod and needs its webhook port (8644) exposed to the LAN:

```bash
# 1. Ensure MetalLB has an L2Advertisement selecting the IP pool
microk8s kubectl patch l2advertisement -n metallb-system example \
  --type=merge -p '{"spec":{"ipAddressPools":["cheap"]}}'

# 2. Change Service type from NodePort to LoadBalancer
microk8s kubectl patch service -n homelab homelab-gateway \
  --type=merge -p '{"spec":{"type":"LoadBalancer"}}'

# 3. Register webhook route inside the pod
microk8s kubectl exec -n homelab deploy/homelab-gateway -- \
  hermes webhook subscribe vault-cron \
    --events "vault-update" \
    --secret "vaultBridgeSecure2026" \
    --deliver discord
```

---

## Vision Proxy Pattern

When an agent runs a model that lacks vision capabilities (e.g., deepseek v4 pro), another agent with image rendering or vision must proxy visual asset generation.

### Pattern: "I design, you render"

1. **No-vision agent** writes their identity brief (`my_icon_prompt.md`) with exact SVG geometry specs — color hex codes, node positions, line paths, glow parameters. Since they can read their own SVG source even though they can't see the PNG, they can specify exact coordinate values.

2. **Vision-capable agent** reads the brief, drafts SVG concepts, renders PNGs with `rsvg-convert`, and places assets in the no-vision agent's `corpus/icons/`.

3. **Review loop**: The no-vision agent reads the SVG source and requests coordinate/color modifications via vault inbox. The vision agent iterates the SVG and re-renders.

4. **Delivery**: Final SVG + PNG set (1024/512/128) plus `index.md` in the target's vault directory.

### Why this belongs here

Not a standalone skill — this is a **coordination pattern** between agent roles. The vision-providing agent temporarily acts as a graphics pipeline for another agent. The vault is the shared workspace, Discord @mentions are the notification channel.

### Pitfalls

- **Don't assume the no-vision agent can see the gallery HTML.** They need a `gallery.html` for the vision-capable human reviewer, but the no-vision agent needs the raw SVG source text. Always include both.
- **Coordinate SVG edits precisely.** The vision-providing agent must implement exact coordinate changes described in natural language. If the no-vision says "move bottom-left node 10px right", translate the exact coordinate shift.
- **Check the target agent's model capabilities before deciding who renders.** The vision proxy is only needed when the target agent's model cannot process images. Some models within the same provider family differ — e.g., deepseek v4 flash supports vision, v4 pro does not.

---

## Setup Steps

### First agent setup (e.g., Argus on macOS):

1. Create broadcast/ and pool/ directories:
   ```bash
   mkdir -p ~/work/Agent-Vault/Agent-Share/{broadcast,pool}
   ```

2. Create the watchdog script at `~/.hermes/scripts/vault-watchdog.py` with per-agent webhook targets
3. Register the incoming webhook route:
   ```bash
   hermes webhook subscribe vault-cron \
     --events "vault-update" \
     --secret "vaultBridgeSecure2026" \
     --deliver discord
   ```
4. Create the cron job:
   ```bash
   hermes cron create "every 10 minutes" \
     --script vault-watchdog.py \
     --no-agent \
     --name "vault-watchdog (argus)" \
     --deliver local
   ```

### Second agent setup (e.g., Hermes on nuc-1):

1. Check the vault path (usually different from macOS — e.g., `~/obsidian-vaults/Agent-Vault/`)
2. Copy the watchdog script, adjusting: vault path, webhook targets, and webhook secret
3. Push script to the remote machine:
   ```bash
   scp ~/.hermes/scripts/hermes-watchdog.py user@host:~/.hermes/scripts/vault-watchdog.py
   ```
4. Register an incoming webhook route on the first agent that points back to this agent
5. Create the cron on the remote machine:
   ```bash
   ssh user@host 'hermes cron create "every 10 minutes" \
     --script vault-watchdog.py --no-agent \
     --name "vault-watchdog (hermes)" --deliver local'
   ```
6. Update the first agent's watchdog script to include this agent's webhook target

### Third / K8s agent setup (e.g., Loom):

1. Create their inbox/ directory in the vault
2. Set up LoadBalancer Service + MetalLB (see §5 above)
3. Exec into pod to register webhook route
4. Add their webhook target to existing watchdog scripts
5. Deploy the watchdog script into the pod's `~/.hermes/scripts/` (hostPath or ConfigMap)
6. Deploy scripts into the pod via `kubectl cp` (not heredoc — heredocs mangle Python string quotes inside f-strings):
   ```bash
   # Write the script locally first
   # Then copy into the pod
   kubectl cp /tmp/<script>.py <ns>/<pod>:/opt/data/scripts/<script>.py
   kubectl exec -n <ns> deploy/<app> -- chmod +x /opt/data/scripts/<script>.py
   ```
7. Set up the cron job inside the pod. If `hermes cron create` isn't available or behaves differently in the container, write the job directly to the cron JSON file:
   ```bash
   kubectl exec -n homelab deploy/homelab-gateway -- python3 -c "
   import json
   job = {
       'id': 'loom-vault-watchdog',
       'name': 'vault-watchdog (loom)',
       'prompt': '',
       'script': 'vault-watchdog.py',
       'no_agent': True,
       'schedule': {'kind': 'interval', 'minutes': 10, 'display': 'every 10m'},
       'enabled': True,
       'state': 'scheduled',
       'deliver': 'local',
       # ... other fields
   }
   data = {'jobs': [job], 'updated_at': '2026-05-11T19:42:00Z'}
   with open('/opt/data/cron/jobs.json', 'w') as f:
       json.dump(data, f, indent=2)
   \" 2>&1
   ```
8. **Keep test scripts in sync.** The master copy lives at `Agent-Share/vault-test.py`. Pod-local copies go stale when the master is fixed (e.g., changing `nuc-1.local` → LAN IP). After deploying to a k8s agent, re-`kubectl cp` the vault-test.py master copy into the pod's `scripts/` directory, or use a shared volume.

---

## Webhook POST Example

```python
import hmac, hashlib, json, urllib.request

secret = "<subscription_secret>"
payload = json.dumps({
    "event_type": "vault-update",  # or "agent-message"; must match subscription
    "sender": "AgentName",
    "message": "Content here"
}).encode()

sig = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()

req = urllib.request.Request(
    "http://target-host:8644/webhooks/<route>",
    data=payload,
    headers={
        "Content-Type": "application/json",
        "X-Webhook-Signature": sig,
    }
)
resp = urllib.request.urlopen(req, timeout=10)
```

**Expected success:** `{"status": "accepted", "route": "...", "event": "...", "delivery_id": "..."}`

---

## Test Harness

A shared regression test file lives at:
- `~/.hermes/scripts/vault-test.py` (local copies)
- `~/work/Agent-Vault/Agent-Share/vault-test.py` (vault, for all agents)

Also bundled with this skill as `scripts/vault-test.py`.

**Key design principle: each agent tests its OWN outgoing webhooks.** No agent tests incoming routes (self-test is pointless). No agent tests on another's behalf (can't be measured remotely). Every agent gets exactly **2 webhook reachability tests** — symmetric count. See `references/test-harness-design.md` for the full design rationale.

```bash
# Full test — runs all checks
python3 scripts/vault-test.py

# Quick test (skip webhook probes for offline mode)
python3 scripts/vault-test.py --quick

# Clean up test files
python3 scripts/vault-test.py --cleanup
```

The test harness auto-detects which agent is running it via `detect_agent()` and builds the target list accordingly.

**Tests performed:**
| # | Section | What it checks | Count |
|---|---------|----------------|-------|
| 1 | Infrastructure | Vault root + 5 directories exist | 6 |
| 2 | Watchdog Health | Script exists, compiles, cron registered, state file exists | 4 |
| 3 | Webhook Reachability | Each agent posts to the other two siblings | 2 |
| 4 | Vault Write + Detect | Creates test file in broadcast/ + own inbox | 2 |
| 5 | State File Integrity | All 5 sections present, file counts | 6 |
| 6 | Self-Reference Fix | First-person instruction in config/skills | 1 |
| 7 | Webhook Registrations | Subscription file exists, route entries | 2-3 |

**Regressions:** After any changes to vault structure, watchdog scripts, webhook routes, or inter-agent config.

---

## Receiver-Side Processing Protocol

When an agent receives an inbox item (via watchdog output or webhook notification), follow this workflow:

### Processing checklist

0. **🔄 Re-fire check (do this first, before anything else)** — Determine if this notification is a **duplicate re-fire** rather than new work. Happens when:
   - A previous session already processed this inbox item and wrote a response
   - The file was saved locally on macOS → rsync pushed it to nuc-1 → nuc-1 watchdog re-detected it as "new"
   - The watchdog state file's checksum changed due to file move (inbox → archive)
   - **⚠️ Two sibling subagents both detect the SAME new file and start processing simultaneously.** This happens because Hermes Agent can spawn multiple sessions from the same webhook trigger. Both sessions receive the same notification body and both begin processing independently.
   
   **How to detect a re-fire:**
   - `session_search(query="topic keywords")` — if a prior session mentions this exact file, a response was already sent
   - SSH to nuc-1 and check if the file is already in `Argus/archive/`: `ssh nuc-1.local 'ls /home/earchibald/obsidian-vaults/Agent-Vault/Argus/archive/'`
   - Check if a response file already exists in the sender's inbox on nuc-1: `ssh nuc-1.local 'ls /home/earchibald/obsidian-vaults/Agent-Vault/<sender>/inbox/'`
   - **Sibling subagent detection** — if you find the source file was already archived, the journal was recently updated by another session, or a response file was written to the sender's inbox with a timestamp from the last 30 seconds, another sibling is actively processing this. Look for these signs:
     - `patch()` or `write_file()` returns "modified by sibling subagent" with a timestamp — re-read the file, the sibling already wrote something
     - The source file is missing from inbox/ but you didn't archive it — sibling already handled it
     - A response file exists in the sender's inbox with a newer timestamp than the original notification
   
   **If confirmed re-fire:**
   - Save the file locally (archive directly, don't re-process)
   - Log in journal: "Received re-fire of [file] — already handled at [prior session time]"
   - Skip all subsequent processing steps
   - Do NOT write another response (the sender already has one) — duplicate responses from different siblings with slightly different framing are harmless but wasteful; the recipient reads two nearly-identical acknowledgments for the same event
   
   **Sibling conflict mitigation:**
   - Before writing ANY response, check if a response already exists in the target inbox. If one with a recent timestamp (< 60 seconds) is there, re-read it — your sibling may have already said everything needed. Only add more if your framing adds genuinely new information.
   - If writing a response and the `patch` tool says "modified by sibling subagent", re-read the target file. If the sibling's version already covers you, stop — your duplicate isn't needed. If yours adds something, append.
   - Re-read the journal before appending. If a sibling already logged the work, your additional entry is redundant. Don't write another one unless you have distinct information to add.
   
   **If not a re-fire:** proceed to step 1.

1. **📍 Locate the file** — Know your vault path. On this agent: `~/work/Agent-Vault/`. On nuc-1: `/home/earchibald/obsidian-vaults/Agent-Vault/`. The vault may not be synced; check both locally and on the sender's machine if possible.

2. **🔍 Recover context via session_search** — Before acting, search past sessions for the referenced topic. Many inbox items refer to work that happened in a previous session. Use `session_search(query="topic keywords")` to understand what came before. This prevents re-research or misinterpretation. If session_search finds a prior session that already processed THE SAME inbox item, treat this as a re-fire (see step 0).

3. **📖 Read and evaluate** — Full read of the item. Understand intent, action requested, and any referenced prior work. If the item is feedback/edits on a vault document you wrote, **read the target document concurrently** to verify each point:

   **Case A: Standalone task** — Inbox item is a request to do something new. Follow the standard response flow below.

   **Case B: Collaborative editing/feedback (single reviewer)** — Inbox item is feedback on a vault document you authored:
   - Load the target document with `read_file`
   - Cross-reference each feedback item against the actual text
   - Apply corrections (patch/edit)
   - Note any feedback that's already been addressed (stale-read issues)
   - Then reply with what changed and what was already correct
   - Archive the feedback item when done

   **Case C: Multi-reviewer consolidation** — When two or more agents review the SAME document, consolidate before editing:
   - **Step 1 — Gather all reviews.** Read each reviewer's inbox file. Extract actionable items into a scratch list (one row per finding: | Reviewer | Finding | Action | Status |).
   - **Step 2 — Read the current doc.** Load the target document. Check the **Revision History** section — earlier review cycles may have already applied fixes. Any finding already logged as committed is DONE — skip re-processing.
   - **Step 3 — Cross-reference overlap.** Merge duplicated findings (both Hermes and Loom called out the missing bot entry → one fix covers both). Split conflicting suggestions into separate decisions.
   - **Step 4 — Determine what's still pending.** After dedup + stale-read filter, the remaining items are what actually needs work. Group them by: (a) ready to fix, (b) needs user input, (c) aspirational/future.
   - **Step 5 — Respond to each reviewer.** Write one coherent response per reviewer. Include: changes made from their feedback, items already fixed (with evidence from revision history), items deferred and why.
   - **Step 6 — Update the doc once.** Apply all merged corrections in a single pass. Update revision history with a consolidated entry like: `"v1.2 — Incorporated feedback from Hermes and Loom"`.
   - **Step 7 — Log in journal.** Brief entry tracking which reviewers, total findings, how many were pre-fixed, how many applied.

   **Case D: Late-arriving feedback on a completed deliverable** — When an agent sends feedback on a deliverable you've already finalized and delivered (e.g., a vote that arrives after you made an executive decision):
   - **Do NOT reject late feedback by default.** Late ≠ invalid. The agent's vote represents legitimate analysis you may not have had. The pattern is: evaluate → confirm → iterate → re-deliver, not "already done, closed."
   - **Read the current deliverable.** Load the actual deliverable file (e.g., SVG source, markdown doc, rendered asset). **Crucially: check the file size on both your local vault AND the sender's vault.** If sizes differ, the sender may be reviewing a different version than what's on your local machine. The one-way rsync (macOS→nuc-1) means files written by nuc-1 agents may not match your local copy. Use `wc -c` locally and via SSH to compare. If mismatched, the sender's version is the one they reviewed — read THAT version to understand their feedback accurately.
     - **Already addressed** — Note it. Say so explicitly in your response. The agent put effort into their review; ignoring their points erodes trust.
     - **Genuinely new** — Apply the change. Iterate the deliverable to v2/v3 even if v1 was "finished."
     - **Needs clarification** — Flag it. Request detail rather than guessing.
   - **Classify each request** into one of: ✅ *already in place*, 🔧 *applied in iteration*, ❓ *needs clarification*, 🔵 *deferred to future*.
   - **Iterate the deliverable** — Produce v2 with the accepted changes. Update revision history/changelog in the deliverable's documentation file (e.g., `index.md` or design notes). Re-render or rebuild as needed.
   - **Re-deliver the updated assets** — Place the new version in the same location as the original. The original files are replaced by the improved versions.
   - **Respond to ALL involved agents** — Write a response in:
     1. The sender's inbox (for their records)
     2. `Agent-Share/broadcast/` (so all agents know the state change)
     3. Discord #agent-round-table (real-time notification, especially if the agent asked other agents for feedback)
   - **Include a classification table** in the response showing each request, its disposition, and what changed. This prevents agents from re-requesting the same changes.
   - **Log in journal** — Brief entry with the total request count, how many were pre-addressed, how many applied.
   - **Key principle:** A deliverable is never truly "done" until all agents who should have voted have voted. The cost of a v2 iteration is small; the cost of shipping a deliverable that an agent had substantive feedback on is high.

   **⚠️ Webhook notification truncation:** The watchdog sends up to a 2,000-char file preview in the webhook body. For files longer than ~300 lines, the preview truncates mid-content. If the notification body cuts off (e.g., "1. R"), first check your **local vault** — the file may be synced there. If not, SSH to the remote host that has the vault or use alternative channels (Discord #agent-round-table, broadcast pool) to re-deliver.

4. **💬 Write a response** — Place your response in the **sender's inbox** (`Agent-Vault/{sender}/inbox/{NNN}-topic.md`):
   - Include a `> **From:** <you>` header
   - Reference the original item by number/name
   - Mark status: `agreed ✅`, `dispatched`, `needs clarification`, etc.
   - Keep responses substantive but concise
   - **If the sender also posted to Discord** (e.g., posted review to `#agent-round-table` simultaneously), an acknowledgment in the same channel can suffice instead of a formal inbox response. Judge based on context — inbox responses are for durable records, Discord for real-time.

5. **📬 Deliver the response** — If vaults are on separate machines (macOS vs nuc-1), copy the response to the remote vault:
   ```bash
   scp ~/work/Agent-Vault/{sender}/inbox/{response}.md {remote}:/path/to/vault/{sender}/inbox/
   ```

6. **📦 Archive the original** — Move from `inbox/` to `archive/` (NOT `processed/`):
   ```bash
   mkdir -p ~/work/Agent-Vault/{agent}/archive
   mv ~/work/Agent-Vault/{agent}/inbox/{item}.md ~/work/Agent-Vault/{agent}/archive/
   ```
   If the remote vault isn't reliably reachable, archive locally — the file is safe on the sender's side. For NUC-hosted vaults, SSH to archive remotely:
   ```bash
   ssh nuc-1.local 'mkdir -p /home/earchibald/obsidian-vaults/Agent-Vault/<agent>/inbox/processed && mv /home/earchibald/obsidian-vaults/Agent-Vault/<agent>/inbox/{item}.md /home/earchibald/obsidian-vaults/Agent-Vault/<agent>/inbox/processed/'
   ```

7. **📝 Log in journal** — Brief entry in `Agent-Vault/{agent}/journal/{YYYY-MM-DD}.md`:
   ```markdown
   ## Inter-agent processing: <topic>
   - Received from: <agent>
   - Item: <NNN-topic.md>
   - Action: accepted / dispatched / delegated
   - Response: <NNN-response.md> placed in <agent>'s inbox
   ```

### Status annotation convention

Every inbox item gets status annotations in the body. As the item moves through processing, update the status:

- `**Status:** pending` — newly received, not yet evaluated
- `**Status:** in_progress` — being worked
- `**Status:** dispatched` — processed, response sent, awaiting confirmation
- `**Status:** archived` — more than 7 days old, or confirmed received by sender

### Urgency convention

- Prefix with `URGENT-` for time-sensitive items. Prioritize these first on session start.

### Inbox/outbox simplification

The target agent's **inbox** IS the sender's **outbox**. There is no separate `outbox/` directory. When you need to send a message to Hermes, write it to `Agent-Vault/Hermes/inbox/`. When Hermes sends you a message, it writes to `Agent-Vault/Argus/inbox/`. This keeps the directory structure flat and unambiguous.

---

## No-Reply Escalation Pattern

When an agent posts a vote request or collaborative decision (vault broadcast + Discord ping) and **no agent responds by the deadline**:

1. **Make the executive decision** — The originating agent has the most context. Proceed with the option that best satisfies the identity brief. Document the rationale clearly in a vault note.
2. **Mark the deliverable as PENDING CONFIRMATION** — Not final. Late feedback is still valid and should be treated as a genuine iteration, not a rejection of the decision.
3. **Push the deliverable** — Place assets in the target vault, write index.md, notify all agents on Discord.
4. **Stay receptive to late feedback** — When feedback arrives hours or sessions later (via vault inbox), process it through the standard workflow. Do NOT dismiss with "already decided." A v2.1 correction is cheaper than shipping a deliverable that violates the recipient's identity brief.
5. **Iterate without defensiveness** — Late feedback is not criticism of your decision; it's information the other agent couldn't provide at the time. Implement it and re-render.

**Pitfall: "No vote = they agree" is a dangerous assumption.** The other agents may simply not have been in-session when the request arrived. Session-based agents (Argus on macOS) have no 24/7 gateway and may miss vault notifications entirely. Always-on agents (Hermes, Loom) are more reliable but may be busy. Default interpretation: no vote = unknown, not no vote = abstain.

---

## Visual Asset Iteration Pipeline

For icon/avatar projects where agents have mixed vision capabilities, expect **multiple review passes** even with good initial concepts:

| Pass | Who reviews | Method | Example Outcome |
|------|-------------|--------|----------------|
| 1. Concept fit | No-vision target agent | SVG coordinate audit vs identity doc | "Green-light concept A" or "violates my no-hierarchy principle" |
| 2. Visual QA | Vision-capable agent | Actual image inspection of rendered PNGs | "Bloom clipping at top, nuc-1 dominates visually" |
| 3. Identity correction | The target agent (no-vision) | Coordinate audit on refined v2 | "Nodes must be geometrically identical, not just visually similar" |

**Key principle:** An icon is not "done" until all three passes complete. The originating agent's v1 draft is just the starting point — the most valuable feedback arrives after delivery, when other agents independently review and catch issues the drafter missed.

### Don't skip the vision QA step

Coordinate audits catch geometry errors but miss rendering artifacts — bloom clipping, stroke aliasing, glow halo truncation at PNG boundaries. Always ping a vision-capable agent to inspect the actual PNGs before declaring the icon final.

### Handling vault sync artifacts in iterations

When a deliverable is scp'd from macOS to nuc-1 mid-iteration, the remote vault may briefly hold a stale version. If a reviewer's finding references an element that was already removed in your local copy:

- Do NOT dismiss the review as invalid — the reviewer analyzed the file they had
- Confirm the finding with a disposition table: "✅ Already in place in v2.1" vs "🔧 Applied now"
- Re-sync the corrected version and verify file sizes match

---

## Pitfalls

### Watchdog & Webhook

- **Vaults are NOT synced in real time.** The macOS vault (`~/work/Agent-Vault/`) and nuc-1 vault (`~/home/earchibald/obsidian-vaults/Agent-Vault/`) are separate filesystems. Write to both when you need the other agent to see your response on their next watchdog tick. If you can only reach one, write to the machine the target agent runs on.
- **SSH to nuc-1 may timeout.** The nuc-1 machine is reliable but networking can hiccup. If scp/ssh fails, the local copy is enough — Hermes will pick it up on the next rsync or when the user next talks to him directly.
- **⚠️ One-way rsync: macOS→nuc-1 only.** Vault sync flows one direction: from macOS to the nuc-1 cluster. Files written by Loom (k8s) to `/home/earchibald/obsidian-vaults/Agent-Vault/` do NOT sync back to macOS. If you need a file from the k8s vault, SSH to fetch it or ask the sender to re-deliver via Discord/broadcast. Conversely, files written locally on macOS WILL sync to nuc-1.
- **⚠️ Rsync timing causes stale review findings.** When a deliverable gets pushed from macOS to nuc-1 (scp, rsync), and the reviewing agent (e.g., Hermes on nuc-1) runs their analysis between the push and the reviewer's session, they may analyze pre-sync files. This manifests as findings about elements that were already removed (e.g., detecting a triskelion that was removed two revisions prior). This is not the reviewer's fault — the async file transfer creates an unavoidable timing window. On the receiving end (the agent being reviewed), **always cross-reference each review finding against the actual current state of the artifact** before acting. Build a disposition table with "✅ Already in place" for stale findings. Do NOT reject the entire review as invalid — the reviewer's other findings are typically genuine and valuable. A single stale finding does not invalidate the rest.
- **⚠️ rsync causes watchdog re-fires.** When you save a vault file locally (macOS), rsync pushes it to nuc-1's vault minutes later. The nuc-1 watchdog then detects the "new" file and re-fires the notification — even though you already processed it from the webhook body. This creates duplicate sessions for the same item. Mitigation: always run the re-fire check (step 0 in processing checklist) before doing any work. If the file was already handled in a prior session, archive locally and skip. Don't try to fix the watchdog (it's working correctly — it doesn't know the content was already delivered via webhook).
- **⚠️ Verify scp file integrity — local and remote copies can diverge silently.** After `scp`-ing deliverable files (SVGs, PNGs, markdown) to a remote vault, verify that the destination file sizes match the source. Silent failures happen when: scp targets a stale directory, the remote path doesn't exist, permissions don't allow overwrite, or a previous version sits in a different location. A 10KB local SVG ending up as 13KB on the remote means the remote agent is reviewing DIFFERENT content than what you finalized. Check with: `wc -c local.file && ssh remote 'wc -c remote.path/file'`. If sizes don't match, re-scp with explicit destination and verify. This is especially critical when iterating versions (v1.1 → v1.2) — the reviewer's feedback applies to the remote copy, which may not be the file you think it is.
- **📬 Re-delivery protocol for truncated messages.** When an agent reports they couldn't read the full content of your message (truncated by watchdog preview limit, transient file, or network issue):
  1. **Check your local vault** — the original file is still there if you wrote it locally
  2. **Search session history** via `session_search` — past conversations may have the full context
  3. **Re-deliver via Discord** — post full content to `#agent-round-table` tagging the recipient's bot ID (`<@BOT_ID>`)
  4. **Mirror to Agent-Share/broadcast/** — write the full content there for persistent availability
  5. **Log in journal** — note the re-delivery and channels used
  6. **Do NOT archive the sender's request** until you've confirmed delivery
  7. **Patch the root cause** — if the watchdog preview limit caused it, bump `f.read(N)` in the watchdog script
- **Don't archive until the sender confirms.** The 7-day rule prevents premature deletion. For critical protocol items, keep in inbox until the response is acknowledged.
- **Journal entries are for you, not the other agent.** Use the inbox for inter-agent messages; use the journal for your own internal recordkeeping. The other agent won't read your journal.

### Setup & Deployment

- **Vault paths differ per agent.** macOS: `~/work/Agent-Vault/`. nuc-1 Linux: `~/obsidian-vaults/Agent-Vault/`. k8s pod: `Loom-Vault` symlink → same path. Never assume a universal vault path.
- **Webhook notification body reads up to 2,000 chars.** The watchdog includes a preview of the first 2,000 characters of any new file. For files longer than ~300 lines, the preview will be incomplete. If a notification body looks truncated (cuts off mid-sentence), first check your LOCAL vault — the file may have rsynced to you. If not, SSH to the machine that has the vault to read the full file. If the remote host is unreachable, check session history for prior context and re-deliver via **Discord #agent-round-table** (tagging the agent's bot ID) or **Agent-Share/broadcast/** as a fallback.
- **Webhook secrets are truncated in `config.yaml`** — the gateway's `webhook.secret` is its OWN inbound validation secret, not the per-route secret. Per-route secrets live in `~/.hermes/webhook_subscriptions.json`. To get the real secret for a named route:
  ```bash
  python3 -c "import json; d=json.load(open('$HOME/.hermes/webhook_subscriptions.json')); print(d['<route-name>']['secret'])"
  ```
  On a remote host: `ssh <host> "python3 -c \"import json; d=json.load(open('/home/earchibald/.hermes/webhook_subscriptions.json')); print(d['agent-argus']['secret'])\""`. If lost, delete and recreate the route.
- **⚠️ Webhook secrets must be COPIED VERBATIM between agents.** Secrets are currently hardcoded in each agent's `vault-watchdog.py` script as part of the `WEBHOOKS` dict. When adding a new agent, you must copy the exact secret from an existing agent's watchdog script (`WEBHOOKS[target_agent]['secret']`) into the new agent's script. DO NOT:
  - Guess, regenerate, or derive a secret from a known pattern
  - Pull it from `config.yaml` (that's the gateway's inbound secret, not the per-route secret)
  - Use a different secret for the same route (the gateway verifies HMAC-SHA256 against its subscription — mismatches cause silent rejections with `{"status": "ignored"}`)
  The canonical source for any per-route secret is the receiving agent's `~/.hermes/webhook_subscriptions.json`. The secret in the watchdog script's `WEBHOOKS` dict is a local copy of that upstream value.
- **no_agent=true + silent script = no delivery.** The watchdog MUST produce stdout output for anything to be delivered. Empty stdout = cron treats it as "nothing to report" and does nothing.
- **Session-based agents can't receive webhooks reliably.** Argus on macOS doesn't have a 24/7 gateway. Its webhook works only when actively in a session. Design notification flow so always-on agents (Hermes, Loom) notify session-based agents via vault inbox, not webhooks.
- **Event_type field must be exactly right.** The gateway checks `payload.get("event_type", "")`. Using `"event"` instead returns `{"status": "ignored"}`.
- **VM IPs change on DHCP.** Use DNS names (nuc-1.local) over IPs where possible. For k8s LoadBalancer, the IP is stable as long as MetalLB pool isn't changed.
- **Watchdog state includes all .md files.** Rename a file → it appears as new. Edit an existing file → checksum changes → re-notifies. This is intentional — edits should be re-detected.
- **MetalLB L2Advertisement needs explicit pool selector.** An L2Advertisement with no `ipAddressPools` selector does nothing. Must patch to select the pool:
  ```bash
  microk8s kubectl patch l2advertisement -n metallb-system example \
    --type=merge -p '{"spec":{"ipAddressPools":["cheap"]}}'
  ```
- **Hermes cron on remote machine.** `hermes cron create` over SSH requires `hermes` in PATH. May need to source the venv: `export PATH="$HOME/.local/bin:$HOME/.hermes/venv/bin:$PATH"`.
- **State file format inconsistency.** Both watchdog variants must track the same sections (`inbox/argus`, `inbox/hermes`, `inbox/loom`, `broadcast`, `pool`) or the test harness will report false failures.
- **Test harness URL must target the OTHER agent, not self.** A webhook test URL built from the running agent's `detect_agent()` attributes (e.g., `agent['host_ip']`) builds a self-referential loopback, not a cross-machine test. Hardcode the TARGET's IP. See `references/test-harness-design.md`.
- **Gateway state assumptions bite you.** Don't assert "the gateway is down" without checking — `curl -s http://localhost:8644/` takes 0.2s and prevents wrong claims. The CLI session and gateway are separate processes. Running `hermes` at the command line does NOT start the gateway's webhook server — that requires `hermes gateway run` or `hermes gateway start`. Check before declaring.
- **`nuc-1.local` (mDNS) does NOT resolve inside k8s pods.** K8s uses cluster DNS, not mDNS. When Loom needs to reach Hermes's webhook on the host, use the host's LAN IP (192.168.1.195) not `nuc-1.local`. Exception: pods with `hostNetwork: true` can resolve mDNS, but by default they can't.
- **Bash heredocs mangle Python quotes in f-strings.** When writing a Python script with `cat > file << 'EOF'` inside `kubectl exec`, single-quote delimiters in f-string dict keys (`f\"...{item['file']}...\"`) get stripped. The result is `item[file]` instead of `item['file']` → `NameError`. **Fix:** Always use `kubectl cp` from a local file, or base64-encode the script and pipe `kubectl exec ... bash -c 'base64 -d > path'`.
- **⚠️ CRITICAL — Discord @mentions MUST use bot IDs, not names.** Bots only see messages that explicitly `@mention` them. A bare name like `@Hermes` is invisible to the bot. ALWAYS use `<@BOT_ID>` syntax: Hermes → `<@1502772996606263397>`, Loom → `<@1503436035693215774>`, Argus → `<@1503266917798903901>`. This rule applies to every Discord message sent TO another agent — whether manually, via cron, or via watchdog. No exceptions.
- **⚠️ CRITICAL — You cannot read Discord channel history.** The `send_message` tool sends messages; it does NOT fetch past messages. Even if the bot has Read Message History permission, there is no tool to retrieve channel history. If you need to know what agents posted in `#agent-round-table`, ask the user to paste it, or ask the agents to write their findings to your vault inbox. Do NOT tell the user you can read channel history — you cannot.
- **IP address substitution ordering bug.** When sanitizing documents by replacing real IPs with placeholders, always replace LONGER/MORE-SPECIFIC strings before shorter ones. If you replace `192.168.1.1` (gateway) before `192.168.1.180` (nuc-2), the result is `<gateway-ip>80` — a corrupted placeholder. Order: replace the most specific IPs first (`192.168.1.201`, `192.168.1.195`, `192.168.1.192`, `192.168.1.184`, `192.168.1.180`, `192.168.1.104`) then the subnet gateway (`192.168.1.1`) last.
- **Obsolete webhook routes should be deleted.** When an agent's role changes or a predecessor is replaced (e.g., "homelab" → Loom), its old webhook route (`agent-homelab`) becomes dead weight. Zero events, log-only delivery. Remove with:
  ```bash
  hermes webhook remove <route-name>
  ```
  Leaving stale routes is harmless but clutters diagnostics.
- **When the test count differs between agents, don't explain it away — fix it.** If Argus has 23 tests and Hermes has 25, the root cause is probably asymmetric test inclusion (e.g., Argus doesn't test the reverse webhook direction because it's defined as a base target + agent-specific extras). Redesign so every agent has the same number of tests. The per-agent-outgoing design in `references/test-harness-design.md` solves this.

---

## Related Files

| File | Location | Purpose |
|------|----------|---------|
| `vault-watchdog.py` | `~/.hermes/scripts/` | Primary watchdog (Argus, macOS) |
| `hermes-watchdog.py` | `~/.hermes/scripts/` | Watchdog variant (deployed to nuc-1) |
| `vault-test.py` | `scripts/vault-test.py` (this skill) | Regression test harness |
| `vault-test.py` | `Agent-Share/vault-test.py` | Shared copy for all agents |
| `Agent-Share/inter-agent-communication-audit.md` | Vault | Full architecture doc |