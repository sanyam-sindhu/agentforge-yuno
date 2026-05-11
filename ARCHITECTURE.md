# How AgentForge Works — A Complete Walkthrough

This document explains how the system is built, why certain decisions were made, and what actually happens when you create an agent, build a workflow, and run it. Written so anyone reading the code for the first time can orient themselves quickly.

---

## The big picture

AgentForge lets you build pipelines of AI agents. You configure each agent with a personality (system prompt), a set of tools it can use, and optionally memory. You then wire multiple agents together in a visual workflow where the output of one becomes the input of the next. The whole thing can be triggered from a web UI or from Telegram.

At its core, it's three things talking to each other:

```
React frontend  ←→  FastAPI backend  ←→  PostgreSQL (Neon)
                          ↕
                    LangGraph runtime
                          ↕
                    Telegram bot
```

The frontend never talks to the database directly. The Telegram bot never talks to the frontend. Everything goes through the FastAPI backend.

---

## Folder structure and what lives where

```
agentforge/
├── backend/
│   ├── api/          ← HTTP route handlers, nothing else
│   ├── services/     ← business logic, talks to DB
│   ├── models/       ← SQLAlchemy ORM table definitions
│   ├── schemas/      ← Pydantic models for request/response validation
│   ├── runtime/      ← LangGraph agent execution, tools
│   ├── channels/     ← Telegram bot integration
│   ├── core/         ← DB connection, config, websocket manager
│   ├── templates/    ← JSON files for pre-built workflow templates
│   ├── tests/        ← pytest test suite
│   └── main.py       ← FastAPI app, lifespan startup
└── frontend/
    └── src/
        ├── pages/    ← one file per page (Agents, Workflows, Monitor, Templates)
        ├── components/  ← reusable UI pieces
        ├── hooks/    ← data fetching with React Query
        └── lib/api.js   ← all HTTP calls in one place
```

The separation is intentional. `api/` files are thin — they validate input and call into `services/`. Services do the actual database work. The runtime layer doesn't know anything about HTTP. This means you can call `run_workflow()` from the API, from Telegram, from a test — without touching any web framework code.

---

## Agents

An agent is a row in the `agents` table. It has:

- `name` — what you call it
- `role` — a short label like "researcher" or "writer"
- `system_prompt` — the instruction you give to the LLM. This is what shapes the agent's behavior entirely.
- `model` — which OpenAI model to use (defaults to `gpt-4o-mini`)
- `tools` — a JSON list of tool names the agent is allowed to use
- `memory_enabled` — whether to persist conversation history across runs
- `guardrails` — JSON blob for any behavioral constraints
- `schedule` — cron string for scheduled runs (stored, scheduler hookup is a future step)
- `channel` — which messaging channel this agent is reachable on

When you create an agent through the UI, the frontend sends a POST to `/api/agents`. The API handler validates the request body using the `AgentCreate` Pydantic schema, calls `create_agent()` in `agent_service.py`, which writes to the database and returns the new row.

### How an agent actually runs

When it's time to execute, `agent_builder.py` constructs a LangGraph ReAct agent:

```python
graph = create_react_agent(
    model=llm,
    tools=tools,
    prompt=system_message,
    checkpointer=checkpointer,  # only set if memory_enabled is True
)
```

A ReAct agent works in a loop: it receives the input, decides whether to use a tool or respond directly, uses the tool if needed, looks at the result, decides again. LangGraph manages this loop internally. The `recursion_limit` defaults to 25 steps — after that it stops regardless.

