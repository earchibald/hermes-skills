#!/usr/bin/env python3
"""
Copy-paste-ready HTTP server for dual-channel interactive reports.
Features multi-page routing, form submission (POST /submit), live
session-status endpoint, page view / form count tracking, confirmation
page with navigation, and quiet logging.

Replace PAGES dict with your HTML file paths. Run from /tmp.
"""
import json
import os
import socketserver
import time
from http import server
from urllib.parse import urlparse, parse_qs

PORT = 8899
RESPONSE_FILE = "/tmp/memory_report_response.json"
SESSION_START = time.time()

# Map URL paths to HTML files
PAGES = {
    "/":     "/tmp/memory_report.html",       # primary decision page
    "/wireframe": "/tmp/deployment_wireframe.html",
    "/session":   "/tmp/session_live.html",    # auto-polling live page
}

# Track metrics
pvs = 0        # page views served
form_count = 0 # form submissions received
chat_turns = 0 # update via /update-status
last_agent_msg = "Session started."

CONFIRM_HTML = """<!DOCTYPE html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Response Received</title>
<style>
body{font-family:system-ui,-apple-system,sans-serif;max-width:600px;margin:3rem auto;padding:0 1rem;text-align:center;background:#0d1117;color:#e6edf3}
.card{padding:2rem;border-radius:12px;background:#161b22;border:1px solid #30363d}
h1{color:#3fb950;font-size:1.5rem}
p{color:#8b949e;margin:0.75rem 0}
.btn{display:inline-block;margin-top:1rem;padding:0.6rem 1.25rem;background:#21262d;color:#e6edf3;text-decoration:none;border-radius:6px;border:1px solid #30363d;font-size:0.9rem}
.btn:hover{background:#30363d}
small{display:block;margin-top:1.5rem;color:#6e7681;font-size:0.8rem}
.nav{display:flex;gap:0.5rem;justify-content:center;margin-top:0.75rem}
</style></head><body>
<div class="card">
<h1>✓ Response Sent</h1>
<p>Your input has been delivered to the agent in the chat session.</p>
<div class="nav">
<a href="/" class="btn">Decision</a>
<a href="/wireframe" class="btn">Wireframe</a>
<a href="/session" class="btn">Live Session</a>
</div>
<small>Close this tab when done, or submit again to update your response.</small>
</div></body></html>"""


class Handler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        global pvs
        path = urlparse(self.path).path.rstrip("/") or "/"

        if path in PAGES:
            pvs += 1
            self._serve_file(PAGES[path], "text/html")
        elif path == "/submitted":
            self._serve_text(CONFIRM_HTML, "text/html")
        elif path == "/session-status":
            elapsed = int(time.time() - SESSION_START)
            status = {
                "pages_served": pvs,
                "form_responses": form_count,
                "chat_turns": chat_turns,
                "elapsed": f"{elapsed//60}m{elapsed%60}s",
                "uptime_seconds": elapsed,
                "last_agent_message": last_agent_msg,
            }
            self._serve_json(status)
        else:
            self._serve_text("404", "text/plain", 404)

    def do_POST(self):
        global form_count, chat_turns, last_agent_msg
        path = urlparse(self.path).path

        if path == "/submit":
            form_count += 1
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len).decode()
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                data = parse_qs(body)
                data = {k: v[0] if len(v) == 1 else v for k, v in data.items()}
            data["status"] = "received"
            data["received_at"] = time.time()
            with open(RESPONSE_FILE, "w") as f:
                json.dump(data, f, indent=2)
            self._serve_json({"ok": True, "status": "received"})

        elif path == "/update-status":
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len).decode()
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                data = {}
            if "chat_turns" in data:
                chat_turns = data["chat_turns"]
            if "last_agent_msg" in data:
                last_agent_msg = data["last_agent_msg"]
            self._serve_json({"ok": True})

        else:
            self._serve_text("404", "text/plain", 404)

    def _serve_file(self, path, mime):
        try:
            with open(path, "rb") as f:
                self.send_response(200)
                self.send_header("Content-Type", mime + "; charset=utf-8")
                self.end_headers()
                self.wfile.write(f.read())
        except FileNotFoundError:
            self._serve_text("File not found", "text/plain", 404)

    def _serve_text(self, text, mime, status=200):
        self.send_response(status)
        self.send_header("Content-Type", mime + "; charset=utf-8")
        self.end_headers()
        self.wfile.write(text.encode())

    def _serve_json(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def log_message(self, fmt, *args):
        pass


class ReusableServer(socketserver.TCPServer):
    allow_reuse_address = True
    allow_reuse_port = True


if __name__ == "__main__":
    if os.path.exists(RESPONSE_FILE):
        os.remove(RESPONSE_FILE)
    httpd = ReusableServer(("", PORT), Handler)
    webbrowser.open(f"http://localhost:{PORT}/")
    print(f"Serving on http://localhost:{PORT}/")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.shutdown()
