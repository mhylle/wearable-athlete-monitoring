"""Data classes and enums for anomaly detection."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import date


class AnomalySeverity(StrEnum):
    """Severity level of a detected anomaly."""

    low = "low"
    medium = "medium"
    high = "high"


class AnomalyType(StrEnum):
    """Classification of anomaly pattern."""

    spike = "spike"
    drop = "drop"
    trend_break = "trend_break"


@dataclass(frozen=True)
class DatedValue:
    """A value associated with a date."""

    date: date
    value: float


@dataclass
class Anomaly:
    """A detected anomaly for a single metric reading."""

    athlete_id: str
    metric_type: str
    value: float
    expected_median: float
    mad_score: float
    severity: AnomalySeverity
    anomaly_type: AnomalyType
    explanation: str
    detected_at: date
