"""Training load analytics service layer."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import TYPE_CHECKING

from app.analytics.acwr import ACWRResult, compute_acwr
from app.analytics.load_helpers import DailyLoad, aggregate_daily_loads
from app.analytics.monotony import compute_monotony, compute_strain
from app.repositories.session_repo import SessionRepository
from app.repositories.user_repo import UserRepository
from app.repositories.wellness_repo import WellnessRepository

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class TrainingLoadSummary:
    """Complete training load summary for an athlete."""

    acwr: ACWRResult
    monotony: float
    strain: float
    daily_loads: list[DailyLoad]
    total_load: float
    avg_daily_load: float


@dataclass
class AthleteACWR:
    """ACWR summary for a single athlete in team overview."""

    athlete_id: uuid.UUID
    full_name: str
    acwr: ACWRResult


async def get_acwr(
    db: AsyncSession,
    athlete_id: uuid.UUID,
    as_of_date: date,
    chronic_days: int = 28,
) -> ACWRResult:
    """Compute ACWR for an athlete as of a given date."""
    start = as_of_date - timedelta(days=chronic_days + 7)
    end = as_of_date

    session_repo = SessionRepository(db)
    wellness_repo = WellnessRepository(db)

    start_dt = datetime(start.year, start.month, start.day, tzinfo=UTC)
    end_dt = datetime(end.year, end.month, end.day, 23, 59, 59, tzinfo=UTC)

    sessions = await session_repo.list_sessions(
        athlete_id, start=start_dt, end=end_dt
    )
    wellness_entries = await wellness_repo.list_entries(
        athlete_id, start=start, end=end
    )

    wellness_by_date = {w.date: w for w in wellness_entries}
    daily_loads = aggregate_daily_loads(sessions, start, end, wellness_by_date)
    load_values = [dl.total_load for dl in daily_loads]

    return compute_acwr(load_values, as_of_date)


async def get_training_load_summary(
    db: AsyncSession,
    athlete_id: uuid.UUID,
    start: date,
    end: date,
) -> TrainingLoadSummary:
    """Get a full training load summary for an athlete over a date range."""
    # Fetch enough history for ACWR chronic window
    history_start = start - timedelta(days=28)

    session_repo = SessionRepository(db)
    wellness_repo = WellnessRepository(db)

    start_dt = datetime(
        history_start.year, history_start.month, history_start.day,
        tzinfo=UTC,
    )
    end_dt = datetime(end.year, end.month, end.day, 23, 59, 59, tzinfo=UTC)

    sessions = await session_repo.list_sessions(
        athlete_id, start=start_dt, end=end_dt
    )
    wellness_entries = await wellness_repo.list_entries(
        athlete_id, start=history_start, end=end
    )

    wellness_by_date = {w.date: w for w in wellness_entries}
    all_daily_loads = aggregate_daily_loads(
        sessions, history_start, end, wellness_by_date
    )
    all_load_values = [dl.total_load for dl in all_daily_loads]

    acwr_result = compute_acwr(all_load_values, end)

    # Get the requested range loads
    requested_daily_loads = [dl for dl in all_daily_loads if start <= dl.date <= end]
    requested_load_values = [dl.total_load for dl in requested_daily_loads]

    total_load = sum(requested_load_values)
    days_count = len(requested_load_values) or 1
    avg_daily_load = total_load / days_count

    monotony = compute_monotony(requested_load_values)
    strain_val = compute_strain(total_load, monotony)

    return TrainingLoadSummary(
        acwr=acwr_result,
        monotony=monotony,
        strain=strain_val,
        daily_loads=requested_daily_loads,
        total_load=total_load,
        avg_daily_load=avg_daily_load,
    )


async def get_team_acwr_overview(
    db: AsyncSession,
    team_id: uuid.UUID,
    as_of_date: date,
) -> list[AthleteACWR]:
    """Get ACWR overview for all athletes on a team."""
    user_repo = UserRepository(db)
    athletes = await user_repo.list_athletes(team_id)

    results: list[AthleteACWR] = []
    for athlete in athletes:
        acwr_result = await get_acwr(db, athlete.id, as_of_date)
        results.append(
            AthleteACWR(
                athlete_id=athlete.id,
                full_name=athlete.full_name,
                acwr=acwr_result,
            )
        )

    return results
