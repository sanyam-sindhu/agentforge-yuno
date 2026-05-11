import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from backend.core.database import Base, get_db
from backend.main import app

TEST_DB_URL = "sqlite+aiosqlite:///./test_agentforge.db"
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
async def test_create_agent(client):
    resp = await client.post("/api/agents", json={
        "name": "Test Agent",
        "role": "tester",
        "system_prompt": "You are a test agent.",
        "model": "gpt-4o-mini",
        "tools": ["web_search"],
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Test Agent"
    assert data["tools"] == ["web_search"]


@pytest.mark.asyncio
async def test_list_agents(client):
    await client.post("/api/agents", json={"name": "A1", "role": "r1", "system_prompt": "p1"})
    await client.post("/api/agents", json={"name": "A2", "role": "r2", "system_prompt": "p2"})
    resp = await client.get("/api/agents")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_update_agent(client):
    create = await client.post("/api/agents", json={"name": "OldName", "role": "r", "system_prompt": "p"})
    agent_id = create.json()["id"]
    resp = await client.put(f"/api/agents/{agent_id}", json={"name": "NewName"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "NewName"


@pytest.mark.asyncio
async def test_delete_agent(client):
    create = await client.post("/api/agents", json={"name": "ToDelete", "role": "r", "system_prompt": "p"})
    agent_id = create.json()["id"]
    resp = await client.delete(f"/api/agents/{agent_id}")
    assert resp.status_code == 204
    get_resp = await client.get(f"/api/agents/{agent_id}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_create_agent_missing_required_fields(client):
    # name and system_prompt are required
    resp = await client.post("/api/agents", json={"role": "tester"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_agent_defaults(client):
    resp = await client.post("/api/agents", json={
        "name": "Minimal Agent",
        "role": "r",
        "system_prompt": "p",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["tools"] == [] or data["tools"] is None
    assert data["memory_enabled"] is False


@pytest.mark.asyncio
async def test_create_agent_with_memory_enabled(client):
    resp = await client.post("/api/agents", json={
        "name": "Memory Agent",
        "role": "r",
        "system_prompt": "p",
        "memory_enabled": True,
    })
    assert resp.status_code == 201
    assert resp.json()["memory_enabled"] is True


@pytest.mark.asyncio
async def test_get_single_agent(client):
    create = await client.post("/api/agents", json={"name": "Fetch Me", "role": "r", "system_prompt": "p"})
    agent_id = create.json()["id"]
    resp = await client.get(f"/api/agents/{agent_id}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Fetch Me"


@pytest.mark.asyncio
async def test_get_nonexistent_agent(client):
    resp = await client.get("/api/agents/99999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_agent_partial(client):
    create = await client.post("/api/agents", json={
        "name": "Original",
        "role": "analyst",
        "system_prompt": "original prompt",
    })
    agent_id = create.json()["id"]
    resp = await client.put(f"/api/agents/{agent_id}", json={"system_prompt": "updated prompt"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Original"
    assert data["system_prompt"] == "updated prompt"
