from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

from sqlalchemy.ext.asyncio import AsyncSession

from agents.executor import ExecutorAgent
from agents.planner import PlannerAgent
from backend.models import Execution, ExecutionStep
from backend.routers.stream import publish_event
from memory.state_manager import StateManager

logger = logging.getLogger(__name__)

MAX_REPLAN_ATTEMPTS = 2


class Orchestrator:
    """
    Ties together Planner → Executor → StateManager with a self-healing replan loop.

    Observe → Plan → Execute → Evaluate → (replan if needed) → repeat
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._planner = PlannerAgent()

    async def run(self, execution_id: int, command: str) -> Dict[str, Any]:
        execution = await self._db.get(Execution, execution_id)
        if not execution:
            raise ValueError(f"Execution {execution_id} not found")

        execution.status = "running"
        execution.started_at = datetime.now(timezone.utc)
        await self._db.commit()

        try:
            plan = await self._planner.create_plan(command)
            execution.plan = plan
            execution.total_steps = len(plan)
            await self._db.commit()

            state = StateManager(self._db, execution_id)
            result = await self._execute_with_recovery(
                execution_id, command, plan, state
            )

            execution.status = result["status"]
            execution.result = {k: v for k, v in result.items() if k != "completed_steps"}
            execution.completed_at = datetime.now(timezone.utc)
            await self._db.commit()

            publish_event(
                execution_id,
                {
                    "type": "execution_complete",
                    "execution_id": execution_id,
                    "status": result["status"],
                    "error": result.get("error"),
                },
            )
            return result

        except Exception as exc:
            logger.error("Orchestrator fatal error for execution %s: %s", execution_id, exc)
            execution.status = "failed"
            execution.error = str(exc)
            execution.completed_at = datetime.now(timezone.utc)
            await self._db.commit()
            publish_event(
                execution_id,
                {"type": "execution_complete", "execution_id": execution_id,
                 "status": "failed", "error": str(exc)},
            )
            raise

    async def _execute_with_recovery(
        self,
        execution_id: int,
        command: str,
        plan: List[Dict],
        state: StateManager,
        attempt: int = 0,
    ) -> Dict[str, Any]:
        executor = ExecutorAgent(execution_id)
        executor.set_progress_callback(
            lambda idx, step, status, result=None, error=None:
            self._on_step_progress(execution_id, idx, step, status, result, error)
        )

        result = await executor.execute_plan(
            plan,
            on_step_complete=lambda idx, step, outcome:
                self._persist_step(execution_id, idx, step, outcome),
        )

        if result["status"] == "failed" and attempt < MAX_REPLAN_ATTEMPTS:
            logger.info(
                "Replanning execution %s (attempt %s/%s)",
                execution_id, attempt + 1, MAX_REPLAN_ATTEMPTS,
            )
            recovery = await self._planner.replan(
                command,
                result.get("completed_steps", []),
                result.get("failed_step", {}),
                result.get("error", "Unknown error"),
            )
            if recovery:
                return await self._execute_with_recovery(
                    execution_id, command, recovery, state, attempt + 1
                )

        return result

    async def _persist_step(
        self,
        execution_id: int,
        idx: int,
        step: Dict,
        outcome: Dict,
    ) -> None:
        execution = await self._db.get(Execution, execution_id)
        if execution:
            execution.steps_completed = idx + 1
            execution.current_step = step.get("description") or step.get("action", "")

        step_record = ExecutionStep(
            execution_id=execution_id,
            step_index=idx,
            action=step.get("action", ""),
            params={k: v for k, v in step.items() if k not in ("action", "description")},
            status=outcome["status"],
            result=outcome.get("result"),
            error=outcome.get("error"),
            screenshot=outcome.get("screenshot"),
            duration_ms=outcome.get("duration_ms"),
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
        )
        self._db.add(step_record)
        await self._db.commit()

    async def _on_step_progress(
        self,
        execution_id: int,
        idx: int,
        step: Dict,
        status: str,
        result: Any = None,
        error: str = None,
    ) -> None:
        publish_event(
            execution_id,
            {
                "type": f"step_{status}",  # step_running | step_completed | step_failed
                "execution_id": execution_id,
                "step_index": idx,
                "action": step.get("action"),
                "description": step.get("description"),
                "status": status,
                "result": result,
                "error": error,
            },
        )
