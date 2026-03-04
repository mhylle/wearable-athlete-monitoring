"""Repository for querying metric aggregates and raw metric data."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import and_, func, select, text

from app.models.metric_record import MetricRecord
from app.models.user import User

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession


@dataclass(frozen=True)
class DailyMetric:
    """Aggregated metric values for a single day."""

    athlete_id: uuid.UUID
    metric_type: str
    bucket: date
    avg_value: float
    min_value: float
    max_value: float
    sample_count: int


@dataclass(frozen=True)
class WeeklyLoad:
    """Aggregated training load for a single week."""

    athlete_id: uuid.UUID
    bucket: date
    total_load: float
    avg_daily_load: float
    session_count: int


@dataclass(frozen=True)
class AthleteMetric:
    """Latest metric value for an athlete."""

    athlete_id: uuid.UUID
    full_name: str
    value: float
    recorded_at: datetime


async def get_daily_metrics(
    db: AsyncSession,
    athlete_id: uuid.UUID,
    metric_type: str,
    start: date,
    end: date,
) -> list[DailyMetric]:
    """Get daily aggregated metrics for an athlete.

    Queries the daily_metric_agg continuous aggregate when available,
    falling back to raw computation from metric_records.
    """
    start_dt = datetime(start.year, start.month, start.day, tzinfo=UTC)
    end_dt = datetime(end.year, end.month, end.day, 23, 59, 59, tzinfo=UTC)

    try:
        # Try continuous aggregate first
        result = await db.execute(
            text("""
                SELECT athlete_id, metric_type, bucket,
                       avg_value, min_value, max_value, sample_count
                FROM daily_metric_agg
                WHERE athlete_id = :athlete_id
                  AND metric_type = :metric_type
                  AND bucket >= :start AND bucket <= :end
                ORDER BY bucket
            """),
            {
                "athlete_id": athlete_id,
                "metric_type": metric_type,
                "start": start_dt,
                "end": end_dt,
            },
        )
    except Exception:
        # Fallback: compute from raw metric_records (works on SQLite too)
        result = await _daily_metrics_fallback(db, athlete_id, metric_type, start_dt, end_dt)
        return result

    return [
        DailyMetric(
            athlete_id=row[0],
            metric_type=row[1],
            bucket=row[2].date() if hasattr(row[2], "date") else row[2],
            avg_value=float(row[3]),
            min_value=float(row[4]),
            max_value=float(row[5]),
            sample_count=int(row[6]),
        )
        for row in result.all()
    ]


async def _daily_metrics_fallback(
    db: AsyncSession,
    athlete_id: uuid.UUID,
    metric_type: str,
    start_dt: datetime,
    end_dt: datetime,
) -> list[DailyMetric]:
    """Compute daily aggregates from raw metric_records (fallback)."""
    from sqlalchemy import cast
    from sqlalchemy.types import Date

    result = await db.execute(
        select(
            MetricRecord.athlete_id,
            MetricRecord.metric_type,
            cast(MetricRecord.recorded_at, Date).label("bucket"),
            func.avg(MetricRecord.value).label("avg_value"),
            func.min(MetricRecord.value).label("min_value"),
            func.max(MetricRecord.value).label("max_value"),
            func.count().label("sample_count"),
        )
        .where(
            MetricRecord.athlete_id == athlete_id,
            MetricRecord.metric_type == metric_type,
            MetricRecord.recorded_at >= start_dt,
            MetricRecord.recorded_at <= end_dt,
        )
        .group_by(
            MetricRecord.athlete_id,
            MetricRecord.metric_type,
            cast(MetricRecord.recorded_at, Date),
        )
        .order_by(cast(MetricRecord.recorded_at, Date))
    )

    return [
        DailyMetric(
            athlete_id=row[0],
            metric_type=row[1],
            bucket=row[2] if isinstance(row[2], date) else row[2],
            avg_value=float(row[3]),
            min_value=float(row[4]),
            max_value=float(row[5]),
            sample_count=int(row[6]),
        )
        for row in result.all()
    ]


async def get_weekly_loads(
    db: AsyncSession,
    athlete_id: uuid.UUID,
    start: date,
    end: date,
) -> list[WeeklyLoad]:
    """Get weekly training load aggregates for an athlete."""
    start_dt = datetime(start.year, start.month, start.day, tzinfo=UTC)
    end_dt = datetime(end.year, end.month, end.day, 23, 59, 59, tzinfo=UTC)

    try:
        result = await db.execute(
            text("""
                SELECT athlete_id, bucket, total_load, avg_daily_load, session_count
                FROM weekly_load_agg
                WHERE athlete_id = :athlete_id
                  AND bucket >= :start AND bucket <= :end
                ORDER BY bucket
            """),
            {"athlete_id": athlete_id, "start": start_dt, "end": end_dt},
        )
    except Exception:
        # Fallback for non-TimescaleDB (e.g. tests with SQLite)
        return await _weekly_loads_fallback(db, athlete_id, start_dt, end_dt)

    return [
        WeeklyLoad(
            athlete_id=row[0],
            bucket=row[1].date() if hasattr(row[1], "date") else row[1],
            total_load=float(row[2]),
            avg_daily_load=float(row[3]),
            session_count=int(row[4]),
        )
        for row in result.all()
    ]


async def _weekly_loads_fallback(
    db: AsyncSession,
    athlete_id: uuid.UUID,
    start_dt: datetime,
    end_dt: datetime,
) -> list[WeeklyLoad]:
    """Compute weekly loads from raw metric_records (fallback)."""
    result = await db.execute(
        select(
            MetricRecord.athlete_id,
            func.sum(MetricRecord.value).label("total_load"),
            func.avg(MetricRecord.value).label("avg_daily_load"),
            func.count().label("session_count"),
        )
        .where(
            MetricRecord.athlete_id == athlete_id,
            MetricRecord.metric_type == "training_load",
            MetricRecord.recorded_at >= start_dt,
            MetricRecord.recorded_at <= end_dt,
        )
        .group_by(MetricRecord.athlete_id)
    )

    return [
        WeeklyLoad(
            athlete_id=row[0],
            bucket=start_dt.date(),
            total_load=float(row[1]),
            avg_daily_load=float(row[2]),
            session_count=int(row[3]),
        )
        for row in result.all()
    ]


async def get_team_latest_metrics(
    db: AsyncSession,
    team_id: uuid.UUID,
    metric_type: str,
) -> list[AthleteMetric]:
    """Get the latest metric value for each athlete on a team.

    Uses a subquery to find the most recent recorded_at per athlete
    for the given metric_type.
    """
    # Subquery: latest recorded_at per athlete
    latest_sq = (
        select(
            MetricRecord.athlete_id,
            func.max(MetricRecord.recorded_at).label("max_recorded_at"),
        )
        .where(MetricRecord.metric_type == metric_type)
        .group_by(MetricRecord.athlete_id)
        .subquery()
    )

    result = await db.execute(
        select(
            User.id,
            User.full_name,
            MetricRecord.value,
            MetricRecord.recorded_at,
        )
        .join(latest_sq, and_(
            User.id == latest_sq.c.athlete_id,
        ))
        .join(MetricRecord, and_(
            MetricRecord.athlete_id == latest_sq.c.athlete_id,
            MetricRecord.metric_type == metric_type,
            MetricRecord.recorded_at == latest_sq.c.max_recorded_at,
        ))
        .where(
            User.team_id == team_id,
            User.role == "athlete",
            User.is_active.is_(True),
        )
        .order_by(User.full_name)
    )

    return [
        AthleteMetric(
            athlete_id=row[0],
            full_name=row[1],
            value=float(row[2]),
            recorded_at=row[3],
        )
        for row in result.all()
    ]
