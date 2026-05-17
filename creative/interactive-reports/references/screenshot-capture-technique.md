# Screenshot Capture for Promotional & Documentation Use

When building interactive reports that you want to promote (Threads posts,
documentation, GitHub README screenshots), capture the page as an image
and serve it alongside the report itself.

## Technique

### 1. Start the server and navigate

```python
terminal(background=true, command="python3 /tmp/<NS>_server.py")
# Wait for port
terminal("sleep 1 && curl -s http://localhost:<PORT>/ | head -1")
# Open in browser
browser_navigate(f"http://localhost:<PORT>/")
```

### 2. Capture the screenshot

Even if the active model does not support `image_url` in messages (e.g.
DeepSeek Flash, Gemini text-only), `browser_vision` **still captures the
screenshot and saves it to disk**. The error response contains the path:

```
screenshot_path: "/Users/earchibald/.hermes/cache/screenshots/browser_screenshot_<uuid>.png"
```

Use this path to access the captured image.

```python
browser_vision(question="Capture screenshot of this page")
# Vision analysis may fail, but screenshot is saved
# → access via error.notes.screenshot_path
```

### 3. Verify screenshot uniqueness

`browser_vision` captures the **full page**, not the visible viewport.
Scrolling then calling `browser_vision` again produces the **same image**
because the headless browser renders the entire page every time.

Always verify screenshots are actually different before using both:

```bash
md5 ~/Desktop/screenshot_a.png ~/Desktop/screenshot_b.png
# If same → they're duplicates, discard one
```

If you need multiple distinct screenshots (top vs bottom), you must:
- Take one screenshot of the full page (covers everything)
- OR navigate to different URLs/pages to get different full-page renders
- OR use `browser_get_images` + `browser_console(expression)` to extract
  specific content instead

### 4. Name and stage files

```bash
cp /path/to/screenshot.png ~/Desktop/ss_<description>.png
```

Use a consistent prefix (`ss_` for screenshots) and descriptive names
(`ss_demo_overview.png`, `ss_provider_decision.png`).

### 5. Serve alongside the report

Patch the mini-server to serve screenshots from a known directory (see
`references/static-asset-serving.md` for full options):

```python
# In do_GET, before the 404 fallback:
elif path.startswith("/ss_") and path.endswith(".png"):
    filename = os.path.basename(path)
    static_path = os.path.expanduser(f"~/Desktop/{filename}")
    self._serve_file(static_path, "image/png")
```

Then embed in your HTML:

```html
<img src="/ss_demo_overview.png" alt="Demo screenshot">
```

### 6. Final delivery

The user can:
- Download screenshots from `~/Desktop/ss_*.png` for direct upload to Threads
- View the presentation page at `http://localhost:<PORT>/` for a live preview
- Submit the form to self-terminate the server when done

## Pitfalls

- **Full-page capture, not viewport.** `browser_vision` always renders the
  entire document. Scrolling does NOT produce a different screenshot. If two
  screenshots from the same page have the same MD5, they're duplicates.
- **Non-vision models still work** — but the error message (400, "unknown
  variant `image_url`") is misleading. The screenshot was saved despite the
  error. Check `screenshot_path` in the error response before retrying.
- **Desktop files persist.** Screenshots on `~/Desktop/` survive server
  restarts. Clean up with `rm ~/Desktop/ss_*.png` when done to avoid
  stale images in future sessions.
- **Large screenshots inflate page size.** A 300KB PNG adds no load time
  when server-served, but base64-embedding it adds 400KB+ to the HTML
  and makes the report slow. Use server-side routes (not base64) for
  screenshots over 50KB.
