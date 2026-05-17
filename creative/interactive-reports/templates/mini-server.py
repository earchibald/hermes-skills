#!/usr/bin/env python3
"""Durable report server — does NOT self-terminate.

FIXED v2: Removed self.server.shutdown() which killed ALL sibling server
processes on the same machine when one got a form submission.

On startup:
  - Computes NS from AGENT + SESSION
  - Scans ports 9100-9199 for first free
  - Emits: ir_ready ns={NS} port={PORT}
  - Creates /tmp/{NS}_responses/ directory

On POST /submit:
  - Saves JSON to /tmp/{NS}_responses/{timestamp}.json
  - Writes latest to /tmp/{NS}_responses/latest.json
  - Returns 200 — server stays alive

Agent polls /last-response to detect new submissions.
"""
import json, os, socketserver, sys, time, socket
from http import server
from urllib.parse import urlparse

AGENT = os.environ.get("HERMES_AGENT_NAME", "argus").lower().replace(" ", "-")
SESSION = (os.environ.get("HERMES_SESSION_ID") or str(int(time.time())))[:12]
NS = "ir_{}_{}".format(AGENT, SESSION)
RESPONSE_DIR = "/tmp/{}_responses".format(NS)
os.makedirs(RESPONSE_DIR, exist_ok=True)
LATEST_RESPONSE = os.path.join(RESPONSE_DIR, "latest.json")

# Port scanning (dedicated range to avoid sibling agent races)
PORT = 9100
for p in range(9100, 9201):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1)
    try:
        if s.connect_ex(("127.0.0.1", p)) != 0:
            PORT = p; break
    finally:
        s.close()

# ── EDIT THIS DICT to point at your HTML file(s) ───────────────────────
PAGES = {"/": "/tmp/{}_page.html".format(NS)}
# ── OPTIONAL: set STATIC_DIR to serve static files (images, CSS, etc) ──
STATIC_DIR = None
# ────────────────────────────────────────────────────────────────────────

SUB_HTML = b"<html><body style='background:#0d1117;color:#e6edf3;" \
    b"font-family:sans-serif;text-align:center;padding:3rem'>" \
    b"<h1 style='color:#3fb950'>Sent</h1>" \
    b"<p>Response delivered. You can submit again or close this tab.</p>" \
    b"<p style='color:#8b949e;font-size:.8rem'>Server stays alive - submit again anytime.</p>" \
    b"</body></html>"

class H(server.BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path.rstrip("/") or "/"
        if path in PAGES:
            with open(PAGES[path]) as f:
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(f.read().encode())
        elif path == "/submitted":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(SUB_HTML)
        elif path == "/last-response":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            if os.path.exists(LATEST_RESPONSE):
                with open(LATEST_RESPONSE) as f:
                    self.wfile.write(f.read().encode())
            else:
                self.wfile.write(json.dumps({"submitted": False}).encode())
        elif STATIC_DIR and path.startswith("/") and not path.startswith("//"):
            filename = path.lstrip("/")
            filepath = os.path.join(STATIC_DIR, filename)
            if os.path.isfile(filepath):
                ext = os.path.splitext(filename)[1].lower()
                mime = {"html":"text/html","css":"text/css","js":"application/javascript",
                        "png":"image/png","jpg":"image/jpeg","jpeg":"image/jpeg",
                        "gif":"image/gif","svg":"image/svg+xml","ico":"image/x-icon",
                        "json":"application/json","txt":"text/plain","md":"text/markdown",
                        "woff2":"font/woff2"}.get(ext, "application/octet-stream")
                with open(filepath, "rb") as f:
                    self.send_response(200)
                    self.send_header("Content-Type", mime)
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    self.wfile.write(f.read())
            else:
                self.send_response(404); self.end_headers()
        else:
            self.send_response(404); self.end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        if urlparse(self.path).path == "/submit":
            l = int(self.headers.get("Content-Length", 0))
            d = json.loads(self.rfile.read(l).decode())
            d["ns"] = NS
            d["received_at"] = time.time()
            ts = int(time.time() * 1000)
            with open(os.path.join(RESPONSE_DIR, "{}.json".format(ts)), "w") as f:
                json.dump(d, f, indent=2)
            with open(LATEST_RESPONSE, "w") as f:
                json.dump(d, f, indent=2)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True}).encode())
            # NO self.server.shutdown() -- server stays alive.
            # Previously this killed ALL sibling report servers on the same
            # machine. Fixed in v2 -- kanban task t_7e288107.
        else:
            self.send_response(404); self.end_headers()

    def log_message(self, *a): pass

if __name__ == "__main__":
    for f in os.listdir(RESPONSE_DIR):
        os.remove(os.path.join(RESPONSE_DIR, f))
    srv = type("S", (socketserver.TCPServer,), {"allow_reuse_address": True})(("", PORT), H)
    sys.stdout.write("ir_ready ns={} port={}\n".format(NS, PORT))
    sys.stdout.write("response_dir={}\n".format(RESPONSE_DIR))
    sys.stdout.flush()
    srv.serve_forever()
