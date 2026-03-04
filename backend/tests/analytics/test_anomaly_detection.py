"""Tests for anomaly detection using modified z-score."""

from datetime import date, timedelta

from app.analytics.anomaly_detection import (
    MIN_BASELINE_DAYS,
    _compute_mad,
    _modified_z_score,
    detect_athlete_anomaly_vs_team,
    detect_metric_anomalies,
)
from app.analytics.anomaly_types import AnomalySeverity, AnomalyType, DatedValue


class TestModifiedZScore:
    """Test the modified z-score calculation."""

    def test_zero_mad_returns_zero(self) -> None:
        assert _modified_z_score(10.0, 5.0, 0.0) == 0.0

    def test_positive_deviation(self) -> None:
        score = _modified_z_score(10.0, 5.0, 2.0)
        expected = 0.6745 * (10.0 - 5.0) / 2.0
        assert abs(score - expected) < 1e-6

    def test_negative_deviation(self) -> None:
        score = _modified_z_score(2.0, 5.0, 2.0)
        expected = 0.6745 * (2.0 - 5.0) / 2.0
        assert score < 0
        assert abs(score - expected) < 1e-6


class TestComputeMAD:
    """Test Median Absolute Deviation computation."""

    def test_constant_values(self) -> None:
        assert _compute_mad([5.0, 5.0, 5.0]) == 0.0

    def test_symmetric_values(self) -> None:
        mad = _compute_mad([1.0, 2.0, 3.0, 4.0, 5.0])
        # Median = 3, deviations = [2, 1, 0, 1, 2], MAD = 1
        assert abs(mad - 1.0) < 1e-6

    def test_single_value(self) -> None:
        assert _compute_mad([42.0]) == 0.0


class TestDetectMetricAnomalies:
    """Test per-metric anomaly detection."""

    def _make_stable_values(
        self, n: int, base: float = 60.0, start_date: date | None = None
    ) -> list[DatedValue]:
        """Generate stable metric values with minor noise."""
        if start_date is None:
            start_date = date(2026, 1, 1)
        return [
            DatedValue(date=start_date + timedelta(days=i), value=base + (i % 3) * 0.5)
            for i in range(n)
        ]

    def test_no_anomalies_in_clean_data(self) -> None:
        values = self._make_stable_values(30)
        anomalies = detect_metric_anomalies(
            values, athlete_id="a1", metric_type="resting_hr"
        )
        assert len(anomalies) == 0

    def test_planted_anomaly_at_day_15_detected(self) -> None:
        """Plant a large spike at day 15 and verify it's detected."""
        values = self._make_stable_values(30)
        # Replace day 15 with a huge spike
        spike_value = 120.0  # Normal is ~60, this is a massive spike
        values[15] = DatedValue(date=values[15].date, value=spike_value)

        anomalies = detect_metric_anomalies(
            values, athlete_id="a1", metric_type="resting_hr", athlete_name="Test"
        )

        assert len(anomalies) >= 1
        spike_anomalies = [a for a in anomalies if a.value == spike_value]
        assert len(spike_anomalies) == 1
        assert spike_anomalies[0].anomaly_type == AnomalyType.spike

    def test_planted_drop_detected(self) -> None:
        """Plant a large drop and verify it's detected."""
        values = self._make_stable_values(30, base=60.0)
        drop_value = 20.0  # Way below normal
        values[20] = DatedValue(date=values[20].date, value=drop_value)

        anomalies = detect_metric_anomalies(
            values, athlete_id="a1", metric_type="resting_hr", athlete_name="Test"
        )

        assert len(anomalies) >= 1
        drop_anomalies = [a for a in anomalies if a.value == drop_value]
        assert len(drop_anomalies) == 1
        # Value is well below median; may be classified as drop or trend_break
        assert drop_anomalies[0].anomaly_type in (AnomalyType.drop, AnomalyType.trend_break)

    def test_multiple_anomalies_all_detected(self) -> None:
        """Multiple anomalous values should all be detected."""
        values = self._make_stable_values(40)
        values[16] = DatedValue(date=values[16].date, value=120.0)
        values[25] = DatedValue(date=values[25].date, value=10.0)

        anomalies = detect_metric_anomalies(
            values, athlete_id="a1", metric_type="resting_hr"
        )

        anomaly_values = {a.value for a in anomalies}
        assert 120.0 in anomaly_values
        assert 10.0 in anomaly_values

    def test_insufficient_history_returns_empty(self) -> None:
        """Fewer than MIN_BASELINE_DAYS should return no anomalies."""
        values = self._make_stable_values(MIN_BASELINE_DAYS - 1)
        anomalies = detect_metric_anomalies(
            values, athlete_id="a1", metric_type="resting_hr"
        )
        assert len(anomalies) == 0

    def test_exactly_min_baseline_no_false_positives(self) -> None:
        """With exactly MIN_BASELINE_DAYS of stable data, no anomalies flagged."""
        values = self._make_stable_values(MIN_BASELINE_DAYS + 1)
        anomalies = detect_metric_anomalies(
            values, athlete_id="a1", metric_type="resting_hr"
        )
        assert len(anomalies) == 0

    def test_anomaly_has_correct_fields(self) -> None:
        """Verify anomaly dataclass is fully populated."""
        values = self._make_stable_values(30, base=60.0)
        values[18] = DatedValue(date=values[18].date, value=150.0)

        anomalies = detect_metric_anomalies(
            values,
            athlete_id="athlete-123",
            metric_type="resting_hr",
            athlete_name="John Doe",
        )

        assert len(anomalies) >= 1
        a = [x for x in anomalies if x.value == 150.0][0]
        assert a.athlete_id == "athlete-123"
        assert a.metric_type == "resting_hr"
        assert a.value == 150.0
        assert a.expected_median > 0
        assert abs(a.mad_score) >= 2.5
        assert a.severity in list(AnomalySeverity)
        assert a.anomaly_type in list(AnomalyType)
        assert "John Doe" in a.explanation
        assert a.detected_at == values[18].date

    def test_custom_threshold(self) -> None:
        """A higher threshold should detect fewer anomalies."""
        values = self._make_stable_values(30, base=60.0)
        values[18] = DatedValue(date=values[18].date, value=80.0)  # Moderate spike

        low_threshold = detect_metric_anomalies(
            values, athlete_id="a1", metric_type="hr", threshold_mad=1.5
        )
        high_threshold = detect_metric_anomalies(
            values, athlete_id="a1", metric_type="hr", threshold_mad=5.0
        )

        assert len(low_threshold) >= len(high_threshold)


