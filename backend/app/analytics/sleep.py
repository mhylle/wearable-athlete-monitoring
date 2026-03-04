"""Sleep quality analysis computations."""

from __future__ import annotations

import statistics
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import date


@dataclass
class SleepRecord:
    """A single sleep metric record from the data store."""

    metric_type: str
    value: float
    date: date


@dataclass
class SleepSummary:
    """Summary of one night's sleep."""

    date: date
    total_minutes: float
    deep_minutes: float
    rem_minutes: float
    light_minutes: float
    awake_minutes: float
    efficiency: float


@dataclass
class SleepAverage:
    """Averaged sleep statistics over a period."""

    days: int
    avg_total_minutes: float
    avg_deep_minutes: float
    avg_rem_minutes: float
    avg_light_minutes: float
    avg_awake_minutes: float
    avg_efficiency: float


def compute_sleep_summary(sleep_records: list[SleepRecord], target_date: date) -> SleepSummary:
    """Compute a sleep summary from individual sleep metric records for a given date.

    Expected metric_type values:
        - "sleep_total": total sleep time in minutes
        - "sleep_deep": deep sleep in minutes
        - "sleep_rem": REM sleep in minutes
        - "sleep_light": light sleep in minutes
        - "sleep_awake": awake time in minutes

    Efficiency = (total - awake) / total if total > 0, else 0.
    """
    total = 0.0
    deep = 0.0
    rem = 0.0
    light = 0.0
    awake = 0.0

    for rec in sleep_records:
        if rec.date != target_date:
            continue
        if rec.metric_type == "sleep_total":
            total = rec.value
        elif rec.metric_type == "sleep_deep":
            deep = rec.value
        elif rec.metric_type == "sleep_rem":
            rem = rec.value
        elif rec.metric_type == "sleep_light":
            light = rec.value
        elif rec.metric_type == "sleep_awake":
            awake = rec.value

    # If total is not explicitly provided, derive from stage breakdowns
    if total == 0.0 and (deep + rem + light + awake) > 0:
        total = deep + rem + light + awake

    efficiency = (total - awake) / total if total > 0 else 0.0
    efficiency = max(0.0, min(1.0, efficiency))

    return SleepSummary(
        date=target_date,
        total_minutes=total,
        deep_minutes=deep,
        rem_minutes=rem,
        light_minutes=light,
        awake_minutes=awake,
        efficiency=efficiency,
    )


def compute_sleep_average(summaries: list[SleepSummary], days: int = 7) -> SleepAverage:
    """Compute average sleep statistics over the most recent `days` summaries.

    Args:
        summaries: Sleep summaries sorted by date ascending.
        days: Number of recent days to average over.

    Returns:
        SleepAverage with averaged values.
    """
    recent = summaries[-days:] if summaries else []

    if not recent:
        return SleepAverage(
            days=0,
            avg_total_minutes=0.0,
            avg_deep_minutes=0.0,
            avg_rem_minutes=0.0,
            avg_light_minutes=0.0,
            avg_awake_minutes=0.0,
            avg_efficiency=0.0,
        )

    return SleepAverage(
        days=len(recent),
        avg_total_minutes=statistics.mean([s.total_minutes for s in recent]),
        avg_deep_minutes=statistics.mean([s.deep_minutes for s in recent]),
        avg_rem_minutes=statistics.mean([s.rem_minutes for s in recent]),
        avg_light_minutes=statistics.mean([s.light_minutes for s in recent]),
        avg_awake_minutes=statistics.mean([s.awake_minutes for s in recent]),
        avg_efficiency=statistics.mean([s.efficiency for s in recent]),
    )
