from __future__ import annotations

import asyncio
import logging
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db, async_session
from backend.models import Execution, ExecutionStep
from backend.schemas import ExecutionCreate, ExecutionResponse, StepResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=ExecutionResponse, status_code=201)
async def create_execution(
    data: ExecutionCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> Execution:
    execution = Execution(
        command=data.command,
        workflow_id=data.workflow_id,
        status="pending",
        screenshots=[],
        logs=[],
    )
    db.add(execution)
    await db.commit()
    await db.refresh(execution)

    background_tasks.add_task(_run_execution, execution.id, data.command)
    return execution


@router.get("/", response_model=List[ExecutionResponse])
async def list_executions(
    limit: int = 20, db: AsyncSession = Depends(get_db)
) -> List[Execution]:
    result = await db.execute(
        select(Execution).order_by(desc(Execution.created_at)).limit(limit)
    )
    return list(result.scalars().all())


@router.get("/{execution_id}", response_model=ExecutionResponse)
async def get_execution(
    execution_id: int, db: AsyncSession = Depends(get_db)
) -> Execution:
    execution = await db.get(Execution, execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    return execution


@router.get("/{execution_id}/steps", response_model=List[StepResponse])
async def get_execution_steps(
    execution_id: int, db: AsyncSession = Depends(get_db)
) -> List[ExecutionStep]:
    result = await db.execute(
        select(ExecutionStep)
        .where(ExecutionStep.execution_id == execution_id)
        .order_by(ExecutionStep.step_index)
    )
    return list(result.scalars().all())


async def _run_execution(execution_id: int, command: str) -> None:
    """Background task that runs inside its own DB session."""
    async with async_session() as db:
        try:
            from agents.orchestrator import Orchestrator

            orchestrator = Orchestrator(db)
            await orchestrator.run(execution_id, command)
        except Exception as exc:
            logger.error("Execution %s crashed: %s", execution_id, exc)
            execution = await db.get(Execution, execution_id)
            if execution:
                execution.status = "failed"
                execution.error = str(exc)
                await db.commit()
