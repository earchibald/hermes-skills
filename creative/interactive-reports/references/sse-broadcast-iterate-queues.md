# SSE Broadcast — Iterate Client Queues

When building SSE event broadcasting for servers with multiple connected
clients, the broadcast function must iterate over each client's individual
queue. The `sse_clients` dict maps `maze_id` (or any broadcast key) to a
LIST of per-client queues.

## Common Bug

Appending the event message to the queue LIST instead of each queue:

```python
sse_clients = defaultdict(list)  # maze_id → [client_queue1, client_queue2, ...]

# Each SSE handler registers its own queue:
client_queue = []
sse_clients[maze_id].append(client_queue)

# WRONG — appends message string to the list of queues:
def broadcast_event_broken(maze_id, event_type, data):
    msg = f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
    sse_clients[maze_id].append(msg)  # goes to queue LIST, not to any client

# RIGHT — appends to each individual client queue:
def broadcast_event_fixed(maze_id, event_type, data):
    msg = f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
    for client_queue in sse_clients[maze_id]:
        client_queue.append(msg)
```

The SSE handler's loop does:
```python
while True:
    while client_queue:
        msg = client_queue.pop(0)
        self.wfile.write(msg.encode())
        self.wfile.flush()
    time.sleep(0.5)
```

It pops from `client_queue` (the queue it registered). If `broadcast_event`
appends to `sse_clients[maze_id]` (the list-of-queues), the client never
sees the message — it's in the wrong data structure.

## Symptom

SSE clients never receive events. The broadcast function runs, messages are
"sent," but the browser chat panel never updates. Internal game.chat() calls
work (messages are stored in session), but SSE streaming is silent.

## Fix

Always iterate `sse_clients[key]` and append to each member queue:

```python
for client_queue in sse_clients[maze_id]:
    client_queue.append(msg)
```
