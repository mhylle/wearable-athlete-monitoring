"""Wellness Pydantic schemas."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


class WellnessCreateRequest(BaseModel):
    """Request body for submitting a wellness entry."""

    date: date
    srpe: int | None = Field(default=None, ge=1, le=10)
    srpe_duration_min: float | None = None
    soreness: int | None = Field(default=None, ge=1, le=10)
    fatigue: int | None = Field(default=None, ge=1, le=10)
    mood: int | None = Field(default=None, ge=1, le=5)
    sleep_quality: int | None = Field(default=None, ge=1, le=5)
    notes: str | None = None


class WellnessUpdateRequest(BaseModel):
    """Request body for updating a wellness entry."""

    srpe: int | None = Field(default=None, ge=1, le=10)
    srpe_duration_min: float | None = None
    soreness: int | None = Field(default=None, ge=1, le=10)
    fatigue: int | None = Field(default=None, ge=1, le=10)
    mood: int | None = Field(default=None, ge=1, le=5)
    sleep_quality: int | None = Field(default=None, ge=1, le=5)
    notes: str | None = None


class WellnessResponse(BaseModel):
    """Wellness entry response."""

    id: uuid.UUID
    athlete_id: uuid.UUID
    date: date
    srpe: int | None = None
    srpe_duration_min: float | None = None
    soreness: int | None = None
    fatigue: int | None = None
    mood: int | None = None
    sleep_quality: int | None = None
    notes: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class WellnessHistoryResponse(BaseModel):
    """List of wellness entries."""

    entries: list[WellnessResponse]
    count: int


class TeamWellnessStatusItem(BaseModel):
    """Wellness submission status for a single athlete."""

    athlete_id: uuid.UUID
    athlete_name: str
    submitted: bool
    latest_entry: WellnessResponse | None = None
