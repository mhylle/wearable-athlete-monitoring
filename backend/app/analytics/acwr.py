"""Acute:Chronic Workload Ratio (ACWR) calculations using EWMA method."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

from app.analytics.ewma import compute_ewma

if TYPE_CHECKING:
    from datetime import date


class ACWRZone(StrEnum):
    """ACWR risk classification zones."""

    UNDERTRAINING = "undertraining"
    OPTIMAL = "optimal"
    CAUTION = "caution"
    HIGH_RISK = "high_risk"


@dataclass
class ACWRResult:
    """Result of an ACWR computation."""

    acute_ewma: float
    chronic_ewma: float
    acwr_value: float | None
    zone: ACWRZone
    date: date


def classify_acwr_zone(acwr_value: float) -> ACWRZone:
    """Classify an ACWR value into a risk zone.

    Zones:
        < 0.8  -> undertraining
        0.8-1.3 -> optimal
        1.3-1.5 -> caution
        > 1.5  -> high_risk
    """
    if acwr_value < 0.8:
        return ACWRZone.UNDERTRAINING
    if acwr_value <= 1.3:
        return ACWRZone.OPTIMAL
    if acwr_value <= 1.5:
        return ACWRZone.CAUTION
    return ACWRZone.HIGH_RISK


def compute_acwr(
    daily_loads: list[float],
    as_of_date: date,
    acute_days: int = 7,
    chronic_days: int = 28,
) -> ACWRResult:
    """Compute ACWR from a list of daily load values.

    The daily_loads list should contain at least chronic_days entries for a
    meaningful result. The last entry corresponds to as_of_date.

    Returns an ACWRResult with acwr_value=None if chronic EWMA is near zero.
    """
    if not daily_loads:
        return ACWRResult(
            acute_ewma=0.0,
            chronic_ewma=0.0,
            acwr_value=None,
            zone=ACWRZone.UNDERTRAINING,
            date=as_of_date,
        )

    acute_ewma_series = compute_ewma(daily_loads, acute_days)
    chronic_ewma_series = compute_ewma(daily_loads, chronic_days)

    acute_ewma = acute_ewma_series[-1]
    chronic_ewma = chronic_ewma_series[-1]

    if chronic_ewma < 1e-6:
        return ACWRResult(
            acute_ewma=acute_ewma,
            chronic_ewma=chronic_ewma,
            acwr_value=None,
            zone=ACWRZone.UNDERTRAINING,
            date=as_of_date,
        )

    acwr_value = acute_ewma / chronic_ewma
    zone = classify_acwr_zone(acwr_value)

    return ACWRResult(
        acute_ewma=acute_ewma,
        chronic_ewma=chronic_ewma,
        acwr_value=acwr_value,
        zone=zone,
        date=as_of_date,
    )
