from sqlalchemy import String, Boolean, JSON, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from backend.core.database import Base


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    role: Mapped[str] = mapped_column(String(100), nullable=False)
    system_prompt: Mapped[str] = mapped_column(String(4000), nullable=False)
    model: Mapped[str] = mapped_column(String(50), default="gpt-4o-mini")
    tools: Mapped[list] = mapped_column(JSON, default=list)
    channel: Mapped[str | None] = mapped_column(String(50), nullable=True)
    memory_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    guardrails: Mapped[dict] = mapped_column(JSON, default=dict)
    schedule: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
