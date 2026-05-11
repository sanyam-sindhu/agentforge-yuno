import asyncio
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.database import get_db, AsyncSessionLocal
from backend.schemas.execution import ExecutionCreate, ExecutionRead
from backend.services.workflow_service import create_execution, get_workflow, list_executions
from backend.runtime.engine import run_workflow

router = APIRouter(prefix="/executions", tags=["executions"])


@router.get("", response_model=list[ExecutionRead])
async def get_executions(workflow_id: int | None = None, db: AsyncSession = Depends(get_db)):
    return await list_executions(db, workflow_id)


@router.post("", response_model=ExecutionRead, status_code=201)
async def create(data: ExecutionCreate, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    workflow = await get_workflow(db, data.workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    execution = await create_execution(db, data)
    background_tasks.add_task(_run_in_new_session, execution.id, workflow.id, data.input_text)
    return execution


async def _run_in_new_session(execution_id: int, workflow_id: int, input_text: str):
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        from backend.models.workflow import Workflow
        result = await db.execute(select(Workflow).where(Workflow.id == workflow_id))
        workflow = result.scalar_one()
        await run_workflow(execution_id, workflow, input_text, db)
