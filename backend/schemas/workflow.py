from pydantic import BaseModel
from datetime import datetime


class WorkflowNode(BaseModel):
    id: str
    agent_id: int
    position: dict = {}


class WorkflowEdge(BaseModel):
    id: str
    source: str
    target: str
    condition: str | None = None


class GraphJson(BaseModel):
    nodes: list[WorkflowNode]
    edges: list[WorkflowEdge]


class WorkflowCreate(BaseModel):
    name: str
    description: str = ""
    graph_json: dict
    template_id: str | None = None


class WorkflowUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    graph_json: dict | None = None


class WorkflowRead(BaseModel):
    id: int
    name: str
    description: str
    graph_json: dict
    template_id: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
