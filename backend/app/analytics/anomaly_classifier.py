"""Anomaly classification and explanation generation."""

from __future__ import annotations

import statistics

from app.analytics.anomaly_types import AnomalySeverity, AnomalyType


def classify_severity(mad_score: float) -> AnomalySeverity:
    """Classify anomaly severity based on modified z-score magnitude.

    - low: 2.5 - 3.0
    - medium: 3.0 - 4.0
    - high: > 4.0
    """
    abs_score = abs(mad_score)
    if abs_score >= 4.0:
        return AnomalySeverity.high
    if abs_score >= 3.0:
        return AnomalySeverity.medium
    return AnomalySeverity.low


def classify_type(current: float, median: float, trend: list[float]) -> AnomalyType:
    """Classify anomaly as spike, drop, or trend_break.

    Args:
        current: The anomalous value.
        median: The expected median from the rolling window.
        trend: Recent values leading up to the anomaly (at least 3 values).
    """
    if len(trend) >= 3:
        # Check for trend break: if trend was moving in one direction
        # but the current value breaks it significantly
        diffs = [trend[i + 1] - trend[i] for i in range(len(trend) - 1)]
        if len(diffs) >= 2:
            avg_diff = statistics.mean(diffs)
            current_diff = current - trend[-1]
            # Trend break: direction reversal with magnitude
            if avg_diff != 0 and (current_diff / avg_diff) < -1.0:
                return AnomalyType.trend_break

    if current > median:
        return AnomalyType.spike
    return AnomalyType.drop


def generate_explanation(
    metric_type: str,
    athlete_name: str,
    value: float,
    expected_median: float,
    mad_score: float,
    severity: AnomalySeverity,
    anomaly_type: AnomalyType,
) -> str:
    """Generate a human-readable explanation for an anomaly.

    Args:
        metric_type: The metric that is anomalous (e.g. "resting_hr").
        athlete_name: The athlete's name.
        value: The anomalous value.
        expected_median: The expected median from baseline.
        mad_score: The modified z-score.
        severity: The severity classification.
        anomaly_type: The type classification.
    """
    direction = "above" if value > expected_median else "below"
    metric_label = metric_type.replace("_", " ")

    return (
        f"{athlete_name}'s {metric_label} of {value:.1f} is a {severity.value}-severity "
        f"{anomaly_type.value} ({direction} expected median of {expected_median:.1f}, "
        f"modified z-score: {mad_score:.2f})"
    )
