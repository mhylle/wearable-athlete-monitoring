"""Map Open Wearables data to local models."""

import uuid

from app.models.metric_record import MetricRecord
from app.models.session_metrics import SessionMetrics
from app.models.training_session import TrainingSession
from app.services.ow_schemas import OWDataPoint, OWSleep, OWWorkout

# Map OW sport strings to our session_type values
_SPORT_TO_SESSION_TYPE: dict[str, str] = {
    "running": "training",
    "cycling": "training",
    "swimming": "training",
    "walking": "training",
    "hiking": "training",
    "strength_training": "gym",
    "gym": "gym",
    "yoga": "recovery",
    "other": "training",
}


def map_ow_workout_to_session(
    ow_workout: OWWorkout,
    athlete_id: uuid.UUID,
) -> tuple[TrainingSession, SessionMetrics | None]:
    """Convert an OW workout into a TrainingSession and optional SessionMetrics."""
    duration_minutes = None
    if ow_workout.duration_seconds is not None:
        duration_minutes = ow_workout.duration_seconds / 60.0

    session_type = _SPORT_TO_SESSION_TYPE.get(ow_workout.sport or "other", "training")

    session = TrainingSession(
        athlete_id=athlete_id,
        source="garmin",
        session_type=session_type,
        start_time=ow_workout.start_time,
        end_time=ow_workout.end_time,
        duration_minutes=duration_minutes,
        ow_event_id=ow_workout.id,
    )

    metrics = None
    if ow_workout.details:
        d = ow_workout.details
        metrics = SessionMetrics(
            hr_avg=d.hr_avg,
            hr_max=d.hr_max,
            hr_min=d.hr_min,
            distance_m=d.distance_m,
            energy_kcal=d.energy_kcal,
            steps=d.steps,
            max_speed_ms=d.max_speed_ms,
            elevation_gain_m=d.elevation_gain_m,
        )

    return session, metrics


def map_ow_timeseries_to_records(
    ow_data: list[OWDataPoint],
    athlete_id: uuid.UUID,
) -> list[MetricRecord]:
    """Convert OW time-series data points to MetricRecord instances."""
    return [
        MetricRecord(
            athlete_id=athlete_id,
            metric_type=dp.type,
            value=dp.value,
            recorded_at=dp.timestamp,
            source=dp.source or "garmin",
        )
        for dp in ow_data
    ]


def map_ow_sleep_to_records(
    ow_sleep: OWSleep,
    athlete_id: uuid.UUID,
) -> list[MetricRecord]:
    """Convert an OW sleep record into MetricRecord instances."""
    records: list[MetricRecord] = []
    ts = ow_sleep.end_time  # Use wake time as the recorded timestamp

    if ow_sleep.duration_minutes is not None:
        records.append(MetricRecord(
            athlete_id=athlete_id,
            metric_type="sleep_duration",
            value=ow_sleep.duration_minutes,
            recorded_at=ts,
            source="garmin",
            ow_series_id=ow_sleep.id,
        ))

    if ow_sleep.score is not None:
        records.append(MetricRecord(
            athlete_id=athlete_id,
            metric_type="sleep_score",
            value=ow_sleep.score,
            recorded_at=ts,
            source="garmin",
            ow_series_id=ow_sleep.id,
        ))

    if ow_sleep.details:
        d = ow_sleep.details
        for metric_type, value in [
            ("sleep_deep_min", d.deep_minutes),
            ("sleep_light_min", d.light_minutes),
            ("sleep_rem_min", d.rem_minutes),
            ("sleep_awake_min", d.awake_minutes),
        ]:
            if value is not None:
                records.append(MetricRecord(
                    athlete_id=athlete_id,
                    metric_type=metric_type,
                    value=value,
                    recorded_at=ts,
                    source="garmin",
                    ow_series_id=ow_sleep.id,
                ))

    return records
