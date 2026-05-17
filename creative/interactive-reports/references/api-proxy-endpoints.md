# Custom API Proxy Endpoints

When your interactive report needs live data from an external API (e.g. searching
Hindsight memory from a recall form), add custom POST handlers to the server.

## Pattern

Add a `do_POST` handler that proxies to the target API. The server must be a
**custom server** (not the mini-server template) — you write it from scratch or
extend the template.

```python
def do_POST(self):
    path = urlparse(self.path).path

    # Existing /submit handler for form submissions
    if path == "/submit":
        l = int(self.headers.get("Content-Length", 0))
        d = json.loads(self.rfile.read(l).decode())
        d["ns"] = NS
        with open(RF, "w") as f:
            json.dump(d, f, indent=2)
        sys.stdout.write(json.dumps(d) + "\n")
        sys.stdout.flush()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"ok": True}).encode())
        threading.Thread(target=self.server.shutdown, daemon=True).start()

    # Custom API proxy endpoint
    elif path == "/recall":
        l = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(l).decode())

        # Forward to external API
        proxy_payload = json.dumps({"query": body.get("query", ""), "limit": 5}).encode()
        try:
            req = urllib.request.Request(
                "http://127.0.0.1:8542/v1/default/banks/hermes/memories/recall",
                method="POST", data=proxy_payload,
                headers={"Content-Type": "application/json"}
            )
            resp = urllib.request.urlopen(req, timeout=10)
            api_data = json.loads(resp.read())

            # Transform to client-expected format
            results = []
            for item in api_data.get("results", []):
                results.append({
                    "content": item.get("text", ""),
                    "context": item.get("context", ""),
                    "score": item.get("score", 0),
                })

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True, "results": results}).encode())

        except urllib.error.HTTPError as e:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "ok": False,
                "error": f"API error {e.code}: {e.read().decode()[:200]}"
            }).encode())
        except Exception as e:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"ok": False, "error": str(e)}).encode())
    else:
        self.send_response(404)
        self.end_headers()
```

## Client-Side (HTML)

```javascript
async function proxyCall() {
  const query = document.getElementById('input-field').value;
  const result = document.getElementById('result-area');

  const resp = await fetch('/recall', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query })
  });
  const data = await resp.json();

  if (data.ok && data.results.length > 0) {
    result.innerHTML = data.results.map(r =>
      `<div>${r.content}</div>`
    ).join('');
  } else {
    result.textContent = 'No results.';
  }
}
```

## Pitfalls

- **API response fields may differ from what the client expects.** The recall
  endpoint returns `text` not `content`, and the results key is `results` not
  `memories`. Always check the actual response format — don't assume field names
  match your client code. Log the raw response during development.
- **CORS headers are required.** The browser's `fetch()` from a served page to
  a different port/endpoint triggers CORS preflight. Add `do_OPTIONS` handler
  and set `Access-Control-Allow-Origin: *` on every response.
- **Error handling is critical.** A failed proxy call should return a structured
  JSON error (not a 500) so the client JS can display it gracefully.
- **Timeouts matter.** The proxy waits the sum of network latency + API response
  time. Set a reasonable `timeout` on the `urllib.request.urlopen` call (10s is
  generous for most APIs) so slow upstream calls don't hang the browser request.
- **The proxy runs in the same process as the report server.** If the upstream
  API is slow or hangs, ALL HTTP requests to the server (including form submissions)
  are blocked until the proxy call completes. For high-latency APIs, consider
  pre-fetching data at server startup or using a thread pool.
