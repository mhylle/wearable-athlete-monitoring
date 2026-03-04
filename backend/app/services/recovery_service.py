"""Recovery service layer -- orchestrates DB queries and pure analytics functions."""

from __future__ import annotations

from datetime import date, timedelta
from typing import TYPE_CHECKING

from sqlalchemy import select

from app.analytics.acwr import compute_acwr
from app.analytics.hrv import DailyHRV, compute_hrv_rolling_stats
from app.analytics.recovery_score import (
    RecoveryScore,
    WellnessInput,
    compute_recovery_score,
)
from app.analytics.sleep import (
    SleepRecord,
    compute_sleep_average,
    compute_sleep_summary,
)

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

    from app.analytics.acwr import ACWRResult
    from app.analytics.hrv import HRVStats
    from app.analytics.sleep import SleepSummary
from app.models.metric_record import MetricRecord
from app.models.user import User
from app.models.wellness_entry import WellnessEntry


async def get_hrv_analysis(
    db: AsyncSession,
    athlete_id: uuid.UUID,
    start: date,
    end: date,
) -> dict:
    """Get HRV trend analysis for an athlete over a date range.

    Returns a dict with daily HRV values, rolling stats, and trend.
    """
    stmt = (
        select(MetricRecord)
        .where(
            MetricRecord.athlete_id == athlete_id,
            MetricRecord.metric_type == "hrv_rmssd",
            MetricRecord.recorded_at >= start,
            MetricRecord.recorded_at <= end + timedelta(days=1),
        )
        .order_by(MetricRecord.recorded_at)
    )
    result = await db.execute(stmt)
    records = list(result.scalars().all())

    daily_hrv = [
        DailyHRV(date=rec.recorded_at.date(), rmssd_value=rec.value)
        for rec in records
    ]

    stats = compute_hrv_rolling_stats(daily_hrv)

    return {
        "athlete_id": athlete_id,
        "start": start,
        "end": end,
        "daily_values": [
            {"date": d.date, "rmssd": d.rmssd_value} for d in daily_hrv
        ],
        "stats": stats,
    }


async def get_sleep_analysis(
    db: AsyncSession,
    athlete_id: uuid.UUID,
    start: date,
    end: date,
) -> dict:
    """Get sleep analysis for an athlete over a date range.

    Returns a dict with daily sleep summaries and a 7-day average.
    """
    sleep_types = ["sleep_total", "sleep_deep", "sleep_rem", "sleep_light", "sleep_awake"]
    stmt = (
        select(MetricRecord)
        .where(
            MetricRecord.athlete_id == athlete_id,
            MetricRecord.metric_type.in_(sleep_types),
            MetricRecord.recorded_at >= start,
            MetricRecord.recorded_at <= end + timedelta(days=1),
        )
        .order_by(MetricRecord.recorded_at)
    )
    result = await db.execute(stmt)
    records = list(result.scalars().all())

    sleep_records = [
        SleepRecord(
            metric_type=rec.metric_type,
            value=rec.value,
            date=rec.recorded_at.date(),
        )
        for rec in records
    ]

    # Build summaries for each day in the range
    summaries: list[SleepSummary] = []
    current = start
    while current <= end:
        summary = compute_sleep_summary(sleep_records, current)
        if summary.total_minutes > 0:
            summaries.append(summary)
        current += timedelta(days=1)

    avg = compute_sleep_average(summaries)

    return {
        "athlete_id": athlete_id,
        "start": start,
        "end": end,
        "daily_summaries": summaries,
        "average": avg,
    }


