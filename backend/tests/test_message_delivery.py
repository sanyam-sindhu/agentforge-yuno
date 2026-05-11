"""
Tests for message delivery:
  - Messages are persisted to the DB after each agent step
  - WebSocket broadcast fires the right events with the right payloads
  - Disconnected WebSocket clients are removed without crashing the broadcast
"""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from backend.core.database import Base, get_db
from backend.core.websocket_manager import WebSocketManager
from backend.main import app
from httpx import AsyncClient, ASGITransport

TEST_DB_URL = "sqlite+aiosqlite:///./test_messages.db"
test_engine = create_async_engine(TEST_DB_URL)
TestSession = async_sessionmaker(test_engine, expire_on_commit=False)


async def override_db():
    async with TestSession() as session:
        yield session


@pytest.fixture(autouse=True)
async def setup_db():
    app.dependency_overrides[get_db] = override_db
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


# ── WebSocketManager unit tests ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_websocket_manager_broadcast_sends_to_all_clients():
    manager = WebSocketManager()
    ws1, ws2 = AsyncMock(), AsyncMock()
    manager.active = [ws1, ws2]

    await manager.broadcast("agent_message", {"content": "hello"})

    expected = json.dumps({"event": "agent_message", "data": {"content": "hello"}})
    ws1.send_text.assert_awaited_once_with(expected)
    ws2.send_text.assert_awaited_once_with(expected)


@pytest.mark.asyncio
async def test_websocket_manager_removes_disconnected_client():
    manager = WebSocketManager()
    good_ws = AsyncMock()
    bad_ws = AsyncMock()
    bad_ws.send_text.side_effect = Exception("connection closed")
    manager.active = [bad_ws, good_ws]

    await manager.broadcast("ping", {})

    assert bad_ws not in manager.active
    assert good_ws in manager.active


@pytest.mark.asyncio
async def test_websocket_manager_empty_active_list():
    manager = WebSocketManager()
    # Should not raise
    await manager.broadcast("event", {"key": "value"})


@pytest.mark.asyncio
async def test_websocket_manager_connect_and_disconnect():
    manager = WebSocketManager()
    ws = AsyncMock()
    await manager.connect(ws)
    assert ws in manager.active
    manager.disconnect(ws)
    assert ws not in manager.active


# ── Message persistence via run_workflow ─────────────────────────────────────

@pytest.mark.asyncio
async def test_messages_persisted_after_agent_run(client):
    """Each agent step must write a Message row to the DB."""
    from backend.runtime.engine import run_workflow
    from backend.models.workflow import Workflow
    from backend.models.message import Message

    agent_id = (await client.post("/api/agents", json={
        "name": "Persist Agent",
        "role": "r",
        "system_prompt": "p",
        "model": "gpt-4o-mini",
        "tools": [],
    })).json()["id"]

    wf_id = (await client.post("/api/workflows", json={
        "name": "Msg Workflow",
        "graph_json": {
            "nodes": [{"id": "n1", "agent_id": agent_id, "position": {"x": 0, "y": 0}}],
            "edges": [],
        },
    })).json()["id"]

    exec_id = (await client.post("/api/executions", json={
        "workflow_id": wf_id,
        "input_text": "test input",
    })).json()["id"]

    with patch("backend.runtime.engine.build_agent") as mock_build, \
         patch("backend.runtime.engine.get_langfuse") as mock_langfuse, \
         patch("backend.runtime.engine.AsyncSessionLocal", TestSession):
        _setup_langfuse_mock(mock_langfuse)
        mock_graph = AsyncMock()
        mock_graph.ainvoke.return_value = {
            "messages": [type("M", (), {"content": "agent reply"})()],
        }
        mock_build.return_value = mock_graph

        async with TestSession() as db:
            wf_row = (await db.execute(select(Workflow).where(Workflow.id == wf_id))).scalar_one()
            await run_workflow(exec_id, wf_row, "test input", db)

    async with TestSession() as db:
        msgs = (await db.execute(select(Message).where(Message.execution_id == exec_id))).scalars().all()
    assert len(msgs) == 1
    assert msgs[0].from_agent == "Persist Agent"
    assert msgs[0].content == "agent reply"


