from pydantic import BaseModel
from datetime import datetime


class ExecutionCreate(BaseModel):
    workflow_id: int
    input_text: str


class ExecutionRead(BaseModel):
    id: int
    workflow_id: int
    status: str
    input_text: str
    output_text: str
    langfuse_trace_id: str | None
    started_at: datetime
    finished_at: datetime | None

    model_config = {"from_attributes": True}


class MessageRead(BaseModel):
    id: int
    execution_id: int | None
    from_agent: str
    to_agent: str
    content: str
    tokens_used: int
    created_at: datetime

    model_config = {"from_attributes": True}
