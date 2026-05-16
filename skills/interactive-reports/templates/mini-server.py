#!/usr/bin/env python3
"""
Generic self-terminating interactive report server.

This template ships with the skill and is NOT rewritten per session.
The agent copies it to /tmp/{NS}_server.py and sets PAGES to point
to the correct HTML file. The server auto-computes its namespace (NS)
from agent name + session ID, scans ports 8899-8920 for a free one,
and self-terminates on first form submission.

Usage (agent does this):
  1. cp templates/mini-server.py /tmp/{NS}_server.py
  2. Edit PAGES in /tmp/{NS}_server.py to point to HTML file(s)
  3. terminal(background=true, notify_on_complete=true,
              command="python3 /tmp/{NS}_server.py")
  4. Read NS + PORT from stdout line: ir_ready ns=... port=...
  5. terminal("open http://localhost:{PORT}/")
  6. On form submit: server saves response, prints JSON to stdout, exits
  7. notify_on_complete fires with submission data

NOTE: Do NOT add webbrowser.open to __main__. The agent controls
browser lifecycle explicitly to avoid duplicate tabs on restart.
"""

import json
import os
import socket
import socketserver
import sys
import threading
import time
from http import server
from urllib.parse import urlparse


# ── Auto-compute namespace ──────────────────────────────────────────────
AGENT = os.environ.get("HERMES_AGENT_NAME", "argus").lower().replace(" ", "-")
SESSION = (os.environ.get("HERMES_SESSION_ID") or str(int(time.time())))[:12]
NS = f"ir_{AGENT}_{SESSION}"

# ── Port scan (8899-8920) ──────────────────────────────────────────────
PORT = 8899
for try_port in range(8899, 8921):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1)
    try:
        if s.connect_ex(("127.0.0.1", try_port)) != 0:
            PORT = try_port
            s.close()
            break
    finally:
        s.close()

# ── Namespaced paths ────────────────────────────────────────────────────
RESPONSE_FILE = f"/tmp/{NS}_response.json"

# ── EDIT THIS: Map routes to your HTML file(s) ──────────────────────────
# Use the namespace for your HTML file: /tmp/{NS}_page.html
PAGES = {
    "/": f"/tmp/{NS}_page.html",
}


class Handler(server.BaseHTTPRequestHandler):
    """HTTP request handler with CORS, file serving, and self-termination."""

    def do_GET(self):
        path = urlparse(self.path).path.rstrip("/") or "/"

        if path in PAGES:
            self._serve_file(PAGES[path], "text/html")
        elif path == "/submitted":
            self._send(200, CONFIRM_HTML.encode(), "text/html; charset=utf-8")
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

            data["status"] = "submitted"
            data["received_at"] = time.time()
            data["agent"] = AGENT
            data["session"] = SESSION

            # Save to response file
            with open(RESPONSE_FILE, "w") as f:
                json.dump(data, f, indent=2)

            # Print JSON to stdout for notify_on_complete
            print(json.dumps(data), flush=True)

            # Respond to client
            self._send_json(200, {"ok": True, "redirect": "/submitted"})

            # Self-terminate after response is sent
            threading.Thread(target=self.server.shutdown, daemon=True).start()
        else:
            self._send(404, b"Not found", "text/plain")

    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(204)
        self._cors_headers()
        self.end_headers()

    # ── Helpers ─────────────────────────────────────────────────────

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

    def log_message(self, *args):
        pass  # quiet


CONFIRM_HTML = (
    "<!DOCTYPE html><html lang='en'><head>"
    "<meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1.0'>"
    "<title>Response Sent</title>"
    "<style>"
    "body{font-family:system-ui,-apple-system,sans-serif;max-width:600px;margin:3rem auto;"
    "padding:0 1rem;text-align:center;background:#0d1117;color:#e6edf3}"
    ".card{padding:2rem;border-radius:12px;background:#161b22;border:1px solid #30363d}"
    "h1{color:#3fb950;font-size:1.5rem}"
    "p{color:#8b949e;margin:0.75rem 0}"
    "small{display:block;margin-top:1.5rem;color:#6e7681;font-size:0.8rem}"
    "</style></head><body>"
    "<div class='card'>"
    "<h1>\u2713 Response Sent</h1>"
    "<p>Your input has been delivered to the agent in the chat session.</p>"
    "<small>Close this tab when done.</small>"
    "</div></body></html>"
)


class ReusableServer(socketserver.TCPServer):
    allow_reuse_address = True
    allow_reuse_port = True


if __name__ == "__main__":
    # Clean slate
    if os.path.exists(RESPONSE_FILE):
        os.remove(RESPONSE_FILE)

    httpd = ReusableServer(("", PORT), Handler)
    # Machine-parseable startup signal
    print(f"ir_ready ns={NS} port={PORT}", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.shutdown()
