from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Optional

logger = logging.getLogger(__name__)


class ToolResult:
    __slots__ = ("success", "data", "error")

    def __init__(self, *, success: bool, data: Any = None, error: Optional[str] = None) -> None:
        self.success = success
        self.data = data
        self.error = error

    def to_dict(self) -> dict:
        return {"success": self.success, "data": self.data, "error": self.error}


class BaseTool(ABC):
    """Contract every tool must implement."""

    name: str = ""
    description: str = ""
    max_retries: int = 3
    retry_base_delay: float = 1.0

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        ...

    async def run(self, **kwargs) -> ToolResult:
        """Execute with exponential-backoff retry on failure."""
        last_error: str = "unknown"
        for attempt in range(self.max_retries):
            try:
                result = await self.execute(**kwargs)
                if result.success:
                    return result
                last_error = result.error or "tool returned failure"
            except Exception as exc:
                last_error = str(exc)
                logger.warning(
                    "[%s] attempt %d/%d failed: %s",
                    self.name, attempt + 1, self.max_retries, last_error,
                )
            if attempt < self.max_retries - 1:
                await asyncio.sleep(self.retry_base_delay * (2 ** attempt))
        return ToolResult(success=False, error=f"Failed after {self.max_retries} attempts: {last_error}")
