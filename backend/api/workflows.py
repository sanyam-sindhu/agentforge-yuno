from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.database import get_db
from backend.schemas.workflow import WorkflowCreate, WorkflowUpdate, WorkflowRead
from backend.services.workflow_service import create_workflow, get_workflow, list_workflows, update_workflow, delete_workflow

router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.get("", response_model=list[WorkflowRead])
async def get_workflows(db: AsyncSession = Depends(get_db)):
    return await list_workflows(db)


@router.post("", response_model=WorkflowRead, status_code=201)
async def create(data: WorkflowCreate, db: AsyncSession = Depends(get_db)):
    return await create_workflow(db, data)


@router.get("/{workflow_id}", response_model=WorkflowRead)
async def get_one(workflow_id: int, db: AsyncSession = Depends(get_db)):
    workflow = await get_workflow(db, workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow


@router.put("/{workflow_id}", response_model=WorkflowRead)
async def update(workflow_id: int, data: WorkflowUpdate, db: AsyncSession = Depends(get_db)):
    workflow = await update_workflow(db, workflow_id, data)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow


@router.delete("/{workflow_id}", status_code=204)
async def delete(workflow_id: int, db: AsyncSession = Depends(get_db)):
    deleted = await delete_workflow(db, workflow_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Workflow not found")
