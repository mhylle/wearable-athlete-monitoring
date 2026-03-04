"""Health Connect sync service -- ingests data pushed from the mobile app."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.health_connect import (
    HCExerciseSession,
    HCMetricRecord,
    HCSyncRequest,
    HCSyncResponse,
)
from app.models.athlete_profile import AthleteProfile
from app.models.metric_record import MetricRecord
from app.models.session_metrics import SessionMetrics
from app.models.training_session import TrainingSession

# Map Health Connect exercise types to our session_type values
_HC_EXERCISE_TO_SESSION_TYPE: dict[str, str] = {
    "running": "training",
    "cycling": "training",
    "swimming": "training",
    "walking": "training",
    "hiking": "training",
    "strength_training": "gym",
    "weightlifting": "gym",
    "yoga": "recovery",
    "pilates": "recovery",
    "stretching": "recovery",
    "football": "match",
    "soccer": "match",
    "basketball": "match",
    "tennis": "match",
    "other": "training",
}


async def ingest_health_data(
    db: AsyncSession,
    athlete_id: uuid.UUID,
    request: HCSyncRequest,
) -> HCSyncResponse:
    """Ingest a batch of Health Connect data for an athlete.

    Uses upsert (ON CONFLICT DO NOTHING) for MetricRecord deduplication
    since it has a composite PK (athlete_id, metric_type, recorded_at).
    """
    response = HCSyncResponse()

    # Ingest metric records
    for metric in request.metrics:
        synced = await _ingest_metric(db, athlete_id, metric)
        if synced:
            response.metrics_synced += 1
        else:
            response.metrics_skipped += 1

    # Ingest exercise sessions
    for session in request.exercise_sessions:
        synced = await _ingest_exercise_session(db, athlete_id, session)
        if synced:
            response.sessions_synced += 1
        else:
            response.sessions_skipped += 1

    # Update athlete profile sync status
    await _update_sync_status(db, athlete_id)

    await db.commit()
    return response


async def _ingest_metric(
    db: AsyncSession,
    athlete_id: uuid.UUID,
    metric: HCMetricRecord,
) -> bool:
    """Insert a single metric record, skipping duplicates via composite PK."""
    # Check if record already exists (composite PK dedup)
    result = await db.execute(
        select(MetricRecord).where(
            MetricRecord.athlete_id == athlete_id,
            MetricRecord.metric_type == metric.metric_type,
            MetricRecord.recorded_at == metric.recorded_at,
        )
    )
    if result.scalar_one_or_none() is not None:
        return False

    record = MetricRecord(
        athlete_id=athlete_id,
        metric_type=metric.metric_type,
        value=metric.value,
        recorded_at=metric.recorded_at,
        source="health_connect",
    )
    db.add(record)
    return True


async def _ingest_exercise_session(
    db: AsyncSession,
    athlete_id: uuid.UUID,
    session: HCExerciseSession,
) -> bool:
    """Insert an exercise session, deduplicating by hc_record_id or time match."""
    # Dedup by hc_record_id if provided
    if session.hc_record_id:
        result = await db.execute(
            select(TrainingSession).where(
                TrainingSession.ow_event_id == session.hc_record_id
            )
        )
        if result.scalar_one_or_none() is not None:
            return False

    # Also dedup by exact time match for same athlete + source
    result = await db.execute(
        select(TrainingSession).where(
            TrainingSession.athlete_id == athlete_id,
            TrainingSession.source == "health_connect",
            TrainingSession.start_time == session.start_time,
        )
    )
    if result.scalar_one_or_none() is not None:
        return False

    session_type = _HC_EXERCISE_TO_SESSION_TYPE.get(
        session.exercise_type.lower(), "training"
    )

    ts = TrainingSession(
        athlete_id=athlete_id,
        source="health_connect",
        session_type=session_type,
        start_time=session.start_time,
        end_time=session.end_time,
        duration_minutes=session.duration_minutes,
        ow_event_id=session.hc_record_id,
    )
    db.add(ts)
    await db.flush()  # Get the ID for session_metrics

    # Create session metrics if any were provided
    if any([session.hr_avg, session.hr_max, session.hr_min,
            session.distance_m, session.energy_kcal, session.steps]):
        metrics = SessionMetrics(
            session_id=ts.id,
            hr_avg=session.hr_avg,
            hr_max=session.hr_max,
            hr_min=session.hr_min,
            distance_m=session.distance_m,
            energy_kcal=session.energy_kcal,
            steps=session.steps,
        )
        db.add(metrics)

    return True


async def _update_sync_status(
    db: AsyncSession,
    athlete_id: uuid.UUID,
) -> None:
    """Update the athlete's Health Connect sync status.

    Creates an AthleteProfile if one doesn't exist (e.g. for coach users
    syncing their own health data from a phone).
    """
    result = await db.execute(
        select(AthleteProfile).where(AthleteProfile.user_id == athlete_id)
    )
    profile = result.scalar_one_or_none()
    if profile is None:
        profile = AthleteProfile(user_id=athlete_id)
        db.add(profile)
    profile.health_connect_connected = True
    profile.last_health_connect_sync_at = datetime.now(timezone.utc)


async def get_sync_status(
    db: AsyncSession,
    athlete_id: uuid.UUID,
) -> dict:
    """Get the Health Connect sync status for an athlete."""
    result = await db.execute(
        select(AthleteProfile).where(AthleteProfile.user_id == athlete_id)
    )
    profile = result.scalar_one_or_none()
    if profile is None:
        return {
            "connected": False,
            "last_sync_at": None,
        }
    return {
        "connected": profile.health_connect_connected,
        "last_sync_at": profile.last_health_connect_sync_at,
    }
