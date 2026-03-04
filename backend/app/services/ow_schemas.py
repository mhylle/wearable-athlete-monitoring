"""Pydantic models for Open Wearables API responses."""

from datetime import datetime

from pydantic import BaseModel


class OWUser(BaseModel):
    """Open Wearables user."""

    id: str
    email: str
    first_name: str
    last_name: str
    created_at: datetime | None = None


class OWConnection(BaseModel):
    """Open Wearables provider connection."""

    id: str
    user_id: str
    provider: str  # e.g. "garmin"
    status: str  # e.g. "active", "disconnected"
    connected_at: datetime | None = None


class OWDataPoint(BaseModel):
    """Open Wearables time-series data point."""

    timestamp: datetime
    type: str  # e.g. "resting_hr", "hrv_rmssd", "steps", "body_battery"
    value: float
    source: str | None = None


class OWWorkoutDetails(BaseModel):
    """Workout aggregate metrics from OW."""

    hr_avg: float | None = None
    hr_max: float | None = None
    hr_min: float | None = None
    distance_m: float | None = None
    energy_kcal: float | None = None
    steps: int | None = None
    max_speed_ms: float | None = None
    elevation_gain_m: float | None = None


class OWWorkout(BaseModel):
    """Open Wearables workout/activity."""

    id: str
    user_id: str
    sport: str | None = None
    start_time: datetime
    end_time: datetime | None = None
    duration_seconds: float | None = None
    source: str = "garmin"
    details: OWWorkoutDetails | None = None


class OWSleepDetails(BaseModel):
    """Sleep stage breakdown from OW."""

    deep_minutes: float | None = None
    light_minutes: float | None = None
    rem_minutes: float | None = None
    awake_minutes: float | None = None


class OWSleep(BaseModel):
    """Open Wearables sleep record."""

    id: str
    user_id: str
    start_time: datetime
    end_time: datetime
    duration_minutes: float | None = None
    score: float | None = None
    source: str = "garmin"
    details: OWSleepDetails | None = None


class SyncResult(BaseModel):
    """Result of a sync operation."""

    athlete_id: str
    records_synced: int = 0
    records_skipped: int = 0
    errors: list[str] = []


class ConnectionStatus(BaseModel):
    """Garmin connection status for an athlete."""

    connected: bool = False
    provider: str = "garmin"
    connection_id: str | None = None
    connected_at: datetime | None = None
