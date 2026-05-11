import asyncio
import json
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from backend.core.config import get_settings
from backend.core.database import init_db, AsyncSessionLocal
from backend.core.websocket_manager import ws_manager
from backend.api.router import api_router
from backend.models.agent import Agent
from backend.models.workflow import Workflow

settings = get_settings()


async def seed_templates():
    templates_dir = Path(__file__).parent / "templates"
    async with AsyncSessionLocal() as db:
        for template_file in templates_dir.glob("*.json"):
            data = json.loads(template_file.read_text())
            template_id = data["id"]

            existing = await db.execute(select(Workflow).where(Workflow.template_id == template_id))
            if existing.scalar_one_or_none():
                continue

            agent_ids = []
            for agent_data in data["agents"]:
                existing_agent = await db.execute(select(Agent).where(Agent.name == agent_data["name"]))
                agent = existing_agent.scalar_one_or_none()
                if not agent:
                    agent = Agent(**{k: v for k, v in agent_data.items()})
                    db.add(agent)
                    await db.flush()
                agent_ids.append(agent.id)

            graph = data["graph"]
            nodes = []
            for node in graph["nodes"]:
                nodes.append({
                    "id": node["id"],
                    "agent_id": agent_ids[node["agent_index"]],
                    "position": node["position"],
                })

            workflow = Workflow(
                name=data["name"],
                description=data["description"],
                graph_json={"nodes": nodes, "edges": graph["edges"]},
                template_id=template_id,
            )
            db.add(workflow)

        await db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await seed_templates()

    if settings.telegram_bot_token:
        try:
            from backend.channels.telegram import build_telegram_app
            telegram_app = build_telegram_app()
            await telegram_app.initialize()
            await telegram_app.start()
            await telegram_app.updater.start_polling(
                drop_pending_updates=True,
                error_callback=lambda e: print(f"Telegram error: {e}"),
            )
            app.state.telegram_app = telegram_app
        except Exception as e:
            print(f"Telegram bot failed to start: {e} — continuing without it")

    yield

    if settings.telegram_bot_token and hasattr(app.state, "telegram_app"):
        await app.state.telegram_app.updater.stop()
        await app.state.telegram_app.stop()
        await app.state.telegram_app.shutdown()


app = FastAPI(title="AgentForge", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.websocket("/ws/monitor")
async def monitor_ws(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


@app.get("/health")
async def health():
    return {"status": "ok"}