async def get_recovery_score(
    db: AsyncSession,
    athlete_id: uuid.UUID,
    target_date: date,
) -> RecoveryScore:
    """Compute recovery score for an athlete on a given date.

    Gathers HRV stats (30-day baseline), last night's sleep,
    current ACWR, and latest wellness entry.
    """
    # HRV: 30-day baseline
    hrv_start = target_date - timedelta(days=30)
    hrv_stmt = (
        select(MetricRecord)
        .where(
            MetricRecord.athlete_id == athlete_id,
            MetricRecord.metric_type == "hrv_rmssd",
            MetricRecord.recorded_at >= hrv_start,
            MetricRecord.recorded_at <= target_date + timedelta(days=1),
        )
        .order_by(MetricRecord.recorded_at)
    )
    hrv_result = await db.execute(hrv_stmt)
    hrv_records = list(hrv_result.scalars().all())
    hrv_stats: HRVStats | None = None
    if hrv_records:
        daily_hrv = [
            DailyHRV(date=r.recorded_at.date(), rmssd_value=r.value) for r in hrv_records
        ]
        hrv_stats = compute_hrv_rolling_stats(daily_hrv)

    # Sleep: target date
    sleep_types = ["sleep_total", "sleep_deep", "sleep_rem", "sleep_light", "sleep_awake"]
    sleep_stmt = (
        select(MetricRecord)
        .where(
            MetricRecord.athlete_id == athlete_id,
            MetricRecord.metric_type.in_(sleep_types),
            MetricRecord.recorded_at >= target_date,
            MetricRecord.recorded_at <= target_date + timedelta(days=1),
        )
    )
    sleep_result = await db.execute(sleep_stmt)
    sleep_records_raw = list(sleep_result.scalars().all())
    sleep_summary: SleepSummary | None = None
    if sleep_records_raw:
        sleep_recs = [
            SleepRecord(metric_type=r.metric_type, value=r.value, date=r.recorded_at.date())
            for r in sleep_records_raw
        ]
        summary = compute_sleep_summary(sleep_recs, target_date)
        if summary.total_minutes > 0:
            sleep_summary = summary

    # ACWR: 28-day load data
    load_start = target_date - timedelta(days=28)
    load_stmt = (
        select(MetricRecord)
        .where(
            MetricRecord.athlete_id == athlete_id,
            MetricRecord.metric_type == "session_load",
            MetricRecord.recorded_at >= load_start,
            MetricRecord.recorded_at <= target_date + timedelta(days=1),
        )
        .order_by(MetricRecord.recorded_at)
    )
    load_result = await db.execute(load_stmt)
    load_records = list(load_result.scalars().all())

    acwr_result: ACWRResult | None = None
    if load_records:
        # Build daily loads array, filling zeros for missing days
        daily_loads: dict[date, float] = {}
        for r in load_records:
            d = r.recorded_at.date()
            daily_loads[d] = daily_loads.get(d, 0.0) + r.value
        loads_list = []
        current = load_start
        while current <= target_date:
            loads_list.append(daily_loads.get(current, 0.0))
            current += timedelta(days=1)
        acwr_result = compute_acwr(loads_list, target_date)

    # Wellness: latest entry on or before target date
    wellness_stmt = (
        select(WellnessEntry)
        .where(
            WellnessEntry.athlete_id == athlete_id,
            WellnessEntry.date <= target_date,
        )
        .order_by(WellnessEntry.date.desc())
        .limit(1)
    )
    wellness_result = await db.execute(wellness_stmt)
    wellness_entry = wellness_result.scalar_one_or_none()

    wellness_input: WellnessInput | None = None
    if wellness_entry is not None:
        wellness_input = WellnessInput(
            mood=wellness_entry.mood,
            soreness=wellness_entry.soreness,
            fatigue=wellness_entry.fatigue,
        )

    return compute_recovery_score(hrv_stats, sleep_summary, acwr_result, wellness_input)


async def get_team_recovery_overview(
    db: AsyncSession,
    team_id: uuid.UUID,
    target_date: date,
) -> list[dict]:
    """Get recovery scores for all athletes on a team.

    Returns a list of dicts with athlete_id, full_name, and recovery_score.
    """
    athletes_stmt = select(User).where(
        User.team_id == team_id,
        User.role == "athlete",
        User.is_active.is_(True),
    )
    athletes_result = await db.execute(athletes_stmt)
    athletes = list(athletes_result.scalars().all())

    overview = []
    for athlete in athletes:
        score = await get_recovery_score(db, athlete.id, target_date)
        overview.append({
            "athlete_id": athlete.id,
            "full_name": athlete.full_name,
            "recovery_score": score,
        })

    return overview
