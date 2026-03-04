"""Training session Pydantic schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class SessionCreateRequest(BaseModel):
    """Request body for creating a manual training session."""

    athlete_id: uuid.UUID
    session_type: str = Field(pattern=r"^(match|training|gym|recovery)$")
    start_time: datetime
    end_time: datetime | None = None
    duration_minutes: float | None = None
    notes: str | None = None


class SessionMetricsResponse(BaseModel):
    """Session metrics response."""

    id: uuid.UUID
    session_id: uuid.UUID
    hr_avg: float | None = None
    hr_max: float | None = None
    hr_min: float | None = None
    distance_m: float | None = None
    energy_kcal: float | None = None
    steps: int | None = None
    max_speed_ms: float | None = None
    elevation_gain_m: float | None = None

    model_config = {"from_attributes": True}


class SessionResponse(BaseModel):
    """Training session response."""

    id: uuid.UUID
    athlete_id: uuid.UUID
    source: str
    session_type: str
    start_time: datetime
    end_time: datetime | None = None
    duration_minutes: float | None = None
    ow_event_id: str | None = None
    notes: str | None = None
    created_by: uuid.UUID | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class SessionDetailResponse(BaseModel):
    """Training session with metrics."""

    session: SessionResponse
    metrics: SessionMetricsResponse | None = None


class SessionListResponse(BaseModel):
    """List of training sessions."""

    sessions: list[SessionResponse]
    count: int


class SessionFilterParams(BaseModel):
    """Query parameters for filtering sessions."""

    start: datetime | None = None
    end: datetime | None = None
    session_type: str | None = None
    source: str | None = None
