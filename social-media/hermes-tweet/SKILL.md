---
name: hermes-tweet
description: Use when Hermes Agent needs a native X/Twitter plugin for tweet search, replies, users, followers, monitors, DMs, and gated account actions.
version: 0.1.6
author: Xquik
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [hermes-agent, hermes-plugin, xquik, twitter, x, social-media, automation]
    homepage: https://docs.xquik.com/guides/hermes-tweet
    repository: https://github.com/Xquik-dev/hermes-tweet
---

# Hermes Tweet

## Overview

Hermes Tweet is a native Hermes Agent X/Twitter plugin for Xquik automation. Use
it when the agent needs to scrape/search tweets, search Twitter/X, read tweet
replies, look up users, monitor tweets, export followers, post tweets/replies,
send DMs, or automate X actions from a Hermes session.

The plugin keeps discovery, reads, and account actions separate:

- `tweet_explore` searches the bundled endpoint catalog and does not need an API key.
- `tweet_read` calls catalog-listed read-only endpoints after `XQUIK_API_KEY` is set.
- `tweet_action` handles private reads and write-like account actions only when actions are enabled.

## When to Use

- Use for X/Twitter research, trend checks, public tweet search, reply reading,
  user lookup, follower export, and monitor planning.
- Use for controlled posting, replies, DMs, follows, webhooks, monitor changes,
  extraction jobs, and giveaway draws only after the user approves the exact
  operation.
- Do not use when the user only needs a generic social media scheduler or an
  official X API OAuth workflow.

## Install

Recommended Hermes plugin install:

```bash
hermes plugins install Xquik-dev/hermes-tweet --enable
```

If the plugin was installed from PyPI into an existing Hermes environment:

```bash
uv pip install --python ~/.hermes/hermes-agent/venv/bin/python hermes-tweet
hermes plugins enable hermes-tweet
```

Hermes prompts for `XQUIK_API_KEY` during interactive installs. For
non-interactive installs, set `XQUIK_API_KEY` in the Hermes runtime environment
or `~/.hermes/.env`, then reload or restart active Hermes sessions before using
`tweet_read`.

Actions stay disabled unless `HERMES_TWEET_ENABLE_ACTIONS=true`.

## Workflow

1. Call `tweet_explore` first with a short query such as `tweet search`,
   `user lookup`, `read replies`, `export followers`, or `post tweet`.
2. Choose a concrete `/api/v1/...` path from the returned catalog.
3. Use `tweet_read` for public read-only endpoints.
4. Use `tweet_action` only for writes, private reads, monitors, webhooks,
   extraction jobs, draws, or account actions after stating the endpoint,
   payload, and reason to the user.
5. Keep `HERMES_TWEET_ENABLE_ACTIONS=false` for unattended cron or gateway
   sessions unless the workflow has an explicit approval step.

## Safety Rules

- Never ask for or reveal API keys, signing keys, passwords, cookies, or TOTP secrets.
- Never place credentials in tool arguments, chat, examples, logs, or issues.
- Do not guess endpoint paths. Use only catalog-listed `/api/v1/...` endpoints.
- Do not use account connection, re-authentication, API key, billing,
  credit top-up, or support-ticket endpoints.
- Do not retry writes through alternate routes after a policy, auth, or account
  state error.

## Examples

Search tweets:

```json
{"query":"tweet search","method":"GET"}
```

Then call `tweet_read` with a catalog path such as:

```json
{"path":"/api/v1/x/tweets/search","query":{"q":"AI agents","limit":25}}
```

Read replies:

```json
{"query":"read tweet replies","method":"GET"}
```

Post a tweet only after user approval:

```json
{"query":"post tweet","include_actions":true}
```

Then call `tweet_action` with the approved endpoint and payload.

## Verification Checklist

- [ ] `hermes plugins enable hermes-tweet` succeeds.
- [ ] `hermes tools list` shows the `hermes-tweet` toolset.
- [ ] `tweet_explore` is available without `XQUIK_API_KEY`.
- [ ] `tweet_read` works after `XQUIK_API_KEY` is configured and Hermes is reloaded.
- [ ] `tweet_action` stays hidden or disabled unless `HERMES_TWEET_ENABLE_ACTIONS=true`.
