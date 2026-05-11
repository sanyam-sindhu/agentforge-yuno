from pydantic import BaseModel
from datetime import datetime


class AgentCreate(BaseModel):
    name: str
    role: str
    system_prompt: str
    model: str = "gpt-4o-mini"
    tools: list[str] = []
    channel: str | None = None
    memory_enabled: bool = False
    guardrails: dict = {}
    schedule: str | None = None


class AgentUpdate(BaseModel):
    name: str | None = None
    role: str | None = None
    system_prompt: str | None = None
    model: str | None = None
    tools: list[str] | None = None
    channel: str | None = None
    memory_enabled: bool | None = None
    guardrails: dict | None = None
    schedule: str | None = None


class AgentRead(BaseModel):
    id: int
    name: str
    role: str
    system_prompt: str
    model: str
    tools: list[str]
    channel: str | None
    memory_enabled: bool
    guardrails: dict
    schedule: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
