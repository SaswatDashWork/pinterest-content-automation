from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models import SavedAutomation
from backend.schemas import SavedAutomationCreate, SavedAutomationResponse

router = APIRouter()


@router.post("/", response_model=SavedAutomationResponse, status_code=201)
async def create_automation(
    data: SavedAutomationCreate, db: AsyncSession = Depends(get_db)
) -> SavedAutomation:
    automation = SavedAutomation(**data.model_dump())
    db.add(automation)
    await db.commit()
    await db.refresh(automation)
    return automation


@router.get("/", response_model=List[SavedAutomationResponse])
async def list_automations(
    db: AsyncSession = Depends(get_db),
) -> List[SavedAutomation]:
    result = await db.execute(
        select(SavedAutomation).order_by(SavedAutomation.use_count.desc())
    )
    return list(result.scalars().all())


@router.get("/{automation_id}", response_model=SavedAutomationResponse)
async def get_automation(
    automation_id: int, db: AsyncSession = Depends(get_db)
) -> SavedAutomation:
    automation = await db.get(SavedAutomation, automation_id)
    if not automation:
        raise HTTPException(status_code=404, detail="Automation not found")
    return automation


@router.delete("/{automation_id}")
async def delete_automation(
    automation_id: int, db: AsyncSession = Depends(get_db)
) -> dict:
    automation = await db.get(SavedAutomation, automation_id)
    if not automation:
        raise HTTPException(status_code=404, detail="Automation not found")
    await db.delete(automation)
    await db.commit()
    return {"deleted": automation_id}


@router.post("/{automation_id}/increment")
async def increment_use_count(
    automation_id: int, db: AsyncSession = Depends(get_db)
) -> dict:
    automation = await db.get(SavedAutomation, automation_id)
    if not automation:
        raise HTTPException(status_code=404, detail="Automation not found")
    automation.use_count += 1
    await db.commit()
    return {"use_count": automation.use_count}
