---
name: ntfy-notify
description: "Use when sending push notifications via ntfy.sh topics. Sends arbitrary messages with optional title, priority, tags, click URL, and attachments via a single curl call. Also use when the user asks to send a notice, ping, or notification."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [notification, push, ntfy, curl, messaging]
    related_skills: []
---

# Ntfy.sh Notifications

## TL;DR

1. POST to `https://ntfy.sh/<topic>` with body as the message
2. Set headers for title, priority, tags, click URL
3. Topic names are public — anyone who knows the name can subscribe
4. Free tier: no auth needed, no rate limits for reasonable use
5. For private topics: use `ntfy.<your-server>` with auth

```bash
curl -s -X POST "https://ntfy.sh/<topic>" \
  -H "Title: Optional title" \
  -H "Priority: default" \
  -H "Tags: tag1,tag2" \
  -H "Click: https://example.com" \
  -d "Your notification body here"
```

## Overview

ntfy.sh is a simple HTTP-based pub-sub notification service. Send a POST request to a topic URL and any subscriber (phone app, browser, script) receives it as a push notification. No accounts, no setup — just HTTP POST. The Hermes-compatible pattern is a single `curl -X POST` to `https://ntfy.sh/<topic>` with JSON or plain text body.

## When to Use

- User asks to "send me a notification" or "ping me when done"
- Long-running task completes and you want to notify the user
- Cron job produces a summary and needs push delivery
- Any situation where you'd otherwise say "check back later"

**Don't use for:**
- Sensitive data (topic names are public unless self-hosted)
- Large payloads (max ~4KB, use a link for big content)

## API Reference

### Send a message

```
POST https://ntfy.sh/<topic>
Body: Plain text or JSON (any string)
```

### Headers

| Header | Example | Description |
|--------|---------|-------------|
| Title | `Task Complete` | Bold title shown in notification |
| Priority | `min`, `low`, `default`, `high`, `urgent` | Android priority level |
| Tags | `robot,chart` | Emoji or lowercase tag names |
| Click | `https://...` or `obsidian://...` | URL opened when notification tapped |
| Attach | `https://example.com/file.pdf` | Downloadable attachment URL |
| Icon | `https://example.com/icon.png` | Custom notification icon |
| Filename | `report.pdf` | Filename for attachment |
| Delay | `30min` or `1700` (Unix timestamp) | Delayed delivery |
| Markdown | `yes` | Enable markdown in body |
| Actions | `view, Open, https://...` | Action buttons (Android) |

### Priority

- `min` / `1`: No vibration or sound
- `low` / `2`: No vibration, quiet sound
- `default` / `3`: Standard notification
- `high` / `4`: Override DND, vibration + sound
- `urgent` / `5`: Override DND, repeated until acknowledged

### Emoji Tags

Tags support emoji shortcodes: `+1`, `chart_with_upwards_trend`, `robot`, `fire`, `tada`, `warning`, `white_check_mark`, `x`, etc. Separate multiple with commas.

### Topics

- Must be non-empty, alphanumeric + hyphens + underscores
- Public by default — anyone who knows the name can POST and subscribe
- For private: self-host an ntfy server and use basic auth or token auth

## Common Patterns

### Task completion notification

```bash
TOPIC="my-topic"
curl -s -X POST "https://ntfy.sh/$TOPIC" \
  -H "Title: Build Complete" \
  -H "Priority: default" \
  -H "Tags: white_check_mark,robot" \
  -d "Build succeeded. Artifacts at /tmp/build/"
```

### Alert with high priority

```bash
curl -s -X POST "https://ntfy.sh/$TOPIC" \
  -H "Title: ⚠️ Disk Space Low" \
  -H "Priority: high" \
  -H "Tags: warning" \
  -d "Only 5% remaining on /dev/sda1"
```

### Clickable obsidian:// link

```bash
curl -s -X POST "https://ntfy.sh/$TOPIC" \
  -H "Title: Report Ready" \
  -H "Click: obsidian://open?vault=Agent-Vault&file=Projects/report.md" \
  -d "Dashboard audit report saved to vault."
```

## Common Pitfalls

1. **Topic name has spaces** — Must be alphanumeric + hyphens + underscores. No spaces.
2. **Priority values are strings** — `"default"` not `default`, `"high"` not `high`. Integer values also work (`3`, `4`).
3. **Click URL encoding** — Ampersands in click URLs must be escaped. Use `\\u0026` not `&` in JSON curl commands.
4. **Long messages** — Max ~4KB. For longer content, put it in a file and use a click link to reference it.
5. **Tag names case sensitive** — Use lowercase tag names: `chart_with_upwards_trend` not `Chart_With_Upwards_Trend`.

## Verification Checklist

- [ ] Notification received on the subscribed device
- [ ] Title, body, priority, and click URL all render correctly
- [ ] Topic name is correct (no typos or extra characters)
