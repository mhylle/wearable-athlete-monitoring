"""Per-metric trend detection using rolling z-scores and EWMA anomaly detection."""

from __future__ import annotations

from dataclasses import dataclass
from math import exp
from statistics import mean, stdev
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.repositories.metric_agg_repo import DailyMetric

# Metrics where lower values are better
_INVERSE_METRICS = {"resting_heart_rate", "resting_hr"}


@dataclass
class TrendResult:
    """Trend classification result for a single metric."""

    metric_type: str
    direction: str  # "improving" | "stable" | "declining"
    z_score: float
    is_anomaly: bool
    window_days: int


def detect_trend(
    metric_type: str,
    data: list[DailyMetric],
    short_window: int = 7,
    long_window: int = 28,
    threshold: float = 0.5,
) -> TrendResult | None:
    """Classify a metric's trend as improving/stable/declining.

    Uses rolling z-score: z = (mean_7d - mean_28d) / std_28d
    - z > threshold  -> "improving" (or "declining" for inverse metrics)
    - z < -threshold -> "declining" (or "improving" for inverse metrics)
    - else -> "stable"

    Also flags anomalies using EWMA ± 2*std.

    Returns None if insufficient data.
    """
    if len(data) < short_window:
        return None

    values = [d.avg_value for d in data]

    # Short-window (recent) stats
    recent = values[-short_window:]
    recent_mean = mean(recent)

    # Long-window (baseline) stats
    baseline = values[-long_window:] if len(values) >= long_window else values
    baseline_mean = mean(baseline)
    baseline_std = stdev(baseline) if len(baseline) >= 2 else 0.0

    # Z-score
    if baseline_std > 0:
        z = (recent_mean - baseline_mean) / baseline_std
    else:
        z = 0.0

    # Direction classification
    is_inverse = metric_type in _INVERSE_METRICS
    if z > threshold:
        direction = "declining" if is_inverse else "improving"
    elif z < -threshold:
        direction = "improving" if is_inverse else "declining"
    else:
        direction = "stable"

    # EWMA anomaly detection on the most recent value
    is_anomaly = _check_ewma_anomaly(values)

    return TrendResult(
        metric_type=metric_type,
        direction=direction,
        z_score=round(z, 3),
        is_anomaly=is_anomaly,
        window_days=len(baseline),
    )


def _check_ewma_anomaly(
    values: list[float],
    span: int = 7,
    threshold_multiplier: float = 2.0,
) -> bool:
    """Check if the latest value is an anomaly vs EWMA ± threshold*std.

    Uses exponential weighted moving average with the given span.
    """
    if len(values) < 3:
        return False

    alpha = 2.0 / (span + 1)
    ewma = values[0]
    ewma_values = [ewma]

    for v in values[1:]:
        ewma = alpha * v + (1 - alpha) * ewma
        ewma_values.append(ewma)

    # Compute residuals
    residuals = [v - e for v, e in zip(values, ewma_values)]
    if len(residuals) < 2:
        return False

    residual_std = stdev(residuals)
    if residual_std == 0:
        return False

    latest_residual = abs(values[-1] - ewma_values[-1])
    return latest_residual > threshold_multiplier * residual_std


def compute_trend_bonus(trends: list[TrendResult]) -> float:
    """Compute a trend bonus score (0-100) from trend results.

    Improving trends add points, declining trends subtract.
    """
    if not trends:
        return 50.0

    score = 50.0
    per_trend = 50.0 / max(len(trends), 1)

    for trend in trends:
        if trend.direction == "improving":
            score += per_trend
        elif trend.direction == "declining":
            score -= per_trend

    return max(0.0, min(100.0, score))
