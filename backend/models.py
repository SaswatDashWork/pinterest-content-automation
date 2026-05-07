from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from backend.database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Workflow(Base):
    __tablename__ = "workflows"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    command: Mapped[str] = mapped_column(Text, nullable=False)
    plan: Mapped[Any] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )

    executions: Mapped[list[Execution]] = relationship(
        "Execution", back_populates="workflow", cascade="all, delete-orphan"
    )


class Execution(Base):
    __tablename__ = "executions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    workflow_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("workflows.id"), nullable=True
    )
    command: Mapped[str] = mapped_column(Text, nullable=False)
    # pending | running | completed | failed
    status: Mapped[str] = mapped_column(String(50), default="pending")
    plan: Mapped[Any] = mapped_column(JSON)
    steps_completed: Mapped[int] = mapped_column(Integer, default=0)
    total_steps: Mapped[int] = mapped_column(Integer, default=0)
    current_step: Mapped[str | None] = mapped_column(Text)
    result: Mapped[Any] = mapped_column(JSON)
    error: Mapped[str | None] = mapped_column(Text)
    screenshots: Mapped[Any] = mapped_column(JSON, default=list)
    logs: Mapped[Any] = mapped_column(JSON, default=list)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    workflow: Mapped[Workflow | None] = relationship("Workflow", back_populates="executions")
    steps: Mapped[list[ExecutionStep]] = relationship(
        "ExecutionStep", back_populates="execution", cascade="all, delete-orphan"
    )


class ExecutionStep(Base):
    __tablename__ = "execution_steps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    execution_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("executions.id"), nullable=False
    )
    step_index: Mapped[int] = mapped_column(Integer, nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    params: Mapped[Any] = mapped_column(JSON)
    # pending | running | completed | failed | skipped
    status: Mapped[str] = mapped_column(String(50), default="pending")
    result: Mapped[Any] = mapped_column(JSON)
    error: Mapped[str | None] = mapped_column(Text)
    screenshot: Mapped[str | None] = mapped_column(String(500))
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    execution: Mapped[Execution] = relationship("Execution", back_populates="steps")


class SavedAutomation(Base):
    __tablename__ = "saved_automations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    command_template: Mapped[str] = mapped_column(Text, nullable=False)
    plan_template: Mapped[Any] = mapped_column(JSON)
    tags: Mapped[Any] = mapped_column(JSON, default=list)
    use_count: Mapped[int] = mapped_column(Integer, default=0)
    success_rate: Mapped[int] = mapped_column(Integer, default=100)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )
