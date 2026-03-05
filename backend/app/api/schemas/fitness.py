"""Pydantic schemas for fitness score and trend endpoints."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel


class TrendResultResponse(BaseModel):
    """Trend detection result for a single metric."""

    metric_type: str
    direction: str  # "improving" | "stable" | "declining"
    z_score: float
    is_anomaly: bool
    window_days: int


class FitnessScoreResponse(BaseModel):
    """Composite fitness score response."""

    total: float | None
    components: dict[str, float]
    available_components: list[str]
    computed_at: datetime


class AthleteFitnessResponse(BaseModel):
    """Full fitness response for a single athlete."""

    athlete_id: uuid.UUID
    fitness_score: FitnessScoreResponse
    trends: list[TrendResultResponse]
    date: date


class AthleteTrendsResponse(BaseModel):
    """Trends-only response for a single athlete."""

    athlete_id: uuid.UUID
    trends: list[TrendResultResponse]
    date: date


class TeamAthleteFitnessResponse(BaseModel):
    """Fitness data for one athlete in a team summary."""

    athlete_id: uuid.UUID
    full_name: str
    fitness_score: FitnessScoreResponse
    trends: list[TrendResultResponse]


class TeamFitnessResponse(BaseModel):
    """Team-wide fitness summary."""

    athletes: list[TeamAthleteFitnessResponse]
    date: date
