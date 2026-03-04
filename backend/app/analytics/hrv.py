"""HRV (Heart Rate Variability) trend analysis using RMSSD rolling statistics."""

from __future__ import annotations

import statistics
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import date


class HRVTrend(StrEnum):
    """HRV trend classification."""

    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"


@dataclass
class DailyHRV:
    """A single day's HRV measurement."""

    date: date
    rmssd_value: float


@dataclass
class HRVStats:
    """Rolling HRV statistics."""

    rolling_mean: float
    rolling_cv: float
    trend: HRVTrend
    baseline_mean: float


def compute_hrv_rolling_stats(
    rmssd_values: list[DailyHRV], window: int = 7
) -> HRVStats:
    """Compute rolling HRV statistics from a list of daily RMSSD values.

    Args:
        rmssd_values: Daily HRV readings sorted by date ascending.
        window: Number of days for the rolling window (default 7).

    Returns:
        HRVStats with rolling mean, rolling CV, trend, and baseline mean.

    The baseline_mean is computed over all provided values.
    The rolling_mean and rolling_cv are computed over the last `window` values.
    """
    if not rmssd_values:
        return HRVStats(
            rolling_mean=0.0,
            rolling_cv=0.0,
            trend=HRVTrend.STABLE,
            baseline_mean=0.0,
        )

    all_values = [d.rmssd_value for d in rmssd_values]
    baseline_mean = statistics.mean(all_values)

    recent = all_values[-window:]
    rolling_mean = statistics.mean(recent)

    rolling_cv = (
        0.0
        if len(recent) < 2 or rolling_mean < 1e-10
        else statistics.pstdev(recent) / rolling_mean
    )

    trend = _detect_trend(all_values, window)

    return HRVStats(
        rolling_mean=rolling_mean,
        rolling_cv=rolling_cv,
        trend=trend,
        baseline_mean=baseline_mean,
    )


def classify_hrv_trend(stats: HRVStats) -> HRVTrend:
    """Classify HRV trend from computed stats.

    This is a convenience wrapper -- the trend is already computed in
    compute_hrv_rolling_stats, but this function allows re-classification
    if needed.
    """
    return stats.trend


def _detect_trend(values: list[float], window: int) -> HRVTrend:
    """Detect HRV trend by comparing recent window to prior window.

    Improving: recent mean > prior mean AND recent CV <= prior CV (or prior unavailable).
    Declining: recent mean < prior mean OR recent CV significantly increasing.
    Stable: otherwise.
    """
    if len(values) < window + 1:
        return HRVTrend.STABLE

    recent = values[-window:]
    prior = values[-(2 * window) : -window] if len(values) >= 2 * window else values[: -window]

    if not prior:
        return HRVTrend.STABLE

    recent_mean = statistics.mean(recent)
    prior_mean = statistics.mean(prior)

    recent_cv = _cv(recent)
    prior_cv = _cv(prior)

    mean_change_pct = (recent_mean - prior_mean) / prior_mean if prior_mean > 1e-10 else 0.0
    cv_change = recent_cv - prior_cv

    # Improving: mean increasing (>2%) and CV not increasing significantly
    if mean_change_pct > 0.02 and cv_change <= 0.05:
        return HRVTrend.IMPROVING

    # Declining: mean decreasing (>2%) or CV increasing significantly (>10%)
    if mean_change_pct < -0.02 or cv_change > 0.10:
        return HRVTrend.DECLINING

    return HRVTrend.STABLE


def _cv(values: list[float]) -> float:
    """Compute coefficient of variation (std/mean)."""
    if len(values) < 2:
        return 0.0
    mean = statistics.mean(values)
    if mean < 1e-10:
        return 0.0
    return statistics.pstdev(values) / mean
