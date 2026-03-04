"""Data synchronization from Open Wearables to local database."""

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.metric_record import MetricRecord
from app.models.training_session import TrainingSession
from app.models.user import User
from app.services.ow_client import OWClient
from app.services.ow_mapper import (
    map_ow_sleep_to_records,
    map_ow_timeseries_to_records,
    map_ow_workout_to_session,
)
from app.services.ow_schemas import SyncResult

# Default timeseries types to fetch from OW
DEFAULT_TIMESERIES_TYPES = [
    "resting_hr",
    "hrv_rmssd",
    "steps",
    "body_battery",
    "stress",
]


async def sync_athlete_timeseries(
    athlete: User,
    start: datetime,
    end: datetime,
    client: OWClient,
    db: AsyncSession,
) -> SyncResult:
    """Sync time-series data for a single athlete."""
    result = SyncResult(athlete_id=str(athlete.id))

    if not athlete.ow_user_id:
        result.errors.append("Athlete not provisioned in Open Wearables")
        return result

    try:
        ow_data = await client.get_timeseries(
            athlete.ow_user_id,
            types=DEFAULT_TIMESERIES_TYPES,
            start=start,
            end=end,
        )
    except Exception as exc:
        result.errors.append(f"Failed to fetch timeseries: {exc}")
        return result

    records = map_ow_timeseries_to_records(ow_data, athlete.id)

    for record in records:
        # Deduplicate by composite key
        existing = await db.execute(
            select(MetricRecord).where(
                MetricRecord.athlete_id == record.athlete_id,
                MetricRecord.metric_type == record.metric_type,
                MetricRecord.recorded_at == record.recorded_at,
            )
        )
        if existing.scalar_one_or_none() is not None:
            result.records_skipped += 1
            continue

        db.add(record)
        result.records_synced += 1

    await db.commit()
    return result


async def sync_athlete_workouts(
    athlete: User,
    start: datetime,
    end: datetime,
    client: OWClient,
    db: AsyncSession,
) -> SyncResult:
    """Sync workouts for a single athlete."""
    result = SyncResult(athlete_id=str(athlete.id))

    if not athlete.ow_user_id:
        result.errors.append("Athlete not provisioned in Open Wearables")
        return result

    try:
        ow_workouts = await client.get_workouts(athlete.ow_user_id, start=start, end=end)
    except Exception as exc:
        result.errors.append(f"Failed to fetch workouts: {exc}")
        return result

    for ow_workout in ow_workouts:
        # Deduplicate by ow_event_id
        existing = await db.execute(
            select(TrainingSession).where(
                TrainingSession.ow_event_id == ow_workout.id,
            )
        )
        if existing.scalar_one_or_none() is not None:
            result.records_skipped += 1
            continue

        session, metrics = map_ow_workout_to_session(ow_workout, athlete.id)
        db.add(session)
        await db.flush()  # Get session.id assigned

        if metrics:
            metrics.session_id = session.id
            db.add(metrics)

        result.records_synced += 1

    await db.commit()
    return result


async def sync_athlete_sleep(
    athlete: User,
    start: datetime,
    end: datetime,
    client: OWClient,
    db: AsyncSession,
) -> SyncResult:
    """Sync sleep data for a single athlete."""
    result = SyncResult(athlete_id=str(athlete.id))

    if not athlete.ow_user_id:
        result.errors.append("Athlete not provisioned in Open Wearables")
        return result

    try:
        ow_sleep_records = await client.get_sleep(athlete.ow_user_id, start=start, end=end)
    except Exception as exc:
        result.errors.append(f"Failed to fetch sleep data: {exc}")
        return result

    for ow_sleep in ow_sleep_records:
        records = map_ow_sleep_to_records(ow_sleep, athlete.id)

        for record in records:
            # Deduplicate by ow_series_id + metric_type
            existing = await db.execute(
                select(MetricRecord).where(
                    MetricRecord.athlete_id == record.athlete_id,
                    MetricRecord.metric_type == record.metric_type,
                    MetricRecord.recorded_at == record.recorded_at,
                )
            )
            if existing.scalar_one_or_none() is not None:
                result.records_skipped += 1
                continue

            db.add(record)
            result.records_synced += 1

    await db.commit()
    return result


async def sync_all_athletes(
    team_id: uuid.UUID,
    start: datetime,
    end: datetime,
    client: OWClient,
    db: AsyncSession,
) -> list[SyncResult]:
    """Sync data for all athletes in a team that have OW accounts."""
    query = select(User).where(
        User.team_id == team_id,
        User.role == "athlete",
        User.ow_user_id.isnot(None),
        User.is_active.is_(True),
    )
    result = await db.execute(query)
    athletes = list(result.scalars().all())

    all_results: list[SyncResult] = []
    for athlete in athletes:
        ts_result = await sync_athlete_timeseries(athlete, start, end, client, db)
        wo_result = await sync_athlete_workouts(athlete, start, end, client, db)
        sl_result = await sync_athlete_sleep(athlete, start, end, client, db)

        combined = SyncResult(
            athlete_id=str(athlete.id),
            records_synced=ts_result.records_synced + wo_result.records_synced + sl_result.records_synced,
            records_skipped=ts_result.records_skipped + wo_result.records_skipped + sl_result.records_skipped,
            errors=ts_result.errors + wo_result.errors + sl_result.errors,
        )
        all_results.append(combined)

    return all_results
