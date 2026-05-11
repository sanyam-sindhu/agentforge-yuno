import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from unittest.mock import AsyncMock, patch

from backend.core.database import Base, get_db
from backend.main import app

TEST_DB_URL = "sqlite+aiosqlite:///./test_wf.db"
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


@pytest.mark.asyncio
async def test_create_workflow(client):
    resp = await client.post("/api/workflows", json={
        "name": "Test Workflow",
        "description": "A test",
        "graph_json": {"nodes": [], "edges": []},
    })
    assert resp.status_code == 201
    assert resp.json()["name"] == "Test Workflow"


@pytest.mark.asyncio
async def test_execute_workflow(client):
    agent_resp = await client.post("/api/agents", json={
        "name": "Mock Agent",
        "role": "mock",
        "system_prompt": "Just echo back the input.",
        "model": "gpt-4o-mini",
        "tools": [],
    })
    agent_id = agent_resp.json()["id"]

    wf_resp = await client.post("/api/workflows", json={
        "name": "Echo Workflow",
        "graph_json": {
            "nodes": [{"id": "n1", "agent_id": agent_id, "position": {"x": 0, "y": 0}}],
            "edges": [],
        },
    })
    wf_id = wf_resp.json()["id"]

    with patch("backend.runtime.engine.build_agent") as mock_build:
        mock_graph = AsyncMock()
        mock_graph.ainvoke.return_value = {
            "messages": [type("Msg", (), {"content": "Mocked output"})()],
        }
        mock_build.return_value = mock_graph

        exec_resp = await client.post("/api/executions", json={
            "workflow_id": wf_id,
            "input_text": "Hello agents",
        })
        assert exec_resp.status_code == 201
        assert exec_resp.json()["status"] == "pending"


@pytest.mark.asyncio
async def test_execute_workflow_completes_and_saves_output(client):
    """run_workflow should set status=completed and persist output_text."""
    import asyncio
    from backend.runtime.engine import run_workflow
    from backend.models.execution import Execution
    from sqlalchemy import select

    agent_resp = await client.post("/api/agents", json={
        "name": "Echo Agent",
        "role": "echo",
        "system_prompt": "Echo input.",
        "model": "gpt-4o-mini",
        "tools": [],
    })
    agent_id = agent_resp.json()["id"]

    wf_resp = await client.post("/api/workflows", json={
        "name": "Single Node",
        "graph_json": {
            "nodes": [{"id": "n1", "agent_id": agent_id, "position": {"x": 0, "y": 0}}],
            "edges": [],
        },
    })
    wf_id = wf_resp.json()["id"]

    exec_resp = await client.post("/api/executions", json={"workflow_id": wf_id, "input_text": "ping"})
    exec_id = exec_resp.json()["id"]

    with patch("backend.runtime.engine.build_agent") as mock_build, \
         patch("backend.runtime.engine.get_langfuse") as mock_langfuse, \
         patch("backend.runtime.engine.AsyncSessionLocal", TestSession):
        _setup_langfuse_mock(mock_langfuse)
        mock_graph = AsyncMock()
        mock_graph.ainvoke.return_value = {
            "messages": [type("M", (), {"content": "pong"})()],
        }
        mock_build.return_value = mock_graph

        from backend.models.workflow import Workflow
        async with TestSession() as db:
            wf_row = (await db.execute(select(Workflow).where(Workflow.id == wf_id))).scalar_one()
            await run_workflow(exec_id, wf_row, "ping", db)

    async with TestSession() as db:
        exec_row = (await db.execute(select(Execution).where(Execution.id == exec_id))).scalar_one()
        assert exec_row.status == "completed"
        assert exec_row.output_text == "pong"