class TestDetectAthleteAnomalyVsTeam:
    """Test per-athlete anomaly detection vs team distribution."""

    def test_normal_value_returns_none(self) -> None:
        team_values = [60.0, 62.0, 58.0, 61.0, 59.0]
        result = detect_athlete_anomaly_vs_team(
            athlete_id="a1",
            athlete_name="Test",
            metric_type="resting_hr",
            athlete_value=61.0,
            team_values=team_values,
        )
        assert result is None

    def test_outlier_detected(self) -> None:
        team_values = [60.0, 62.0, 58.0, 61.0, 59.0, 60.5]
        result = detect_athlete_anomaly_vs_team(
            athlete_id="a1",
            athlete_name="Test Athlete",
            metric_type="resting_hr",
            athlete_value=95.0,  # Way above team
            team_values=team_values,
        )
        assert result is not None
        assert result.anomaly_type == AnomalyType.spike
        assert result.athlete_id == "a1"

    def test_low_outlier_detected(self) -> None:
        team_values = [60.0, 62.0, 58.0, 61.0, 59.0, 60.5]
        result = detect_athlete_anomaly_vs_team(
            athlete_id="a1",
            athlete_name="Test",
            metric_type="resting_hr",
            athlete_value=30.0,  # Way below team
            team_values=team_values,
        )
        assert result is not None
        assert result.anomaly_type == AnomalyType.drop

    def test_too_few_team_values_returns_none(self) -> None:
        result = detect_athlete_anomaly_vs_team(
            athlete_id="a1",
            athlete_name="Test",
            metric_type="resting_hr",
            athlete_value=100.0,
            team_values=[60.0, 62.0],  # < 3 values
        )
        assert result is None

    def test_detection_date_used(self) -> None:
        team_values = [60.0, 62.0, 58.0, 61.0, 59.0, 60.5]
        detection = DatedValue(date=date(2026, 3, 15), value=0)
        result = detect_athlete_anomaly_vs_team(
            athlete_id="a1",
            athlete_name="Test",
            metric_type="resting_hr",
            athlete_value=95.0,
            team_values=team_values,
            detection_date=detection,
        )
        assert result is not None
        assert result.detected_at == date(2026, 3, 15)
