from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.models.agent import Agent
from backend.schemas.agent import AgentCreate, AgentUpdate


async def create_agent(db: AsyncSession, data: AgentCreate) -> Agent:
    agent = Agent(**data.model_dump())
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    return agent


async def get_agent(db: AsyncSession, agent_id: int) -> Agent | None:
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    return result.scalar_one_or_none()


async def list_agents(db: AsyncSession) -> list[Agent]:
    result = await db.execute(select(Agent).order_by(Agent.created_at.desc()))
    return result.scalars().all()


async def update_agent(db: AsyncSession, agent_id: int, data: AgentUpdate) -> Agent | None:
    agent = await get_agent(db, agent_id)
    if not agent:
        return None
    for key, value in data.model_dump(exclude_none=True).items():
        setattr(agent, key, value)
    await db.commit()
    await db.refresh(agent)
    return agent


async def delete_agent(db: AsyncSession, agent_id: int) -> bool:
    agent = await get_agent(db, agent_id)
    if not agent:
        return False
    await db.delete(agent)
    await db.commit()
    return True
