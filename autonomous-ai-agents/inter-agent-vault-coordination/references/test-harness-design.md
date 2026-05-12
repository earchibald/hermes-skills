# Test Harness Design

Captures the per-agent-outgoing webhook test pattern designed during the 2026-05-11 session.

## Principle: Each Agent Tests Its Own Outgoing

**Do NOT test incoming webhooks.** A test that posts to the agent's own incoming route tests nothing useful — it only proves the server is running, which is trivially true if the agent is online.

**Do NOT test on another agent's behalf.** A test named `argus→hermes` that Hermes runs is confusing — Hermes is not Argus, and the architectural label obscures who's actually sending the POST.

**Instead:** Each agent lists the OTHER agents it can reach and tests posting to THEM.

| Agent | Tests: can reach → | By posting to |
|-------|-------------------|---------------|
| Argus | hermes, loom | Hermes's `agent-argus`, Loom's `vault-cron` |
| Hermes | argus, loom | Argus's `vault-cron`, Loom's `vault-cron` |
| Loom | argus, hermes | Argus's `vault-cron`, Hermes's `agent-argus` |

Every agent gets **exactly 2 webhook reachability tests** — symmetric count, no confusion about whose perspective.

## Why This Design Won Out

1. **Clarity.** A test named `loom → hermes` is unambiguous — Loom is running it, Hermes is the target.
2. **Symmetric counts.** Every agent has exactly 2 webhook tests. No "why does Hermes have 25 and I have 23?" confusion.
3. **No self-tests.** Agents never test their own webhook route (pointless).
4. **No proxy tests.** Agents never test another agent's outgoing capability (can't be measured remotely anyway).

## Implementation

In `vault-test.py`, the webhook targets section:

```python
if me == "argus":
    webhook_targets = {
        "argus → hermes": {"url": "http://nuc-1.local:8644/webhooks/agent-argus", ...},
        "argus → loom": {"url": "http://192.168.1.201:8644/webhooks/vault-cron", ...},
    }
elif me == "hermes":
    webhook_targets = {
        "hermes → argus": {"url": "http://192.168.1.104:8644/webhooks/vault-cron", ...},
        "hermes → loom": {"url": "http://192.168.1.201:8644/webhooks/vault-cron", ...},
    }
elif me == "loom":
    webhook_targets = {
        "loom → argus": {"url": "http://192.168.1.104:8644/webhooks/vault-cron", ...},
        "loom → hermes": {"url": "http://192.168.1.195:8644/webhooks/agent-argus", ...},
    }
```

## Common Bug: Self-Referential Webhook URLs

During this session, the Hermes → Argus webhook test failed because the URL was built from `agent['host_ip']` — which for Hermes resolves to its own Tailscale IP (100.105.253.43). The URL became `http://100.105.253.43:8644/webhooks/vault-cron` — Hermes posting to itself.

**Fix:** Hardcode the TARGET's IP, never use the running agent's attributes for the URL.
