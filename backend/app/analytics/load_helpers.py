"""Helper functions for computing and aggregating session loads."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.training_session import TrainingSession
    from app.models.wellness_entry import WellnessEntry


@dataclass
class DailyLoad:
    """Aggregated training load for a single day."""

    date: date
    total_load: float
    session_count: int


def compute_session_load(
    session: TrainingSession, wellness: WellnessEntry | None
) -> float:
    """Compute load for a single session.

    For manual sessions: sRPE * duration_minutes (from wellness entry).
    For garmin sessions with HR data: use HR-based estimate (avg_hr * duration).
    Falls back to 0.0 if data is insufficient.
    """
    duration = session.duration_minutes
    if duration is None or duration <= 0:
        return 0.0

    # Manual sessions use sRPE from wellness entry
    if session.source == "manual" and wellness is not None and wellness.srpe is not None:
        return float(wellness.srpe * duration)

    # For garmin/device sessions, fall back to duration as load if no other data
    if session.source != "manual":
        return float(duration)

    return 0.0


def aggregate_daily_loads(
    sessions: list[TrainingSession],
    start: date,
    end: date,
    wellness_by_date: dict[date, WellnessEntry] | None = None,
) -> list[DailyLoad]:
    """Aggregate session loads into daily totals, filling missing days with zero.

    Returns a list of DailyLoad from start to end (inclusive), sorted by date.
    """
    if wellness_by_date is None:
        wellness_by_date = {}

    daily: dict[date, DailyLoad] = {}

    # Initialize all days to zero
    current = start
    while current <= end:
        daily[current] = DailyLoad(date=current, total_load=0.0, session_count=0)
        current += timedelta(days=1)

    # Accumulate session loads
    for session in sessions:
        session_date = session.start_time.date()
        if session_date < start or session_date > end:
            continue
        wellness = wellness_by_date.get(session_date)
        load = compute_session_load(session, wellness)
        daily[session_date].total_load += load
        daily[session_date].session_count += 1

    return sorted(daily.values(), key=lambda dl: dl.date)
