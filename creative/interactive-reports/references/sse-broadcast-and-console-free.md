# SSE Broadcasting & Console-Free UI Patterns

## SSE Broadcasting Pattern

When building interactive reports with real-time agent thinking (SSE chat panels):

### 1. Use ThreadingTCPServer
`http.server.ThreadingTCPServer` with `daemon_threads=True`. Single-threaded TCPServer blocks all requests while an SSE connection is open.

### 2. Broadcast Must Iterate Client Queues
Each SSE client registers a `client_queue = []`. Broadcasting must iterate and append to each queue.

WRONG (appends to queue list, never reaches clients):
```python
sse_clients[maze_id].append(msg)
```

RIGHT (appends to each client's queue):
```python
for client_queue in sse_clients[maze_id]:
    client_queue.append(msg)
```

### 3. Internal Methods Must Broadcast
Server-side code calling internal methods (not via HTTP handler) must call `broadcast_event()` explicitly. The POST handler does it automatically; background threads do not.

## Console-Free Workflow

User preference: NO console pasting. Wire everything into the UI.

### URL Parameter Initialization
```javascript
const params = new URLSearchParams(location.search);
const id = params.get('maze_id');
if (id) {
    loadResource(id);  // auto-connect without console
}
```
Document URLs: `http://localhost:9100/?maze_id=abc123` — not "paste in console."

### Auto-Create Sessions
On page load with URL params, auto-join/create sessions and connect SSE so a solver button click Just Works.

## Verify Browser is on Correct Page

When user reports "nothing showing":

1. Check `location.href` first — the browser may be on `about:blank` from a failed navigation
2. Re-navigate before concluding rendering is broken
3. Terminal `open` commands may fail silently — verify with `browser_navigate`
