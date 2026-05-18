# Single-Endpoint Agent Initialization

Pattern: one GET endpoint that returns everything an autonomous agent needs
to start working — no multi-step setup, no manual configuration.

Discovered during the Maze Viewer project (May 2026). The user explicitly
demanded: "a simple GET to an endpoint should initialize the agent with all
the information they need."

## Why

- Agents should need exactly ONE call to initialize
- No manual wiring of session IDs, maze IDs, or other state
- Human watching the GUI should just click a button, not paste console commands
- Works for: game agents, background workers, cron-job triggers, webhook handlers

## Pattern

```
GET /api/agent/start?maze_id=X&seed=Y&width=W&height=H&complexity=C
```

All parameters are optional:
- `maze_id` → join an existing resource
- `seed` → create a deterministic resource (same seed = same resource)
- `width/height/complexity` → configure auto-generated resources
- No params → auto-generate everything

Returns:
```json
{
  "maze_id": "deadbeef1234",
  "session_id": "abc123def456",
  "width": 30,
  "height": 30,
  "complexity": "medium",
  "optimal_steps": 217,
  "room": {
    "description": "Line of sight:\n  ↑ NORTH: ·· 2 cells...",
    "exits": ["north", "south"],
    "line_of_sight": {...}
  },
  "agent_prompt": "# MAZE SOLVING MISSION\n...",
  "instructions": "Use POST /api/move to navigate, POST /api/chat to stream thinking."
}
```

## Implementation

```python
# In do_GET:
elif path == "/api/agent/start":
    params = urllib.parse.parse_qs(urlparse(self.path).query)
    maze_id = params.get("maze_id", [None])[0]
    seed = params.get("seed", [None])[0]
    width = int(params.get("width", [30])[0])
    height = int(params.get("height", [30])[0])
    complexity = params.get("complexity", ["medium"])[0]
    
    # Auto-generate if no maze_id
    if not maze_id:
        maze_id = create_resource(width, height, complexity, seed)
    elif maze_id not in resources:
        # Unknown ID — treat as seed for deterministic generation
        maze_id = create_resource(width, height, complexity, maze_id)
    
    session_id = join_resource(maze_id)
    
    return send_json({
        "maze_id": maze_id,
        "session_id": session_id,
        "room": get_room_description(maze_id, session_id),
        "agent_prompt": build_prompt(maze_id),
        "instructions": "Use POST /api/action to interact."
    })
```

## Deterministic Seeds as IDs

The resource ID should BE the seed for deterministic replayability:
- `seed=deadbeef` → `maze_id=deadbeef`, always the same maze
- No seed → auto-generate a random seed
- This way the ID is both the identifier AND the reproducible seed

Implementation:
```python
def create_resource(seed=None):
    if seed is None:
        seed = uuid.uuid4().hex[:12]
    resource_id = seed  # ID IS the seed
    seed_int = int(seed, 16) if all(c in '0123456789abcdef' for c in seed) else hash(seed) % (2**32)
    random.seed(seed_int)
    # ... generate deterministic resource ...
    return resource_id
```

## UI Integration

Pair this with a button that calls `/api/solve` after initialization:

```html
<button id="solveBtn">⚡ Start Solver</button>
```

```javascript
document.getElementById('solveBtn').addEventListener('click', async () => {
  const startResp = await fetch(`/api/agent/start?maze_id=${mazeId}`);
  const data = await startResp.json();
  sessionId = data.session_id;
  
  await fetch('/api/solve', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({session_id: sessionId})
  });
});
```

The user never sees a console, never pastes an ID, never types a command.
One click starts the whole pipeline.
