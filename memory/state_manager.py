from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class StateManager:
    """
    Holds mutable in-process state for a single execution run.
    Persisted fields (URL, step counts) are written back to the Execution row
    by the Orchestrator; this class owns only the in-memory mirror.
    """

    def __init__(self, db: AsyncSession, execution_id: int) -> None:
        self._db = db
        self.execution_id = execution_id
        self._state: Dict[str, Any] = {
            "current_url": None,
            "open_tabs": [],
            "logged_in_services": [],
            "task_progress": 0.0,
            "step_history": [],
            "failure_count": 0,
            "failures": [],
        }

    # ─── mutators ────────────────────────────────────────────────────────────────

    async def update_current_url(self, url: str) -> None:
        self._state["current_url"] = url
        logger.debug("[exec:%s] url=%s", self.execution_id, url)

    async def record_step(self, step: Dict) -> None:
        self._state["step_history"].append(step)

    async def record_failure(self, step: Dict, error: str) -> None:
        self._state["failure_count"] += 1
        self._state["failures"].append({"step": step, "error": error})

    async def update_progress(self, completed: int, total: int) -> None:
        self._state["task_progress"] = round(completed / total, 2) if total else 0.0

    async def set_logged_in(self, service: str) -> None:
        if service not in self._state["logged_in_services"]:
            self._state["logged_in_services"].append(service)

    # ─── accessors ───────────────────────────────────────────────────────────────

    def get_current_url(self) -> Optional[str]:
        return self._state["current_url"]

    def get_progress(self) -> float:
        return self._state["task_progress"]

    def snapshot(self) -> Dict[str, Any]:
        return dict(self._state)
