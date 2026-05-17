# Static Asset Serving

The default mini-server template only serves pages explicitly registered in the
`PAGES` dict. HTML `<img src="...">` or `<link href="...">` references to
images, CSS files, or JS files on disk will return 404 unless you add routes
for them.

## Option A: Add a static file route (recommended)

Patch the server's `do_GET` to serve files from a directory. Add this branch
before the final `else: self._send(404, ...)`:

```python
# ── Static assets directory ────────────────────────────────────────────
STATIC_DIR = os.path.expanduser("~/Desktop/screenshots")  # or your dir

# In do_GET, after PAGES and special routes, add:
elif path.startswith("/static/") and ".." not in path:
    # Safe filename extraction — blocks directory traversal
    rel_path = path[len("/static/"):]
    file_path = os.path.join(STATIC_DIR, rel_path)
    if os.path.isfile(file_path):
        # Guess MIME type from extension
        ext = os.path.splitext(file_path)[1].lower()
        mime = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".webp": "image/webp",
            ".svg": "image/svg+xml",
            ".css": "text/css",
            ".js": "application/javascript",
            ".woff2": "font/woff2",
        }.get(ext, "application/octet-stream")
        self._serve_file(file_path, mime)
    else:
        self._send(404, b"File not found", "text/plain")
```

Then in your HTML, reference assets as:

```html
<img src="/static/my-screenshot.png" alt="Demo">
<link rel="stylesheet" href="/static/extra-theme.css">
```

**Safety note:** The `".." not in path` check prevents directory traversal
attacks. Only serve from the `STATIC_DIR` — never serve the entire filesystem.

## Option B: Direct path routes (one-off)

For a small number of assets (1-3 files), add individual routes directly in
`do_GET`:

```python
elif path == "/screenshot.png":
    self._serve_file("/tmp/ir_demo_screenshot.png", "image/png")
```

Less flexible but zero extra code. Good for a single screenshot in a
presentation page.

## Option C: Base64 inline (zero server changes)

Embed images directly in the HTML as data URIs. No server changes needed, but
increases HTML file size significantly:

```html
<img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUg..." alt="Demo">
```

**When to use:** Tiny assets (icons, small diagrams < 10KB) where you want
a single self-contained HTML file. Not recommended for screenshots or photos
(50-300KB each inflates the HTML to 1-3MB).

## Practical pattern from this session

In the Threads presentation post, I needed 5 screenshots served alongside
the HTML. I used a combined approach:

1. Copied screenshots to `~/Desktop/ss_demo_overview.png`, etc.
2. Patched `do_GET` to match `/ss_*.png` → serve from `~/Desktop/{filename}`
3. HTML `<img src="/ss_demo_overview.png">` referenced the screenshot

The actual patch:

```python
elif path.startswith("/ss_") and path.endswith(".png"):
    filename = os.path.basename(path)
    static_path = os.path.expanduser(f"~/Desktop/{filename}")
    self._serve_file(static_path, "image/png")
```

This is dirt-simple and avoids the STATIC_DIR setup when you know all
assets live in the same flat directory.

## Pitfalls

- **Don't serve an entire ~/Desktop directory.** If you use a broad static
  route, narrow it to a specific subdirectory. Accidentally serving the
  Desktop exposes user data.
- **MIME type guessing is fragile.** Nginx and Apache do it better. For
  Python's http.server, the extension-based mapping above covers common
  cases. Add types as needed.
- **Base64-inflated HTML exceeds 50KB** — the interactive-report server
  reads the full HTML into memory. A 3MB base64-heavy page works but is
  slow to load. Prefer server-side file serving for anything over 100KB.
- **Path traversal attacks.** Always sanitize the filename when constructing
  file paths from user-controlled routes. The `".." not in path` check is
  minimal but sufficient for a local-only server. Do not remove it.