@pytest.mark.asyncio
async def test_execute_workflow_multi_agent_chains_output(client):
    """Output of agent N becomes input of agent N+1."""
    from backend.runtime.engine import run_workflow
    from backend.models.workflow import Workflow
    from sqlalchemy import select

    a1 = (await client.post("/api/agents", json={"name": "A1", "role": "r", "system_prompt": "p", "model": "gpt-4o-mini", "tools": []})).json()["id"]
    a2 = (await client.post("/api/agents", json={"name": "A2", "role": "r", "system_prompt": "p", "model": "gpt-4o-mini", "tools": []})).json()["id"]

    wf_resp = await client.post("/api/workflows", json={
        "name": "Chain",
        "graph_json": {
            "nodes": [
                {"id": "n1", "agent_id": a1, "position": {"x": 0, "y": 0}},
                {"id": "n2", "agent_id": a2, "position": {"x": 1, "y": 0}},
            ],
            "edges": [{"source": "n1", "target": "n2"}],
        },
    })
    wf_id = wf_resp.json()["id"]
    exec_id = (await client.post("/api/executions", json={"workflow_id": wf_id, "input_text": "start"})).json()["id"]

    call_inputs = []

    with patch("backend.runtime.engine.build_agent") as mock_build, \
         patch("backend.runtime.engine.get_langfuse") as mock_langfuse, \
         patch("backend.runtime.engine.AsyncSessionLocal", TestSession):
        _setup_langfuse_mock(mock_langfuse)

        def make_graph(text):
            graph = AsyncMock()
            async def ainvoke(payload, config=None):
                call_inputs.append(payload["messages"][0].content)
                return {"messages": [type("M", (), {"content": f"out:{text}"})()]}
            graph.ainvoke = ainvoke
            return graph

        # first call → agent A1, second call → agent A2
        mock_build.side_effect = [make_graph("first"), make_graph("second")]

        async with TestSession() as db:
            wf_row = (await db.execute(select(Workflow).where(Workflow.id == wf_id))).scalar_one()
            result = await run_workflow(exec_id, wf_row, "start", db)

    assert call_inputs[0] == "start"
    assert call_inputs[1] == "out:first"   # A2 received A1's output
    assert result == "out:second"


@pytest.mark.asyncio
async def test_execute_workflow_agent_failure_propagates_as_text(client):
    """When an agent raises, its error string becomes the next agent's input."""
    from backend.runtime.engine import run_workflow
    from backend.models.workflow import Workflow
    from backend.models.execution import Execution
    from sqlalchemy import select

    a1 = (await client.post("/api/agents", json={"name": "Broken", "role": "r", "system_prompt": "p", "model": "gpt-4o-mini", "tools": []})).json()["id"]

    wf_resp = await client.post("/api/workflows", json={
        "name": "Fail Workflow",
        "graph_json": {
            "nodes": [{"id": "n1", "agent_id": a1, "position": {"x": 0, "y": 0}}],
            "edges": [],
        },
    })
    wf_id = wf_resp.json()["id"]
    exec_id = (await client.post("/api/executions", json={"workflow_id": wf_id, "input_text": "trigger"})).json()["id"]

    with patch("backend.runtime.engine.build_agent") as mock_build, \
         patch("backend.runtime.engine.get_langfuse") as mock_langfuse, \
         patch("backend.runtime.engine.AsyncSessionLocal", TestSession):
        _setup_langfuse_mock(mock_langfuse)
        mock_graph = AsyncMock()
        mock_graph.ainvoke.side_effect = RuntimeError("LLM timeout")
        mock_build.return_value = mock_graph

        async with TestSession() as db:
            wf_row = (await db.execute(select(Workflow).where(Workflow.id == wf_id))).scalar_one()
            result = await run_workflow(exec_id, wf_row, "trigger", db)

    assert "Agent error" in result
    assert "LLM timeout" in result

    async with TestSession() as db:
        exec_row = (await db.execute(select(Execution).where(Execution.id == exec_id))).scalar_one()
        assert exec_row.status == "completed"   # still marks completed (current behaviour)
        assert "Agent error" in exec_row.output_text


@pytest.mark.asyncio
async def test_execute_nonexistent_workflow(client):
    resp = await client.post("/api/executions", json={"workflow_id": 99999, "input_text": "x"})
    assert resp.status_code in (404, 422)


# ── helpers ──────────────────────────────────────────────────────────────────

def _setup_langfuse_mock(mock_langfuse):
    """Wire up the langfuse context-manager chain used inside run_workflow."""
    from unittest.mock import MagicMock
    lf = MagicMock()
    span = MagicMock()
    span.__enter__ = MagicMock(return_value=span)
    span.__exit__ = MagicMock(return_value=False)
    span.trace_id = "test-trace"
    lf.start_as_current_observation.return_value = span
    lf.flush = MagicMock()
    mock_langfuse.return_value = lf
