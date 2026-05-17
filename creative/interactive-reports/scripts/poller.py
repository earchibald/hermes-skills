#!/usr/bin/env python3
"""Poll an interactive-report server for new form submissions.

Usage: python3 poller.py <port> [timeout_seconds]
Exits 0 when a new submission arrives, printing it to stdout.
Exits 1 on timeout.
"""
import json, sys, time, urllib.request, urllib.error

PORT = sys.argv[1] if len(sys.argv) > 1 else "9100"
TIMEOUT_S = int(sys.argv[2]) if len(sys.argv) > 2 else 240

URL = "http://localhost:{}/last-response".format(PORT)
attempts = TIMEOUT_S // 2  # poll every 2 seconds

for i in range(attempts):
    try:
        resp = urllib.request.urlopen(URL, timeout=3).read().decode()
        data = json.loads(resp)
        if data.get("action"):
            print(json.dumps(data))
            sys.exit(0)
    except Exception:
        pass
    time.sleep(2)

print("TIMEOUT")
sys.exit(1)
