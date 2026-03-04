"""Wellness service layer."""

import uuid
from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.wellness import TeamWellnessStatusItem, WellnessResponse
from app.models.wellness_entry import WellnessEntry
from app.repositories.user_repo import UserRepository
from app.repositories.wellness_repo import WellnessRepository


async def submit_wellness(
    db: AsyncSession,
    athlete_id: uuid.UUID,
    data: dict,
) -> WellnessEntry:
    """Submit a wellness entry for an athlete.

    Raises 409 if an entry already exists for the same athlete and date.
    """
    repo = WellnessRepository(db)
    entry_data = {**data, "athlete_id": athlete_id}
    try:
        return await repo.create_entry(entry_data)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Wellness entry already exists for this date",
        ) from None


async def update_wellness(
    db: AsyncSession,
    entry_id: uuid.UUID,
    athlete_id: uuid.UUID,
    data: dict,
) -> WellnessEntry:
    """Update a wellness entry. Only the owning athlete can update."""
    repo = WellnessRepository(db)
    entry = await repo.get_entry_by_id(entry_id)
    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wellness entry not found",
        )
    if entry.athlete_id != athlete_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this entry",
        )
    return await repo.update_entry(entry, data)


async def get_wellness_history(
    db: AsyncSession,
    athlete_id: uuid.UUID,
    start: date | None = None,
    end: date | None = None,
) -> list[WellnessEntry]:
    """Get wellness history for an athlete with optional date range."""
    repo = WellnessRepository(db)
    return await repo.list_entries(athlete_id, start=start, end=end)


async def get_latest_wellness(
    db: AsyncSession,
    athlete_id: uuid.UUID,
) -> WellnessEntry | None:
    """Get the latest wellness entry for an athlete."""
    repo = WellnessRepository(db)
    return await repo.get_latest_entry(athlete_id)


async def get_team_wellness_overview(
    db: AsyncSession,
    team_id: uuid.UUID,
) -> list[TeamWellnessStatusItem]:
    """Get today's wellness submission status for all team athletes."""
    user_repo = UserRepository(db)
    wellness_repo = WellnessRepository(db)

    athletes = await user_repo.list_athletes(team_id)
    today = date.today()

    results: list[TeamWellnessStatusItem] = []
    for athlete in athletes:
        entry = await wellness_repo.get_entry_by_athlete_and_date(
            athlete.id, today
        )
        latest = await wellness_repo.get_latest_entry(athlete.id)
        results.append(
            TeamWellnessStatusItem(
                athlete_id=athlete.id,
                athlete_name=athlete.full_name,
                submitted=entry is not None,
                latest_entry=WellnessResponse.model_validate(latest) if latest else None,
            )
        )

    return results
