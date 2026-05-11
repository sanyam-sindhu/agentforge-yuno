# AgentForge

A platform for building and running multi-agent AI workflows. You create agents, wire them together into a workflow, and let them run — communicating with each other to complete tasks. You can also talk to a workflow directly through Telegram.

Built for the Yuno AI Team hiring challenge.

---

## What it does

- Create agents with a name, role, system prompt, model, tools, memory, and guardrails
- Wire agents together visually in a workflow builder (drag-and-drop, powered by React Flow)
- Run workflows — agents execute in order, each one's output becomes the next one's input
- Watch everything happen live in the monitor (WebSocket feed — agent start, messages, token counts)
- Send a Telegram message and it triggers a workflow end-to-end
- Two pre-built templates ready to go on first run

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      Web UI (React)                     │
│  Agents │ Workflows │ Templates │ Monitor (WebSocket)   │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP + WebSocket
┌──────────────────────▼──────────────────────────────────┐
│                   FastAPI Backend                       │
│   REST API  │  WebSocket /ws/monitor  │  Lifespan       │
├───────────────┬───────────────────────┬─────────────────┤
│  LangGraph    │  Langfuse             │  Telegram Bot   │
│  Runtime      │  Observability        │  Integration    │
├───────────────┴───────────────────────┴─────────────────┤
│           PostgreSQL (Neon) via SQLAlchemy async        │
└─────────────────────────────────────────────────────────┘
```

The three layers are kept separate on purpose — the frontend only talks to REST/WebSocket, the runtime layer handles agent orchestration and never touches HTTP concerns, and the persistence layer is just models + sessions. The Telegram channel and the web UI both call into the same `run_workflow` function from the runtime layer.

---

## Stack choices

| Layer | What | Why |
|---|---|---|
| Frontend | React + Tailwind + Vite | Fast to build with, React Flow handles the workflow canvas well |
| Backend | FastAPI | Async-first, WebSocket support built-in, automatic API docs |
| AI Runtime | LangGraph | Explained below |
| Database | PostgreSQL via Neon | Async driver (asyncpg), free tier, zero infra for local dev |
| Observability | Langfuse | Token tracking and trace visualization per agent hop, free tier |
| Messaging | Telegram Bot API | Zero infra, good Python SDK, easy to test locally |

### Why LangGraph

I picked LangGraph over CrewAI and AutoGen for this project. The main reason is control — LangGraph gives you an explicit execution graph where you define exactly how state flows between nodes. That maps directly to the visual workflow builder: each node in the UI is a node in the LangGraph graph, each edge is an edge.

CrewAI is higher-level and makes simple things easier, but it abstracts away the execution order in a way that would make the "visual workflow builder with configurable edges" requirement awkward to implement. AutoGen is fine but more verbose and oriented toward conversational agent loops rather than pipeline-style execution.

LangGraph also has solid async support out of the box, which matters for the WebSocket monitor to work without blocking.

---

## Setup

You need Python 3.11+, Node 18+, and API keys before running.

```bash
git clone <repo>
cd agentforge
cp .env.example .env
# fill in your keys in .env
./setup.sh
```

That installs everything and starts both servers. Open http://localhost:5173.

If you're on Windows, run the backend and frontend manually:

```bash
# terminal 1
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# terminal 2
cd frontend
npm install
npm run dev
```

---

## Environment variables

```
OPENAI_API_KEY=sk-...
TELEGRAM_BOT_TOKEN=...         # from @BotFather
LANGFUSE_PUBLIC_KEY=pk-lf-...  # from cloud.langfuse.com
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com
DATABASE_URL=postgresql+asyncpg://<user>:<pass>@<host>/<db>?ssl=require
```

For the database, Neon's free tier works perfectly. Create a project at neon.tech, copy the connection string, paste it in. The schema is auto-created on first startup.

If you want to run purely local with SQLite instead, change `DATABASE_URL` to:

```
DATABASE_URL=sqlite+aiosqlite:///./agentforge.db
```

---

## What's built

**Agent configuration**
- Name, role, system prompt, model (any OpenAI model)
- Tools: `web_search`, `scrape_url`, `http_request`, `calculate`
- Memory toggle (persists conversation history across runs using LangGraph's MemorySaver)
- Guardrails field (stored as JSON, applied to agent config)
- Schedule field (cron string, stored — scheduler hookup is the next step)
- Channel assignment (which messaging channel this agent is reachable on)

**Workflow builder**
- Drag-and-drop canvas using React Flow
- Add agents as nodes, connect them with edges
- Execution order is determined by topological sort — the order you draw the edges is the order agents run

**Templates (auto-seeded on startup)**
1. **Research + Report** — ResearchAgent uses `web_search` + `scrape_url` to gather info, WriterAgent turns findings into a markdown report
2. **Triage + Respond** — TriageAgent classifies the message intent as technical/billing/general, SpecialistAgent writes the response

**Telegram integration**
- Start the bot, send it a message
- It finds the default workflow and runs it with your message as input
- Sends the final output back to you in the chat
- The execution shows up in the web monitor in real time

**Live monitor**
- WebSocket feed at `/ws/monitor`
- Events: `agent_start`, `agent_message` (with token count), `execution_done`
- Every inter-agent message is persisted and queryable via `/api/messages`

**Langfuse tracing**
- Every workflow run creates a trace
- Every agent hop is a span within the trace
- Token count and output captured per span

---

## Adding a workflow template

Templates live in `backend/templates/` as JSON files. The backend auto-seeds them on startup. To add one:

1. Create `backend/templates/<your_id>.json`. Use this structure:

```json
{
  "id": "your_template_id",
  "name": "Human-readable name",
  "description": "What this workflow does",
  "agents": [
    {
      "name": "First Agent",
      "role": "researcher",
      "system_prompt": "Your system prompt here",
      "model": "gpt-4o-mini",
      "tools": ["web_search"]
    },
    {
      "name": "Second Agent",
      "role": "writer",
      "system_prompt": "Your system prompt here",
      "model": "gpt-4o-mini",
      "tools": []
    }
  ],
  "graph": {
    "nodes": [
      {"id": "node-1", "agent_index": 0, "position": {"x": 100, "y": 200}},
      {"id": "node-2", "agent_index": 1, "position": {"x": 450, "y": 200}}
    ],
    "edges": [
      {"id": "edge-1", "source": "node-1", "target": "node-2"}
    ]
  }
}
```

2. Restart the backend. The seeder checks for existing templates by `id` so it won't duplicate.

The `agent_index` in `graph.nodes` refers to the position of the agent in the `agents` array.

---

## Adding a messaging channel

Telegram is in `backend/channels/telegram.py`. To add Slack, WhatsApp, or anything else:

1. Create `backend/channels/<name>.py`. It needs one function:

```python
async def build_<name>_app() -> YourAppType:
    # initialize your SDK, register message handlers
    # inside your handler, call:
    #   from backend.runtime.engine import run_workflow
    #   result = await run_workflow(execution_id, workflow, user_text, db)
    # then send result back to the user
    return app
```

2. Wire it into `backend/main.py` lifespan:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    your_app = await build_<name>_app()
    await your_app.start()
    yield
    await your_app.stop()
```

3. Add the token/credentials to `backend/core/config.py` and `.env.example`.

The channel is just a trigger — it creates an execution record, calls `run_workflow`, and sends back the output. All the actual agent logic stays in the runtime layer unchanged.

---

## Tests

```bash
cd backend
pytest tests/ -v
```

23 tests covering agent CRUD, workflow execution (single-agent, multi-agent chaining, failure propagation), and message delivery (WebSocket broadcast, DB persistence).

---

## API docs

Auto-generated at http://localhost:8000/docs after startup.
