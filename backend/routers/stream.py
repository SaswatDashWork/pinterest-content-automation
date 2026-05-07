from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models import Execution

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory bus: execution_id -> list of subscriber queues
_subscribers: dict[int, list[asyncio.Queue]] = {}


def publish_event(execution_id: int, event: dict) -> None:
    """Called by the orchestrator/executor to broadcast a step event."""
    for queue in _subscribers.get(execution_id, []):
        try:
            queue.put_nowait(event)
        except asyncio.QueueFull:
            pass


async def _event_stream(
    execution_id: int, db: AsyncSession
) -> AsyncGenerator[str, None]:
    execution = await db.get(Execution, execution_id)
    if not execution:
        yield _sse({"type": "error", "error": "Execution not found"})
        return

    # If already done, stream a synthetic completion event and close
    if execution.status in ("completed", "failed"):
        yield _sse(
            {
                "type": "execution_complete",
                "execution_id": execution_id,
                "status": execution.status,
                "error": execution.error,
            }
        )
        return

    queue: asyncio.Queue = asyncio.Queue(maxsize=256)
    _subscribers.setdefault(execution_id, []).append(queue)

    try:
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=30.0)
            except asyncio.TimeoutError:
                # Heartbeat to keep the connection alive
                yield ": heartbeat\n\n"
                # Check if execution finished during the wait
                await db.refresh(execution)
                if execution.status in ("completed", "failed"):
                    break
                continue

            yield _sse(event)

            if event.get("type") == "execution_complete":
                break
    finally:
        subs = _subscribers.get(execution_id, [])
        if queue in subs:
            subs.remove(queue)


def _sse(payload: dict) -> str:
    payload.setdefault(
        "timestamp", datetime.now(timezone.utc).isoformat()
    )
    return f"data: {json.dumps(payload)}\n\n"


@router.get("/executions/{execution_id}/stream")
async def stream_execution(
    execution_id: int, db: AsyncSession = Depends(get_db)
) -> StreamingResponse:
    return StreamingResponse(
        _event_stream(execution_id, db),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
