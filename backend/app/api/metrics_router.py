"""Metrics API endpoints for querying raw daily-aggregated metric data."""

import uuid
from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.metrics import (
    AvailableMetricsResponse,
    DailyMetricDataPoint,
    DailyMetricsResponse,
)
from app.auth.dependencies import get_current_user
from app.db import get_db
from app.models.metric_record import MetricRecord
from app.models.user import User
from app.repositories.metric_agg_repo import get_daily_metrics

metrics_router = APIRouter(prefix="/api/v1/metrics", tags=["metrics"])


@metrics_router.get(
    "/athlete/{athlete_id}/daily", response_model=DailyMetricsResponse
)
async def get_athlete_daily_metrics(
    athlete_id: uuid.UUID,
    metric_type: str = Query(..., description="Metric type to query"),
    start: date = Query(default=None, description="Start date (default: 30 days ago)"),
    end: date = Query(default=None, description="End date (default: today)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DailyMetricsResponse:
    """Get daily-aggregated metrics for an athlete."""
    if end is None:
        end = date.today()
    if start is None:
        start = end - timedelta(days=30)

    rows = await get_daily_metrics(db, athlete_id, metric_type, start, end)

    return DailyMetricsResponse(
        metric_type=metric_type,
        start=start,
        end=end,
        data=[
            DailyMetricDataPoint(
                date=row.bucket,
                avg=row.avg_value,
                min=row.min_value,
                max=row.max_value,
                count=row.sample_count,
            )
            for row in rows
        ],
    )


@metrics_router.get(
    "/athlete/{athlete_id}/available", response_model=AvailableMetricsResponse
)
async def get_athlete_available_metrics(
    athlete_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AvailableMetricsResponse:
    """Get which metric types have data for an athlete."""
    result = await db.execute(
        select(MetricRecord.metric_type)
        .where(MetricRecord.athlete_id == athlete_id)
        .distinct()
        .order_by(MetricRecord.metric_type)
    )
    metric_types = [row[0] for row in result.all()]

    return AvailableMetricsResponse(
        athlete_id=athlete_id,
        metric_types=metric_types,
    )
