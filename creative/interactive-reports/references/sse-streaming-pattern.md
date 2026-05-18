# SSE Streaming Pattern

Real-time streaming from agent to browser via Server-Sent Events.
Discovered and proven during the Maze Viewer project (May 2026).

## When to use SSE

Push agent thinking/logs/game-state to the browser in real-time,
especially when building interactive simulations, maze solvers,
live dashboards, or any page where the user watches agent activity
unfold.

SSE is simpler than WebSockets for one-directional server→client
streaming. No external dependencies — Python's `http.server` handles it.

## ThreadingTCPServer Requirement

**CRITICAL: `socketserver.TCPServer` is single-threaded.** An SSE
`while True` loop blocks ALL other requests (form submissions, state
polling, JSON endpoints). The server appears hung — requests time out
until the SSE client disconnects.

Always use `socketserver.ThreadingTCPServer` with `daemon_threads=True`:

```python
srv = type("S", (socketserver.ThreadingTCPServer,),
           {"allow_reuse_address": True, "daemon_threads": True})(
    ("", PORT), HandlerClass
)
```

This was discovered in production during the Maze Viewer project.
The mini-server template (`templates/mini-server.py`) has been updated
to ThreadingTCPServer.

## Server-Side SSE Endpoint

```python
from collections import defaultdict

sse_clients = defaultdict(list)  # room/maze_id -> [queue_of_pending_events]

def broadcast_event(room_id, event_type, data):
    msg = f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
    sse_clients[room_id].append(msg)

# In do_GET:
elif path == "/api/events":
    params = urllib.parse.parse_qs(urlparse(self.path).query)
    room_id = params.get("room_id", [None])[0]
    
    self.send_response(200)
    self.send_header("Content-Type", "text/event-stream")
    self.send_header("Cache-Control", "no-cache")
    self.send_header("Connection", "keep-alive")
    self.send_header("Access-Control-Allow-Origin", "*")
    self.end_headers()
    
    # Replay existing messages
    for msg in get_existing_messages(room_id):
        try:
            self.wfile.write(msg.encode())
            self.wfile.flush()
        except: return
    
    client_queue = []
    sse_clients[room_id].append(client_queue)
    
    try:
        while True:
            while client_queue:
                msg = client_queue.pop(0)
                try:
                    self.wfile.write(msg.encode())
                    self.wfile.flush()
                except: return
            
            if time.time() - last_heartbeat > 15:
                self.wfile.write(": heartbeat\n\n".encode())
                self.wfile.flush()
                last_heartbeat = time.time()
            
            time.sleep(0.5)
    except (BrokenPipeError, ConnectionResetError):
        pass
    finally:
        if client_queue in sse_clients.get(room_id, []):
            sse_clients[room_id].remove(client_queue)
```

## Client-Side JavaScript

```javascript
let eventSource = null;

function connectSSE() {
  if (eventSource) eventSource.close();
  eventSource = new EventSource(`/api/events?room_id=${roomId}`);
  
  eventSource.addEventListener('chat', (e) => {
    const data = JSON.parse(e.data);
    addChatEntry(data.text, 'agent');
  });
  
  eventSource.addEventListener('system', (e) => {
    addChatEntry(data.text, 'system');
  });
  
  // Auto-reconnects on error
}

function addChatEntry(text, type) {
  const log = document.getElementById('chatLog');
  const div = document.createElement('div');
  div.className = `entry ${type}`;
  div.innerHTML = `<span class="msg-text">${escapeHtml(text)}</span>`;
  log.appendChild(div);
  if (!scrollLocked) log.scrollTop = log.scrollHeight;
}
```

## State Polling vs SSE

For visual state (agent position, maze walls, visited cells), use
client-side polling (e.g. every 500ms) rather than SSE. It's simpler
and tolerates brief disconnects:

```javascript
setInterval(() => {
  fetch(`/api/state?room_id=${roomId}&session_id=${sessionId}`)
    .then(r => r.json())
    .then(state => { render(state); });
}, 500);
```

Use SSE only for text streams (thinking logs, chat messages).

## Canvas in Flex Layout

When embedding a `<canvas>` inside a flex layout alongside an SSE
chat panel, the canvas will render at 0x0 unless sizing is explicit:

```css
.maze-panel { flex: 1; min-width: 0; min-height: 0;
  display: flex; align-items: center; justify-content: center; }
.maze-canvas-wrap { width: 100%; height: 100%;
  display: flex; align-items: center; justify-content: center;
  overflow: auto; }
#mazeCanvas { display: block; }
```

The key: `min-height: 0` on every flex ancestor, and `width:100%;
height:100%` (not `max-width/max-height`) on the wrapper. Without
this, the canvas ends up at the container's default `min-height: auto`,
which can be very small.

## Stats Overlay Positioning

Avoid `position: absolute` overlays inside the maze-panel — they
overlap the canvas. Instead, move stats to the top bar:

```html
<div class="topbar">
  <span class="stat">Steps: <b id="stepCount">0</b></span>
  <span class="stat">Optimal: <b id="optimalCount">—</b></span>
</div>
```

If an overlay is required, position it inside `.maze-canvas-wrap`
with `position: absolute; bottom/left` so it stays within the canvas
boundary without overlapping scrollbars.
