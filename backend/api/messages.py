from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.core.database import get_db
from backend.models.message import Message
from backend.schemas.execution import MessageRead

router = APIRouter(prefix="/messages", tags=["messages"])


@router.get("", response_model=list[MessageRead])
async def get_messages(execution_id: int | None = None, db: AsyncSession = Depends(get_db)):
    query = select(Message).order_by(Message.created_at.desc())
    if execution_id:
        query = query.where(Message.execution_id == execution_id)
    result = await db.execute(query)
    return result.scalars().all()
