from sqlalchemy import String, Integer, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from backend.core.database import Base


class Execution(Base):
    __tablename__ = "executions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    workflow_id: Mapped[int] = mapped_column(Integer, ForeignKey("workflows.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    input_text: Mapped[str] = mapped_column(String(2000), default="")
    output_text: Mapped[str] = mapped_column(String(4000), default="")
    langfuse_trace_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    started_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
    finished_at: Mapped[DateTime | None] = mapped_column(DateTime, nullable=True)
