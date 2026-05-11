from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.database import get_db
from backend.schemas.agent import AgentCreate, AgentUpdate, AgentRead
from backend.services.agent_service import create_agent, get_agent, list_agents, update_agent, delete_agent

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("", response_model=list[AgentRead])
async def get_agents(db: AsyncSession = Depends(get_db)):
    return await list_agents(db)


@router.post("", response_model=AgentRead, status_code=201)
async def create(data: AgentCreate, db: AsyncSession = Depends(get_db)):
    return await create_agent(db, data)


@router.get("/{agent_id}", response_model=AgentRead)
async def get_one(agent_id: int, db: AsyncSession = Depends(get_db)):
    agent = await get_agent(db, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.put("/{agent_id}", response_model=AgentRead)
async def update(agent_id: int, data: AgentUpdate, db: AsyncSession = Depends(get_db)):
    agent = await update_agent(db, agent_id, data)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.delete("/{agent_id}", status_code=204)
async def delete(agent_id: int, db: AsyncSession = Depends(get_db)):
    deleted = await delete_agent(db, agent_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Agent not found")
