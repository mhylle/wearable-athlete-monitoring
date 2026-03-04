"""Pydantic schemas for Health Connect data ingestion from mobile app."""

from datetime import datetime

from pydantic import BaseModel, Field


class HCMetricRecord(BaseModel):
    """A single metric data point from Health Connect."""

    metric_type: str = Field(
        ...,
        description="Type of metric: heart_rate, hrv, resting_heart_rate, steps, "
        "sleep_duration, sleep_score, sleep_deep_min, sleep_light_min, "
        "sleep_rem_min, sleep_awake_min, vo2max, spo2, respiratory_rate",
    )
    value: float
    recorded_at: datetime


class HCExerciseSession(BaseModel):
    """An exercise session from Health Connect."""

    exercise_type: str = Field(
        ...,
        description="Health Connect exercise type string, e.g. running, cycling, swimming",
    )
    start_time: datetime
    end_time: datetime | None = None
    duration_minutes: float | None = None
    hr_avg: float | None = None
    hr_max: float | None = None
    hr_min: float | None = None
    distance_m: float | None = None
    energy_kcal: float | None = None
    steps: int | None = None
    hc_record_id: str | None = Field(
        None, description="Health Connect record ID for deduplication"
    )


class HCSyncRequest(BaseModel):
    """Batch sync request from mobile app."""

    metrics: list[HCMetricRecord] = Field(default_factory=list)
    exercise_sessions: list[HCExerciseSession] = Field(default_factory=list)
    changes_token: str | None = Field(
        None, description="Health Connect changes token for incremental sync tracking"
    )


class HCSyncResponse(BaseModel):
    """Response from a sync operation."""

    metrics_synced: int = 0
    metrics_skipped: int = 0
    sessions_synced: int = 0
    sessions_skipped: int = 0
    errors: list[str] = Field(default_factory=list)


class HCSyncStatus(BaseModel):
    """Health Connect sync status for an athlete."""

    connected: bool
    last_sync_at: datetime | None = None
    changes_token: str | None = None