Memory uses LangGraph's `MemorySaver`. When enabled, the agent's state (full message history) is stored in memory keyed by `thread_id` (the agent's database ID). This means the same agent remembers context across different workflow runs. When disabled, every run starts completely fresh.

---

## Tools

Tools are functions the agent can call during execution. They live in `backend/runtime/tools/` and are registered in `registry.py`. Currently available:

**web_search** — uses DuckDuckGo to search the web. Has retry logic with backoff (2s, 5s, 10s) because DuckDuckGo rate-limits free requests. If all retries fail, it returns a graceful error message instead of crashing the agent.

**scrape_url** — fetches a URL with httpx, parses the HTML with BeautifulSoup, strips navigation/footer/script tags, and returns the first 1500 characters of readable text.

**http_request** — makes arbitrary GET or POST requests. Useful for calling external APIs from within an agent.

**calculate** — evaluates a math expression. Prevents the LLM from doing arithmetic in its head (which it's notoriously bad at).

---

## Workflows

A workflow is a directed graph of agents. It's stored as a single JSON blob in the `graph_json` column:

```json
{
  "nodes": [
    {"id": "node-1", "agent_id": 3, "position": {"x": 100, "y": 200}},
    {"id": "node-2", "agent_id": 4, "position": {"x": 450, "y": 200}}
  ],
  "edges": [
    {"id": "edge-1", "source": "node-1", "target": "node-2"}
  ]
}
```

The `position` field is purely for the visual canvas. Execution doesn't care about it.

The workflow builder in the frontend uses React Flow — a library specifically built for node-based editors. Agents are dragged from the sidebar onto the canvas. Connections are drawn by dragging from one node's handle to another. When you save, the current canvas state (nodes + edges) is sent to the API and stored.

### Execution order

When a workflow runs, `engine.py` does a topological sort (Kahn's algorithm) on the nodes and edges to determine execution order. This guarantees that:

1. Cycles are detected and excluded
2. Every agent runs only after all agents that feed into it have completed
3. For linear chains (A → B → C), they run in exactly that order

---

## What happens when you run a workflow

This is the most important part to understand. Here's the full path:

**1. POST /api/executions**

The API creates an `Execution` row in the database with `status = "pending"` and returns it immediately. The actual workflow execution is kicked off as a FastAPI `BackgroundTask` — meaning the HTTP response goes back to the client before the agents have done anything. This is why the UI shows "pending" right after you click Run.

**2. Background task kicks off**

`_run_in_new_session()` opens a fresh database session (the original request session has already closed) and calls `run_workflow()`.

**3. run_workflow() iterates through agents**

For each node in topological order:
- Opens a DB session, fetches the agent record
- Broadcasts `agent_start` over WebSocket so the monitor updates in real time
- Builds the LangGraph graph for this agent
- Calls `graph.ainvoke()` with the current text as input
- Extracts the output from the last message in the response
- Saves a `Message` row to the database (from_agent, to_agent, content, tokens)
- Broadcasts `agent_message` over WebSocket
- Sets `current_text = output` so the next agent receives this agent's output as its input

**4. After all agents complete**

Updates the `Execution` row: `status = "completed"`, `output_text = final_output`, `finished_at = now`. Broadcasts `execution_done` over WebSocket.

**5. Error handling**

If an agent throws an exception, the error is caught, converted to a string (`"Agent error: <message>"`), and used as the output for that node. The workflow continues. This is intentional — it means a broken agent doesn't crash the whole pipeline, though it does poison the input for the next agent. The execution still completes.

---

## Real-time monitoring

The monitor works over WebSocket. The backend has a `WebSocketManager` that keeps a list of active connections. Any time something meaningful happens during a workflow run, `ws_manager.broadcast(event, data)` is called.

The frontend connects to `/ws/monitor` on load. Every incoming message is prepended to the events list (max 200 events kept). If a WebSocket client disconnects, it's silently removed from the active list during the next broadcast attempt.

Events you'll see:
- `agent_start` — an agent is about to run
- `agent_message` — an agent finished, here's its output and token count
- `execution_done` — the full workflow completed

The execution list in the monitor polls every 3 seconds via React Query's `refetchInterval`. The detail panel derives its data from this same live list rather than storing a snapshot, so the status badge updates automatically as the execution progresses.

---

## Telegram integration

The Telegram bot runs inside the same FastAPI process, started during the lifespan context. It uses long polling — the bot library keeps an open connection to Telegram's servers, and messages arrive as they're sent.

`drop_pending_updates=True` is set on startup. This is important for Railway deployments — when the container restarts, Telegram queues up any messages sent during downtime. Without this flag, the restarted instance would immediately process a flood of old messages. With it, stale messages are discarded.

Three commands are registered:
- `/start` — shows a welcome message with available commands
- `/research <topic>` — triggers the Research + Report workflow
- `/triage <message>` — triggers the Triage + Respond workflow
- Any plain text message — triggers Research + Report by default

When a message arrives, the handler:
1. Sends "Processing your request..." immediately (so the user knows something is happening)
2. Looks up the workflow by `template_id` in the database
3. Creates an `Execution` row
4. Calls `run_workflow()` directly (blocking, not backgrounded — the bot waits for the result)
5. Strips markdown from the output (Telegram renders its own formatting)
6. Truncates to 4000 characters if the output is too long
7. Sends the result back

---

## Templates

Templates are JSON files in `backend/templates/`. On every startup, `seed_templates()` reads these files and creates the corresponding agents and workflows in the database if they don't already exist (checked by `template_id`). This means:

- Fresh deployments automatically have working workflows
- You can add new templates just by dropping a JSON file and restarting
- Existing templates are never re-seeded — your edits to them in the UI are preserved

The JSON format:
```json
{
  "id": "unique_template_id",
  "name": "Display name",
  "description": "Short description",
  "agents": [...],
  "graph": {
    "nodes": [{"id": "...", "agent_index": 0, "position": {...}}],
    "edges": [{"id": "...", "source": "node-1", "target": "node-2"}]
  }
}
```

`agent_index` refers to the position in the `agents` array, not a database ID. The seeder resolves this to real agent IDs after creating the agents.

---

## Database

PostgreSQL hosted on Neon. The connection uses `asyncpg` (async driver) through SQLAlchemy's async engine. `NullPool` is used instead of a connection pool — this is intentional for serverless/edge deployments where long-lived connection pools can hit Neon's idle timeout and drop.

Four tables:
- `agents` — agent configurations
- `workflows` — workflow metadata + graph JSON
- `executions` — one row per run, tracks status and output
- `messages` — one row per agent step, stores the inter-agent communication

Schema is created automatically on startup via `Base.metadata.create_all`. No migrations — for this project, drop and recreate is fine.

---

## Configuration

All config lives in `backend/core/config.py` as a Pydantic `BaseSettings` class. Values come from environment variables (or a `.env` file locally). 

One thing worth knowing: `CORS_ORIGINS` is a `List[str]` field. Railway sets env vars as plain strings. The `parse_cors` validator handles both formats — you can set it as `https://myapp.vercel.app` or as `["https://myapp.vercel.app"]` and it'll work either way.

---

## Tests

23 tests across three files:

**test_agents.py** — tests the agent CRUD API end-to-end through the HTTP client. Covers creation, listing, update (full and partial), delete, 404 cases, and validation errors.

**test_workflow_execution.py** — tests that `run_workflow()` actually does what it's supposed to. The LangGraph agent is mocked so tests don't make real OpenAI calls. Key things tested: output is saved to the DB after completion, agent N+1 receives agent N's output as input, agent errors propagate as text strings without crashing the pipeline.

**test_message_delivery.py** — tests the WebSocket manager in isolation (broadcast to multiple clients, disconnected client removal) and verifies that `Message` rows are written to the database after each agent step and that all three WebSocket events fire during a run.

All tests use an isolated SQLite database (created fresh per test, dropped after). The `AsyncSessionLocal` used inside `run_workflow()` is patched to use the test session so database writes are visible to test assertions.

---

## Deployment

Backend runs on Railway. Frontend runs on Vercel. Database on Neon.

Railway reads `railway.toml` for the start command and `runtime.txt` for the Python version. The `requirements.txt` at the repo root contains the full dependency list — Railpack (Railway's build system) copies this file into the build container before running pip, so it needs to be self-contained at the root level.

Environment variables are set in the Railway dashboard, not in any config file. The only things Railway needs are: `OPENAI_API_KEY`, `TELEGRAM_BOT_TOKEN`, `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST`, `DATABASE_URL`, and `CORS_ORIGINS`.

Vercel needs one env var: `VITE_API_URL` pointing at the Railway backend URL. The frontend uses this to build the correct base URL for API calls and WebSocket connections. When `VITE_API_URL` is not set (local dev), it falls back to relative paths and Vite's proxy handles routing to localhost.

---

## Things that could be better

**No execution timeout.** If an agent gets stuck (LLM hangs, tool never returns), the background task runs forever. Adding a timeout wrapper around `run_workflow()` would fix this.

**Error-as-output pattern.** When an agent fails, the error string becomes the next agent's input. This means downstream agents silently receive garbage. A better approach would be to mark the execution as `failed` immediately and stop the pipeline.

**Schedule field is stored but not executed.** The `schedule` column exists on agents but there's no scheduler wired up. Connecting APScheduler or a Railway cron job would complete this.

**Single-process WebSocket.** The WebSocket manager is an in-memory list. If Railway ever scales to multiple instances, WebSocket events from one instance won't reach clients connected to another. Redis pub/sub would solve this if it ever becomes relevant.

**DuckDuckGo rate limits.** The free search API gets rate limited under heavy use. The retry logic (2s, 5s, 10s backoff) helps for occasional bursts but a paid search API (Tavily, Brave) would be more reliable for production use.
