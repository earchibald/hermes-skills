# NS Drift on Server Restart

## Problem

The mini-server computes NS from `HERMES_AGENT_NAME` + `HERMES_SESSION_ID` (or a timestamp fallback) on every startup. When the agent kills and restarts the server mid-session, the `HERMES_SESSION_ID` may have changed or the timestamp fallback produces a different NS. The server looks for HTML files at `/tmp/{new_NS}_page.html` but the agent wrote them at `/tmp/{old_NS}_page.html` — all pages return 500 errors.

Diagnostic: `FileNotFoundError` on PAGES paths in stderr, `ir_ready ns=ir_argus_YYYYMMDDDIFFERENT port=...` in stdout.

## Fix

Hardcode NS in the server after copying the template:

```python
# In /tmp/{NS}_server.py, change:
NS = "ir_{}_{}".format(AGENT, SESSION)
# to:
NS = "ir_argus_20260517_021"  # fixed for this session
```

The agent picks the NS once when creating pages, and the server must use the same NS. When the server is long-lived, the env-var-based NS computation is fine — it's only on RESTART that it drifts.

## Prevention

Always hardcode NS in the server when using the execute_code pattern, since restarts are expected. The env-var computation is fine for one-shot terminal(background=true) launches.
