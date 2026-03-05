"""Fitness score service layer -- orchestrates DB queries and analytics."""

from __future__ import annotations

from datetime import date, timedelta
from typing import TYPE_CHECKING

from sqlalchemy import select

from app.analytics.fitness_score import FitnessScore, compute_fitness_score
from app.analytics.trend_detection import (
    TrendResult,
    compute_trend_bonus,
    detect_trend,
)
from app.repositories.metric_agg_repo import DailyMetric, get_daily_metrics

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User

# Metric types to fetch for fitness score computation
_METRIC_TYPES = [
    "hrv_rmssd",
    "resting_heart_rate",
    "sleep_total",
    "sleep_quality",
    "steps",
]


async def compute_athlete_fitness(
    db: AsyncSession,
    athlete_id: uuid.UUID,
    target_date: date | None = None,
) -> dict:
    """Compute fitness score and trends for an athlete.

    Returns a dict with fitness_score and trends list.
    """
    if target_date is None:
        target_date = date.today()

    start = target_date - timedelta(days=28)

    # Fetch daily metrics for each type
    metric_data: dict[str, list[DailyMetric]] = {}
    for mt in _METRIC_TYPES:
        data = await get_daily_metrics(db, athlete_id, mt, start, target_date)
        if data:
            metric_data[mt] = data

    # Compute trends for each available metric
    trends: list[TrendResult] = []
    for mt, data in metric_data.items():
        trend = detect_trend(mt, data)
        if trend is not None:
            trends.append(trend)

    # Compute trend bonus from all trends
    trend_bonus = compute_trend_bonus(trends)

    # Compute composite fitness score
    fitness = compute_fitness_score(metric_data, trend_bonus=trend_bonus)

    return {
        "athlete_id": athlete_id,
        "fitness_score": fitness,
        "trends": trends,
        "date": target_date,
    }


async def compute_team_fitness(
    db: AsyncSession,
    team_id: uuid.UUID,
    target_date: date | None = None,
) -> list[dict]:
    """Compute fitness scores for all athletes on a team."""
    if target_date is None:
        target_date = date.today()

    athletes_stmt = select(User).where(
        User.team_id == team_id,
        User.role == "athlete",
        User.is_active.is_(True),
    )
    athletes_result = await db.execute(athletes_stmt)
    athletes = list(athletes_result.scalars().all())

    results = []
    for athlete in athletes:
        result = await compute_athlete_fitness(db, athlete.id, target_date)
        result["full_name"] = athlete.full_name
        results.append(result)

    return results
