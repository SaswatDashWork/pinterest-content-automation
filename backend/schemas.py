from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


# ─── Workflow ────────────────────────────────────────────────────────────────────────
class WorkflowCreate(BaseModel):
    name: str
    description: Optional[str] = None
    command: str


class WorkflowResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str
    description: Optional[str]
    command: str
    plan: Optional[List[Dict[str, Any]]]
    created_at: datetime


# ─── Execution ─────────────────────────────────────────────────────────────────────
class ExecutionCreate(BaseModel):
    command: str
    workflow_id: Optional[int] = None


class ExecutionResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    workflow_id: Optional[int]
    command: str
    status: str
    plan: Optional[List[Dict[str, Any]]]
    steps_completed: int
    total_steps: int
    current_step: Optional[str]
    result: Optional[Dict[str, Any]]
    error: Optional[str]
    screenshots: List[Any]
    logs: List[Any]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime


class StepResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    execution_id: int
    step_index: int
    action: str
    params: Optional[Dict[str, Any]]
    status: str
    result: Optional[Dict[str, Any]]
    error: Optional[str]
    screenshot: Optional[str]
    duration_ms: Optional[int]


# ─── Saved Automation ───────────────────────────────────────────────────────────────
class SavedAutomationCreate(BaseModel):
    name: str
    description: Optional[str] = None
    command_template: str
    tags: List[str] = []


class SavedAutomationResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str
    description: Optional[str]
    command_template: str
    tags: List[Any]
    use_count: int
    success_rate: int
    created_at: datetime


# ─── SSE event ──────────────────────────────────────────────────────────────────────
class StreamEvent(BaseModel):
    type: str  # step_start | step_complete | step_failed | execution_complete | error
    execution_id: int
    step_index: Optional[int] = None
    action: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    screenshot: Optional[str] = None
    progress: Optional[float] = None  # 0.0 – 1.0
    timestamp: Optional[datetime] = None
