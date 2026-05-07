from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import Execution, SavedAutomation

logger = logging.getLogger(__name__)


class MemoryLayer:
    """
    Persists successful workflows and provides recall for similar past runs.
    Future enhancement: swap keyword search for vector similarity (ChromaDB).
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def save_workflow(
        self,
        name: str,
        command: str,
        plan: List[Dict],
        tags: Optional[List[str]] = None,
        description: str = "",
    ) -> SavedAutomation:
        automation = SavedAutomation(
            name=name,
            description=description,
            command_template=command,
            plan_template=plan,
            tags=tags or [],
        )
        self._db.add(automation)
        await self._db.commit()
        await self._db.refresh(automation)
        logger.info("Saved workflow: %s", name)
        return automation

    async def get_similar_workflows(
        self, command: str, limit: int = 5
    ) -> List[SavedAutomation]:
        # Naive most-used recall; replace with embedding search when ready
        result = await self._db.execute(
            select(SavedAutomation)
            .order_by(desc(SavedAutomation.use_count))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_recent_executions(self, limit: int = 10) -> List[Execution]:
        result = await self._db.execute(
            select(Execution)
            .order_by(desc(Execution.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def increment_use_count(self, automation_id: int) -> None:
        automation = await self._db.get(SavedAutomation, automation_id)
        if automation:
            automation.use_count += 1
            await self._db.commit()

    async def update_success_rate(
        self, automation_id: int, succeeded: bool
    ) -> None:
        automation = await self._db.get(SavedAutomation, automation_id)
        if not automation:
            return
        # Simple exponential moving average (alpha = 0.1)
        current = automation.success_rate
        new_val = int(current * 0.9 + (100 if succeeded else 0) * 0.1)
        automation.success_rate = new_val
        await self._db.commit()
