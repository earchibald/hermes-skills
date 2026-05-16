#!/usr/bin/env python3
"""
Copy-paste-ready self-terminating HTTP server for interactive reports.

Features: auto-namespacing (NS from agent + session), port scanning
(8899-8920), page serving, POST /submit handler with JSON save + stdout
output, CORS headers, confirmation page, and self-termination on first
form submission via threading shutdown.

Replace PAGES dict with your HTML file paths. Run from /tmp.
"""

import json
import os
import socket
import socketserver
import threading
import time
from http import server
from urllib.parse import urlparse


# ── Namespace ──────────────────────────────────────────────────────────
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

# Map URL paths to HTML files
PAGES = {
    "/": f"/tmp/{NS}_page.html",       # primary decision page
}

# Track metrics
pvs = 0        # page views served
SESSION_START = time.time()


CONFIRM_HTML = (
    "<!DOCTYPE html><html lang='en'><head>"
    "<meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1.0'>"
    "<title>Response Received</title>"
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


class Handler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        global pvs
        path = urlparse(self.path).path.rstrip("/") or "/"

        if path in PAGES:
            pvs += 1
            self._serve_file(PAGES[path], "text/html")
        elif path == "/submitted":
            self._send(200, CONFIRM_HTML.encode(), "text/html; charset=utf-8")
        elif path == "/session-status":
            elapsed = int(time.time() - SESSION_START)
            status = {
                "pages_served": pvs,
                "elapsed": f"{elapsed//60}m{elapsed%60}s",
                "uptime_seconds": elapsed,
                "ns": NS,
                "port": PORT,
            }
            self._send_json(200, status)
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

            # Print to stdout for notify_on_complete
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
        pass


class ReusableServer(socketserver.TCPServer):
    allow_reuse_address = True
    allow_reuse_port = True


if __name__ == "__main__":
    if os.path.exists(RESPONSE_FILE):
        os.remove(RESPONSE_FILE)
    httpd = ReusableServer(("", PORT), Handler)
    print(f"ir_ready ns={NS} port={PORT}", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.shutdown()
