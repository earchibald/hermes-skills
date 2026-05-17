#!/usr/bin/env python3
"""
Copy-paste-ready durable HTTP server for interactive reports (v2).

FIXED v2: Removed self.server.shutdown() which killed ALL sibling server
processes on the same machine when one got a form submission.

Features:
- Auto-namespacing (NS from agent + session)
- Port scanning (8899-8950)
- Page serving from PAGES dict
- POST /submit handler with JSON save + /last-response polling
- CORS headers, confirmation page
- Server stays alive for repeated submissions (no self-termination)
- /last-response endpoint for agent-side polling

Updates from v1:
  - No self.server.shutdown()
  - Response directory /tmp/{NS}_responses/ instead of single file
  - /last-response JSON endpoint for polling
  - Wider port range (8899-8950) for sibling agent collision reduction
  - Port can be pinned to a specific value outside the shared range

Replace PAGES dict with your HTML file paths. Run from /tmp.
"""
import json, os, socket, socketserver, time
from http import server
from urllib.parse import urlparse

# ── Namespace ──────────────────────────────────────────────────────────
AGENT = os.environ.get("HERMES_AGENT_NAME", "argus").lower().replace(" ", "-")
SESSION = (os.environ.get("HERMES_SESSION_ID") or str(int(time.time())))[:12]
NS = "ir_{}_{}".format(AGENT, SESSION)
RESPONSE_DIR = "/tmp/{}_responses".format(NS)
os.makedirs(RESPONSE_DIR, exist_ok=True)
LATEST_RESPONSE = os.path.join(RESPONSE_DIR, "latest.json")

# ── Port scan (8899-8950) ──────────────────────────────────────────────
# For high-reliability sessions, PIN to a port outside the shared range:
#   PORT = 9001  # uncomment to pin, skip scanning
PORT = 8899
for try_port in range(8899, 8951):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1)
    try:
        if s.connect_ex(("127.0.0.1", try_port)) != 0:
            PORT = try_port
            break
    finally:
        s.close()

# Map URL paths to HTML files
PAGES = {"/": "/tmp/{}_page.html".format(NS)}

# Track metrics (optional)
pvs = 0
SESSION_START = time.time()

SUB_HTML = b"<html><body style='background:#0d1117;color:#e6edf3;" \
    b"font-family:sans-serif;text-align:center;padding:3rem'>" \
    b"<h1 style='color:#3fb950'>Sent</h1>" \
    b"<p>Response delivered. You can submit again or close this tab.</p>" \
    b"<p style='color:#8b949e;font-size:.8rem'>Server stays alive - submit again anytime.</p>" \
    b"</body></html>"


class Handler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        global pvs
        path = urlparse(self.path).path.rstrip("/") or "/"

        if path in PAGES:
            pvs += 1
            self._serve_file(PAGES[path], "text/html")
        elif path == "/submitted":
            self._send(200, SUB_HTML, "text/html; charset=utf-8")
        elif path == "/last-response":
            self._send_json(200, self._get_latest())
        elif path == "/session-status":
            elapsed = int(time.time() - SESSION_START)
            self._send_json(200, {
                "pages_served": pvs,
                "elapsed": "{}m{}s".format(elapsed // 60, elapsed % 60),
                "uptime_seconds": elapsed,
                "ns": NS,
                "port": PORT,
            })
        elif path == "/health":
            self._send_json(200, {"status": "ok", "ns": NS, "port": PORT})
        else:
            self._send(404, b"Not found", "text/plain")

    def do_POST(self):
        if urlparse(self.path).path == "/submit":
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len).decode()
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                data = {"raw": body}

            data["ns"] = NS
            data["received_at"] = time.time()

            # Save as timestamped file + latest
            ts = int(time.time() * 1000)
            with open(os.path.join(RESPONSE_DIR, "{}.json".format(ts)), "w") as f:
                json.dump(data, f, indent=2)
            with open(LATEST_RESPONSE, "w") as f:
                json.dump(data, f, indent=2)

            self._send_json(200, {"ok": True, "redirect": "/submitted"})
            # NO self.server.shutdown() -- server stays alive.
            # Previously this killed ALL sibling report servers.
        else:
            self._send(404, b"Not found", "text/plain")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors_headers()
        self.end_headers()

    def _serve_file(self, path, mime):
        try:
            with open(path, "rb") as f:
                self.send_response(200)
                self.send_header("Content-Type", mime + "; charset=utf-8")
                self._cors_headers()
                self.end_headers()
                self.wfile.write(f.read())
        except FileNotFoundError:
            self._send(404, b"File not found", "text/plain")

    def _send(self, status, body, mime="text/html; charset=utf-8"):
        self.send_response(status)
        self.send_header("Content-Type", mime)
        self._cors_headers()
        self.end_headers()
        self.wfile.write(body if isinstance(body, bytes) else body.encode())

    def _send_json(self, status, data):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self._cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def _cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _get_latest(self):
        if os.path.exists(LATEST_RESPONSE):
            with open(LATEST_RESPONSE) as f:
                return json.load(f)
        return {"submitted": False}

    def log_message(self, *a):
        pass


class ReusableServer(socketserver.TCPServer):
    allow_reuse_address = True


if __name__ == "__main__":
    import os
    for f in os.listdir(RESPONSE_DIR):
        os.remove(os.path.join(RESPONSE_DIR, f))
    httpd = ReusableServer(("", PORT), Handler)
    print("ir_ready ns={} port={}".format(NS, PORT), flush=True)
    print("response_dir={}".format(RESPONSE_DIR), flush=True)
    httpd.serve_forever()
