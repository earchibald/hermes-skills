# Webhook Delivery Types

Discovered during the `deliver: local` bug fix (2026-05-16). The webhook
gateway platform at `gateway/platforms/webhook.py` validates delivery types
in its `send()` method.

## Valid delivery types

| Type | Behavior |
|---|---|
| `log` | Logs the agent response to gateway.log via `logger.info()` — no external delivery. Use when side effects (kanban task creation, DB writes) are the point. |
| `github_comment` | Posts the agent's response as a GitHub PR/issue comment via the `gh` CLI. Requires `deliver_extra` with `repo` (e.g. `owner/name`) and `pr_number`. |
| Platform names | `telegram`, `discord`, `slack`, `signal`, `sms`, `whatsapp`, `matrix`, `mattermost`, `homeassistant`, `email`, `dingtalk`, `feishu`, `wecom`, `weixin`, `bluebubbles`, `qqbot`, `yuanbao` — deliver via the corresponding gateway adapter. |

## Invalid delivery types

| Type | Why it fails |
|---|---|
| `local` | Not recognized. Produces `WARNING: Unknown deliver type: local` and `ERROR: Fallback send also failed`. Was used in early `webhook_subscriptions.json` configs. |

## Route configuration

Each route in `webhook_subscriptions.json` (or `config.yaml` webhook routes):

```json
{
  "route-name": {
    "events": ["event-type"],
    "secret": "hmac-secret",
    "prompt": "template string with {payload.field}",
    "skills": ["skill-name"],
    "deliver": "log",
    "deliver_extra": {"repo": "owner/name", "pr_number": "{payload.pull_request.number}"},
    "deliver_only": false
  }
}
```

- `deliver_only: true` — skip the agent entirely, deliver the rendered prompt
  directly to the delivery target. Used for push notifications.
- `deliver_extra` — rendered through the same template engine as `prompt`, so
  payload fields like `{payload.pull_request.number}` work.
