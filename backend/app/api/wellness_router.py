"""Wellness API router."""

import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.wellness import (
    TeamWellnessStatusItem,
    WellnessCreateRequest,
    WellnessHistoryResponse,
    WellnessResponse,
    WellnessUpdateRequest,
)
from app.auth.dependencies import get_current_user, require_athlete, require_coach
from app.db import get_db
from app.models.user import User
from app.services import wellness_service

router = APIRouter(prefix="/api/v1/wellness", tags=["wellness"])


@router.post("/", response_model=WellnessResponse, status_code=status.HTTP_201_CREATED)
async def submit_wellness(
    body: WellnessCreateRequest,
    athlete: User = Depends(require_athlete),
    db: AsyncSession = Depends(get_db),
) -> WellnessResponse:
    """Submit a wellness entry (athlete only, one per day)."""
    entry = await wellness_service.submit_wellness(
        db,
        athlete.id,
        body.model_dump(exclude_unset=True),
    )
    return WellnessResponse.model_validate(entry)


@router.put("/{entry_id}", response_model=WellnessResponse)
async def update_wellness(
    entry_id: uuid.UUID,
    body: WellnessUpdateRequest,
    athlete: User = Depends(require_athlete),
    db: AsyncSession = Depends(get_db),
) -> WellnessResponse:
    """Update a wellness entry (athlete only, own entry)."""
    entry = await wellness_service.update_wellness(
        db,
        entry_id,
        athlete.id,
        body.model_dump(exclude_unset=True),
    )
    return WellnessResponse.model_validate(entry)


@router.get(
    "/athlete/{athlete_id}",
    response_model=WellnessHistoryResponse,
)
async def get_wellness_history(
    athlete_id: uuid.UUID,
    start: date | None = Query(default=None),
    end: date | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WellnessHistoryResponse:
    """Get wellness history for an athlete (coach or self)."""
    if current_user.role != "coach" and current_user.id != athlete_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this wellness data",
        )

    entries = await wellness_service.get_wellness_history(
        db, athlete_id, start=start, end=end
    )
    return WellnessHistoryResponse(
        entries=[WellnessResponse.model_validate(e) for e in entries],
        count=len(entries),
    )


@router.get(
    "/athlete/{athlete_id}/latest",
    response_model=WellnessResponse | None,
)
async def get_latest_wellness(
    athlete_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WellnessResponse | None:
    """Get the latest wellness entry for an athlete."""
    if current_user.role != "coach" and current_user.id != athlete_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this wellness data",
        )

    entry = await wellness_service.get_latest_wellness(db, athlete_id)
    if entry is None:
        return None
    return WellnessResponse.model_validate(entry)


@router.get(
    "/team/overview",
    response_model=list[TeamWellnessStatusItem],
)
async def get_team_wellness_overview(
    current_user: User = Depends(require_coach),
    db: AsyncSession = Depends(get_db),
) -> list[TeamWellnessStatusItem]:
    """Get today's wellness submission status for all team athletes."""
    return await wellness_service.get_team_wellness_overview(
        db, current_user.team_id
    )
