"""Anomaly detection service - bridges analytics with database."""

from __future__ import annotations

import uuid
from datetime import date, timedelta
from typing import TYPE_CHECKING

from sqlalchemy import select

from app.analytics.anomaly_detection import (
    detect_athlete_anomaly_vs_team,
    detect_metric_anomalies,
)
from app.analytics.anomaly_types import Anomaly, DatedValue
from app.models.anomaly_record import AnomalyRecord
from app.models.metric_record import MetricRecord
from app.models.user import User

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

# Metrics to scan for anomalies
SCAN_METRICS = [
    "resting_hr",
    "hrv_rmssd",
    "sleep_duration",
    "training_load",
    "body_battery",
]


async def _fetch_metric_values(
    db: AsyncSession,
    athlete_id: uuid.UUID,
    metric_type: str,
    start: date,
    end: date,
) -> list[DatedValue]:
    """Fetch metric values for an athlete within a date range."""
    from datetime import UTC, datetime

    start_dt = datetime(start.year, start.month, start.day, tzinfo=UTC)
    end_dt = datetime(end.year, end.month, end.day, 23, 59, 59, tzinfo=UTC)

    result = await db.execute(
        select(MetricRecord.recorded_at, MetricRecord.value)
        .where(
            MetricRecord.athlete_id == athlete_id,
            MetricRecord.metric_type == metric_type,
            MetricRecord.recorded_at >= start_dt,
            MetricRecord.recorded_at <= end_dt,
        )
        .order_by(MetricRecord.recorded_at)
    )
    rows = result.all()
    return [DatedValue(date=row[0].date(), value=row[1]) for row in rows]


async def scan_athlete_anomalies(
    db: AsyncSession,
    athlete_id: uuid.UUID,
    target_date: date,
    window_days: int = 30,
) -> list[Anomaly]:
    """Scan an athlete's recent metrics for anomalies.

    Fetches the last `window_days` of data for each metric and runs
    per-metric anomaly detection.
    """
    # Fetch athlete name
    result = await db.execute(
        select(User.full_name).where(User.id == athlete_id)
    )
    row = result.scalar_one_or_none()
    athlete_name = row if row else "Unknown"

    start = target_date - timedelta(days=window_days + 14)  # extra for baseline
    all_anomalies: list[Anomaly] = []

    for metric in SCAN_METRICS:
        values = await _fetch_metric_values(db, athlete_id, metric, start, target_date)
        anomalies = detect_metric_anomalies(
            values,
            athlete_id=str(athlete_id),
            metric_type=metric,
            athlete_name=athlete_name,
        )
        all_anomalies.extend(anomalies)

    return all_anomalies


async def scan_team_anomalies(
    db: AsyncSession,
    team_id: uuid.UUID,
    target_date: date,
) -> list[Anomaly]:
    """Scan team for per-athlete anomalies (compare each athlete to team distribution)."""
    # Get all active athletes on the team
    result = await db.execute(
        select(User.id, User.full_name).where(
            User.team_id == team_id,
            User.role == "athlete",
            User.is_active.is_(True),
        )
    )
    athletes = result.all()
    if len(athletes) < 3:
        return []

    from datetime import UTC, datetime

    # For each metric, get latest values for all athletes and compare
    day_start = datetime(target_date.year, target_date.month, target_date.day, tzinfo=UTC)
    day_end = datetime(target_date.year, target_date.month, target_date.day, 23, 59, 59, tzinfo=UTC)

    all_anomalies: list[Anomaly] = []

    for metric in SCAN_METRICS:
        # Fetch latest value per athlete for this metric
        athlete_values: dict[str, tuple[str, float]] = {}
        for athlete_id, athlete_name in athletes:
            result = await db.execute(
                select(MetricRecord.value)
                .where(
                    MetricRecord.athlete_id == athlete_id,
                    MetricRecord.metric_type == metric,
                    MetricRecord.recorded_at >= day_start,
                    MetricRecord.recorded_at <= day_end,
                )
                .order_by(MetricRecord.recorded_at.desc())
                .limit(1)
            )
            row = result.scalar_one_or_none()
            if row is not None:
                athlete_values[str(athlete_id)] = (athlete_name, row)

        if len(athlete_values) < 3:
            continue

        team_vals = [v for _, v in athlete_values.values()]
        detection_date = DatedValue(date=target_date, value=0)

        for aid, (aname, aval) in athlete_values.items():
            anomaly = detect_athlete_anomaly_vs_team(
                athlete_id=aid,
                athlete_name=aname,
                metric_type=metric,
                athlete_value=aval,
                team_values=team_vals,
                detection_date=detection_date,
            )
            if anomaly is not None:
                all_anomalies.append(anomaly)

    return all_anomalies


async def get_anomaly_history(
    db: AsyncSession,
    athlete_id: uuid.UUID,
    start: date,
    end: date,
) -> list[AnomalyRecord]:
    """Retrieve persisted anomaly records for an athlete within a date range."""
    result = await db.execute(
        select(AnomalyRecord)
        .where(
            AnomalyRecord.athlete_id == athlete_id,
            AnomalyRecord.detected_at >= start,
            AnomalyRecord.detected_at <= end,
        )
        .order_by(AnomalyRecord.detected_at.desc())
    )
    return list(result.scalars().all())


async def persist_anomalies(
    db: AsyncSession,
    anomalies: list[Anomaly],
) -> list[AnomalyRecord]:
    """Persist a list of anomalies as AnomalyRecord rows."""
    records = []
    for a in anomalies:
        record = AnomalyRecord(
            athlete_id=uuid.UUID(a.athlete_id),
            metric_type=a.metric_type,
            value=a.value,
            expected_median=a.expected_median,
            mad_score=a.mad_score,
            severity=a.severity,
            anomaly_type=a.anomaly_type,
            explanation=a.explanation,
            detected_at=a.detected_at,
        )
        db.add(record)
        records.append(record)
    await db.commit()
    return records
