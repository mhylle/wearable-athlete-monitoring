"""Tests for anomaly classification and explanation generation."""

from app.analytics.anomaly_classifier import (
    classify_severity,
    classify_type,
    generate_explanation,
)
from app.analytics.anomaly_types import AnomalySeverity, AnomalyType


class TestClassifySeverity:
    """Test severity classification based on MAD score."""

    def test_low_severity(self) -> None:
        assert classify_severity(2.5) == AnomalySeverity.low
        assert classify_severity(2.9) == AnomalySeverity.low
        assert classify_severity(-2.5) == AnomalySeverity.low

    def test_medium_severity(self) -> None:
        assert classify_severity(3.0) == AnomalySeverity.medium
        assert classify_severity(3.5) == AnomalySeverity.medium
        assert classify_severity(-3.5) == AnomalySeverity.medium

    def test_high_severity(self) -> None:
        assert classify_severity(4.0) == AnomalySeverity.high
        assert classify_severity(5.0) == AnomalySeverity.high
        assert classify_severity(-4.5) == AnomalySeverity.high

    def test_boundary_30(self) -> None:
        assert classify_severity(3.0) == AnomalySeverity.medium

    def test_boundary_40(self) -> None:
        assert classify_severity(4.0) == AnomalySeverity.high


class TestClassifyType:
    """Test anomaly type classification."""

    def test_spike(self) -> None:
        result = classify_type(current=100.0, median=60.0, trend=[59.0, 60.0, 61.0])
        assert result == AnomalyType.spike

    def test_drop(self) -> None:
        # Flat trend, then a drop -> classified as drop (not trend_break)
        result = classify_type(current=30.0, median=60.0, trend=[60.0, 60.0, 60.0])
        assert result == AnomalyType.drop

    def test_drop_from_rising_trend_is_trend_break(self) -> None:
        """A rising trend that suddenly drops is a trend_break."""
        result = classify_type(current=30.0, median=60.0, trend=[59.0, 60.0, 61.0])
        assert result == AnomalyType.trend_break

    def test_trend_break_rising_to_drop(self) -> None:
        """Trend was rising, then suddenly drops."""
        trend = [50.0, 55.0, 60.0, 65.0, 70.0]
        result = classify_type(current=40.0, median=60.0, trend=trend)
        assert result == AnomalyType.trend_break

    def test_short_trend_falls_back_to_spike_drop(self) -> None:
        """With fewer than 3 trend values, classify as spike or drop."""
        result = classify_type(current=100.0, median=60.0, trend=[60.0])
        assert result == AnomalyType.spike

    def test_empty_trend(self) -> None:
        result = classify_type(current=30.0, median=60.0, trend=[])
        assert result == AnomalyType.drop


class TestGenerateExplanation:
    """Test human-readable explanation generation."""

    def test_explanation_contains_athlete_name(self) -> None:
        explanation = generate_explanation(
            metric_type="resting_hr",
            athlete_name="Alice Smith",
            value=95.0,
            expected_median=60.0,
            mad_score=3.5,
            severity=AnomalySeverity.medium,
            anomaly_type=AnomalyType.spike,
        )
        assert "Alice Smith" in explanation

    def test_explanation_contains_metric(self) -> None:
        explanation = generate_explanation(
            metric_type="resting_hr",
            athlete_name="Alice",
            value=95.0,
            expected_median=60.0,
            mad_score=3.5,
            severity=AnomalySeverity.medium,
            anomaly_type=AnomalyType.spike,
        )
        assert "resting hr" in explanation

    def test_explanation_contains_direction_above(self) -> None:
        explanation = generate_explanation(
            metric_type="resting_hr",
            athlete_name="Alice",
            value=95.0,
            expected_median=60.0,
            mad_score=3.5,
            severity=AnomalySeverity.medium,
            anomaly_type=AnomalyType.spike,
        )
        assert "above" in explanation

    def test_explanation_contains_direction_below(self) -> None:
        explanation = generate_explanation(
            metric_type="hrv_rmssd",
            athlete_name="Bob",
            value=20.0,
            expected_median=55.0,
            mad_score=-4.2,
            severity=AnomalySeverity.high,
            anomaly_type=AnomalyType.drop,
        )
        assert "below" in explanation

    def test_explanation_contains_severity(self) -> None:
        explanation = generate_explanation(
            metric_type="resting_hr",
            athlete_name="Alice",
            value=95.0,
            expected_median=60.0,
            mad_score=3.5,
            severity=AnomalySeverity.medium,
            anomaly_type=AnomalyType.spike,
        )
        assert "medium" in explanation

    def test_explanation_contains_anomaly_type(self) -> None:
        explanation = generate_explanation(
            metric_type="resting_hr",
            athlete_name="Alice",
            value=95.0,
            expected_median=60.0,
            mad_score=3.5,
            severity=AnomalySeverity.medium,
            anomaly_type=AnomalyType.spike,
        )
        assert "spike" in explanation

    def test_explanation_contains_values(self) -> None:
        explanation = generate_explanation(
            metric_type="resting_hr",
            athlete_name="Alice",
            value=95.0,
            expected_median=60.0,
            mad_score=3.5,
            severity=AnomalySeverity.medium,
            anomaly_type=AnomalyType.spike,
        )
        assert "95.0" in explanation
        assert "60.0" in explanation
        assert "3.50" in explanation