@pytest.mark.asyncio
async def test_messages_persisted_for_each_agent_in_chain(client):
    """Multi-agent workflow must produce one Message row per agent."""
    from backend.runtime.engine import run_workflow
    from backend.models.workflow import Workflow
    from backend.models.message import Message

    a1 = (await client.post("/api/agents", json={"name": "Chain-A", "role": "r", "system_prompt": "p", "model": "gpt-4o-mini", "tools": []})).json()["id"]
    a2 = (await client.post("/api/agents", json={"name": "Chain-B", "role": "r", "system_prompt": "p", "model": "gpt-4o-mini", "tools": []})).json()["id"]

    wf_id = (await client.post("/api/workflows", json={
        "name": "Chain Msg",
        "graph_json": {
            "nodes": [
                {"id": "n1", "agent_id": a1, "position": {"x": 0, "y": 0}},
                {"id": "n2", "agent_id": a2, "position": {"x": 1, "y": 0}},
            ],
            "edges": [{"source": "n1", "target": "n2"}],
        },
    })).json()["id"]

    exec_id = (await client.post("/api/executions", json={"workflow_id": wf_id, "input_text": "go"})).json()["id"]

    with patch("backend.runtime.engine.build_agent") as mock_build, \
         patch("backend.runtime.engine.get_langfuse") as mock_langfuse, \
         patch("backend.runtime.engine.AsyncSessionLocal", TestSession):
        _setup_langfuse_mock(mock_langfuse)

        def _graph(reply):
            g = AsyncMock()
            g.ainvoke.return_value = {"messages": [type("M", (), {"content": reply})()]}
            return g

        mock_build.side_effect = [_graph("step1"), _graph("step2")]

        async with TestSession() as db:
            wf_row = (await db.execute(select(Workflow).where(Workflow.id == wf_id))).scalar_one()
            await run_workflow(exec_id, wf_row, "go", db)

    async with TestSession() as db:
        msgs = (await db.execute(select(Message).where(Message.execution_id == exec_id))).scalars().all()

    assert len(msgs) == 2
    contents = {m.content for m in msgs}
    assert "step1" in contents
    assert "step2" in contents


@pytest.mark.asyncio
async def test_ws_broadcast_events_fired_during_execution(client):
    """run_workflow must broadcast agent_start, agent_message, and execution_done."""
    from backend.runtime.engine import run_workflow
    from backend.models.workflow import Workflow

    agent_id = (await client.post("/api/agents", json={
        "name": "Broadcast Agent",
        "role": "r",
        "system_prompt": "p",
        "model": "gpt-4o-mini",
        "tools": [],
    })).json()["id"]

    wf_id = (await client.post("/api/workflows", json={
        "name": "Broadcast WF",
        "graph_json": {
            "nodes": [{"id": "n1", "agent_id": agent_id, "position": {"x": 0, "y": 0}}],
            "edges": [],
        },
    })).json()["id"]

    exec_id = (await client.post("/api/executions", json={"workflow_id": wf_id, "input_text": "hi"})).json()["id"]

    broadcast_calls = []

    async def capture_broadcast(event, data):
        broadcast_calls.append(event)

    with patch("backend.runtime.engine.build_agent") as mock_build, \
         patch("backend.runtime.engine.get_langfuse") as mock_langfuse, \
         patch("backend.runtime.engine.AsyncSessionLocal", TestSession), \
         patch("backend.runtime.engine.ws_manager") as mock_ws:
        _setup_langfuse_mock(mock_langfuse)
        mock_ws.broadcast = AsyncMock(side_effect=capture_broadcast)
        mock_graph = AsyncMock()
        mock_graph.ainvoke.return_value = {"messages": [type("M", (), {"content": "done"})()]}
        mock_build.return_value = mock_graph

        async with TestSession() as db:
            wf_row = (await db.execute(select(Workflow).where(Workflow.id == wf_id))).scalar_one()
            await run_workflow(exec_id, wf_row, "hi", db)

    assert "agent_start" in broadcast_calls
    assert "agent_message" in broadcast_calls
    assert "execution_done" in broadcast_calls


# ── helper ────────────────────────────────────────────────────────────────────

def _setup_langfuse_mock(mock_langfuse):
    lf = MagicMock()
    span = MagicMock()
    span.__enter__ = MagicMock(return_value=span)
    span.__exit__ = MagicMock(return_value=False)
    span.trace_id = "test-trace"
    lf.start_as_current_observation.return_value = span
    lf.flush = MagicMock()
    mock_langfuse.return_value = lf
