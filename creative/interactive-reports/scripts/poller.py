#!/usr/bin/env python3
"""Poll an interactive-report server for new form submissions.

Usage: python3 poller.py <port> [timeout_seconds] [last_received_at]

Exits 0 when a NEW submission arrives, printing the submission JSON to stdout.
Exits 1 on timeout.

"New submission" = the /last-response payload is not the {"submitted": false}
sentinel AND carries a server-stamped `received_at`. Any submission counts —
form posts, quick-action buttons, freeform messages — not only ones with an
`action` key (the old behavior silently ignored everything else).

`last_received_at` (optional float): only fire for submissions strictly newer
than this. Pass the `received_at` of the last submission you processed so a
restarted poller does not instantly re-fire on a stale latest.json.
"""
import json, sys, time, urllib.request

PORT = sys.argv[1] if len(sys.argv) > 1 else "9100"
TIMEOUT_S = int(sys.argv[2]) if len(sys.argv) > 2 else 240
SINCE = float(sys.argv[3]) if len(sys.argv) > 3 else None

URL = "http://localhost:{}/last-response".format(PORT)
attempts = max(1, TIMEOUT_S // 2)  # poll every 2 seconds

for _ in range(attempts):
    try:
        resp = urllib.request.urlopen(URL, timeout=3).read().decode()
        data = json.loads(resp)
        # Sentinel {"submitted": false} has no received_at; real submissions do.
        received_at = data.get("received_at")
        is_new = (
            data.get("submitted") is not False
            and received_at is not None
            and (SINCE is None or float(received_at) > SINCE)
        )
        if is_new:
            print(json.dumps(data))
            sys.exit(0)
    except Exception:
        pass
    time.sleep(2)

print("TIMEOUT")
sys.exit(1)
