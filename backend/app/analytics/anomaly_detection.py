"""Pure anomaly detection functions using modified z-score."""

from __future__ import annotations

import statistics

from app.analytics.anomaly_classifier import (
    classify_severity,
    classify_type,
    generate_explanation,
)
from app.analytics.anomaly_types import (
    Anomaly,
    AnomalyType,
    DatedValue,
)

# Minimum days of history required to establish a baseline
MIN_BASELINE_DAYS = 14

# Consistency factor for normal distribution (0.6745 = Q3 of std normal)
_CONSISTENCY_FACTOR = 0.6745


def _modified_z_score(value: float, median: float, mad: float) -> float:
    """Compute the modified z-score for a value.

    Formula: 0.6745 * (x - median) / MAD
    """
    if mad < 1e-10:
        return 0.0
    return _CONSISTENCY_FACTOR * (value - median) / mad


def _compute_mad(values: list[float]) -> float:
    """Compute the Median Absolute Deviation."""
    med = statistics.median(values)
    return statistics.median([abs(v - med) for v in values])


def detect_metric_anomalies(
    values: list[DatedValue],
    *,
    athlete_id: str = "",
    metric_type: str = "",
    athlete_name: str = "",
    window_days: int = 30,
    threshold_mad: float = 2.5,
) -> list[Anomaly]:
    """Detect per-metric anomalies using modified z-score on a rolling window.

    Args:
        values: Time-ordered list of dated metric values.
        athlete_id: Athlete identifier for the anomaly record.
        metric_type: Metric name (e.g. "resting_hr").
        athlete_name: Athlete name for explanation generation.
        window_days: Size of the rolling baseline window in days.
        threshold_mad: Modified z-score threshold for flagging anomalies.

    Returns:
        List of detected anomalies.
    """
    if len(values) < MIN_BASELINE_DAYS:
        return []

    # Sort by date
    sorted_values = sorted(values, key=lambda dv: dv.date)
    anomalies: list[Anomaly] = []

    for i in range(MIN_BASELINE_DAYS, len(sorted_values)):
        # Build rolling window from preceding values
        window_start = max(0, i - window_days)
        window = [sv.value for sv in sorted_values[window_start:i]]

        if len(window) < MIN_BASELINE_DAYS:
            continue

        current = sorted_values[i]
        median = statistics.median(window)
        mad = _compute_mad(window)
        score = _modified_z_score(current.value, median, mad)

        if abs(score) >= threshold_mad:
            severity = classify_severity(score)
            # Get recent trend (last 5 values in window)
            trend = window[-5:] if len(window) >= 5 else window
            anomaly_type = classify_type(current.value, median, trend)
            explanation = generate_explanation(
                metric_type=metric_type,
                athlete_name=athlete_name,
                value=current.value,
                expected_median=median,
                mad_score=score,
                severity=severity,
                anomaly_type=anomaly_type,
            )
            anomalies.append(
                Anomaly(
                    athlete_id=athlete_id,
                    metric_type=metric_type,
                    value=current.value,
                    expected_median=median,
                    mad_score=score,
                    severity=severity,
                    anomaly_type=anomaly_type,
                    explanation=explanation,
                    detected_at=current.date,
                )
            )

    return anomalies


def detect_athlete_anomaly_vs_team(
    athlete_id: str,
    athlete_name: str,
    metric_type: str,
    athlete_value: float,
    team_values: list[float],
    *,
    threshold_mad: float = 2.5,
    detection_date: DatedValue | None = None,
) -> Anomaly | None:
    """Detect if an athlete's value is anomalous compared to the team distribution.

    Args:
        athlete_id: Athlete identifier.
        athlete_name: Athlete name for explanation.
        metric_type: Metric name.
        athlete_value: The athlete's current value.
        team_values: List of the same metric's values from all team members.
        threshold_mad: Modified z-score threshold.
        detection_date: Optional dated value for the detection date.

    Returns:
        An Anomaly if detected, otherwise None.
    """
    if len(team_values) < 3:
        return None

    median = statistics.median(team_values)
    mad = _compute_mad(team_values)
    score = _modified_z_score(athlete_value, median, mad)

    if abs(score) < threshold_mad:
        return None

    from datetime import date as date_type

    severity = classify_severity(score)
    anomaly_type = AnomalyType.spike if athlete_value > median else AnomalyType.drop
    detected_at = detection_date.date if detection_date else date_type.today()

    explanation = generate_explanation(
        metric_type=metric_type,
        athlete_name=athlete_name,
        value=athlete_value,
        expected_median=median,
        mad_score=score,
        severity=severity,
        anomaly_type=anomaly_type,
    )

    return Anomaly(
        athlete_id=athlete_id,
        metric_type=metric_type,
        value=athlete_value,
        expected_median=median,
        mad_score=score,
        severity=severity,
        anomaly_type=anomaly_type,
        explanation=explanation,
        detected_at=detected_at,
    )
