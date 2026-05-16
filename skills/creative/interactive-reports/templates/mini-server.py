#!/usr/bin/env python3
"""Interactive report server template — copy and customize for each session.

Usage:
  1. Copy this file to /tmp/memory-report-server.py
  2. Update the PAGES dict with your HTML file paths
  3. Customize CONFIRM_HTML if needed
  4. Run: python3 /tmp/memory-report-server.py
  5. Agent opens browser: terminal("open http://localhost:8899/")

NOTE: Do NOT add webbrowser.open to __main__. The agent controls
browser lifecycle explicitly to avoid duplicate tabs on restart.
"""

import json
import os
import socketserver
import time
from http import server
from urllib.parse import urlparse

PORT = 8899
RESPONSE_FILE = "/tmp/memory_report_response.json"
SESSION_START = time.time()

# ── Register your HTML pages here ───────────────────────────────────────
# Add entries: "/route-name": "/path/to/html/file.html"
PAGES = {
    "/":  "/tmp/memory_report.html",
    "/example": "/tmp/example_page.html",
}

# ── Confirmation page (shown after form submission) ──────────────────────
CONFIRM_HTML = """<!DOCTYPE html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Response Received</title>
<style>
body{font-family:system-ui,-apple-system,sans-serif;max-width:600px;margin:3rem auto;padding:0 1rem;text-align:center;background:#0d1117;color:#e6edf3}
.card{padding:2rem;border-radius:12px;background:#161b22;border:1px solid #30363d}
h1{color:#3fb950;font-size:1.5rem}
p{color:#8b949e;margin:0.75rem 0}
.nav{display:flex;gap:0.5rem;justify-content:center;margin-top:0.75rem}
.btn{display:inline-block;margin-top:1rem;padding:0.6rem 1.25rem;background:#21262d;color:#e6edf3;text-decoration:none;border-radius:6px;border:1px solid #30363d;font-size:0.9rem}
.btn:hover{background:#30363d}
small{display:block;margin-top:1.5rem;color:#6e7681;font-size:0.8rem}
</style></head><body>
<div class="card">
<h1>\u2713 Response Sent</h1>
<p>Your input has been delivered to the agent in the chat session.</p>
<div class="nav">
{PAGE_LINKS}
</div>
<small>Close this tab when done, or submit again to update your response.</small>
</div></body></html>"""

# ── Stats tracking ──────────────────────────────────────────────────────
page_views = 0
form_count = 0


class Handler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        global page_views
        path = urlparse(self.path).path.rstrip("/") or "/"

        if path in PAGES:
            page_views += 1
            self._serve_file(PAGES[path], "text/html")
        elif path == "/submitted":
            # Build nav links from registered pages
            links = "".join(
                f'<a href="{r}" class="btn">{n}</a>'
                for r, n in _nav_links()
            )
            html = CONFIRM_HTML.replace("{PAGE_LINKS}", links)
            self._serve_text(html, "text/html")
        elif path == "/session-status":
            elapsed = int(time.time() - SESSION_START)
            status = {
                "pages_served": page_views,
                "form_responses": form_count,
                "elapsed": _fmt_duration(elapsed),
                "uptime_seconds": elapsed,
                "active_decision": "",
            }
            self._serve_json(status)
        else:
            self._serve_text("Not found", "text/plain", 404)

    def do_POST(self):
        global form_count
        if urlparse(self.path).path == "/submit":
            form_count += 1
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len).decode()
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                from urllib.parse import parse_qs
                data = parse_qs(body)
                data = {k: v[0] if len(v) == 1 else v for k, v in data.items()}
            data["status"] = "received"
            data["received_at"] = time.time()
            with open(RESPONSE_FILE, "w") as f:
                json.dump(data, f, indent=2)
            self._serve_json({"ok": True, "status": "received"})
        else:
            self._serve_text("Not found", "text/plain", 404)

    # ── Helpers ─────────────────────────────────────────────────────
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
        pass  # quiet


def _nav_links():
    """Return list of (route, pretty_name) tuples for the registered pages."""
    out = []
    for route in sorted(PAGES):
        name = route.strip("/").replace("-", " ").title() or "Home"
        out.append((route, name))
    return out


def _fmt_duration(seconds):
    if seconds < 60:
        return f"{seconds}s"
    return f"{seconds // 60}m{seconds % 60}s"


class ReusableServer(socketserver.TCPServer):
    allow_reuse_address = True
    allow_reuse_port = True


if __name__ == "__main__":
    # Clean slate
    if os.path.exists(RESPONSE_FILE):
        os.remove(RESPONSE_FILE)

    httpd = ReusableServer(("", PORT), Handler)
    print(f"Serving on http://localhost:{PORT}/")
    print(f"Pages: {', '.join(PAGES)}")
    print("Agent: terminal('open http://localhost:PORT/') to open browser")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.shutdown()
