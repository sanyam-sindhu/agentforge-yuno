from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.models.workflow import Workflow
from backend.models.execution import Execution
from backend.schemas.workflow import WorkflowCreate, WorkflowUpdate
from backend.schemas.execution import ExecutionCreate


async def create_workflow(db: AsyncSession, data: WorkflowCreate) -> Workflow:
    workflow = Workflow(**data.model_dump())
    db.add(workflow)
    await db.commit()
    await db.refresh(workflow)
    return workflow


async def get_workflow(db: AsyncSession, workflow_id: int) -> Workflow | None:
    result = await db.execute(select(Workflow).where(Workflow.id == workflow_id))
    return result.scalar_one_or_none()


async def list_workflows(db: AsyncSession) -> list[Workflow]:
    result = await db.execute(select(Workflow).order_by(Workflow.created_at.desc()))
    return result.scalars().all()


async def update_workflow(db: AsyncSession, workflow_id: int, data: WorkflowUpdate) -> Workflow | None:
    workflow = await get_workflow(db, workflow_id)
    if not workflow:
        return None
    for key, value in data.model_dump(exclude_none=True).items():
        setattr(workflow, key, value)
    await db.commit()
    await db.refresh(workflow)
    return workflow


async def delete_workflow(db: AsyncSession, workflow_id: int) -> bool:
    workflow = await get_workflow(db, workflow_id)
    if not workflow:
        return False
    await db.delete(workflow)
    await db.commit()
    return True


async def create_execution(db: AsyncSession, data: ExecutionCreate) -> Execution:
    execution = Execution(workflow_id=data.workflow_id, input_text=data.input_text)
    db.add(execution)
    await db.commit()
    await db.refresh(execution)
    return execution


async def list_executions(db: AsyncSession, workflow_id: int | None = None) -> list[Execution]:
    query = select(Execution).order_by(Execution.started_at.desc())
    if workflow_id:
        query = query.where(Execution.workflow_id == workflow_id)
    result = await db.execute(query)
    return result.scalars().all()
