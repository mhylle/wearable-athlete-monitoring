"""Metrics response schemas."""

import uuid
from datetime import date

from pydantic import BaseModel


class DailyMetricDataPoint(BaseModel):
    """A single day's aggregated metric values."""

    date: date
    avg: float
    min: float
    max: float
    count: int


class DailyMetricsResponse(BaseModel):
    """Daily-aggregated metrics for an athlete."""

    metric_type: str
    start: date
    end: date
    data: list[DailyMetricDataPoint]


class AvailableMetricsResponse(BaseModel):
    """Available metric types for an athlete."""

    athlete_id: uuid.UUID
    metric_types: list[str]
