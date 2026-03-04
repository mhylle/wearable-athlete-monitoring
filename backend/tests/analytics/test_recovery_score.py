"""Tests for composite recovery score computation."""

from datetime import date

from app.analytics.acwr import ACWRResult, ACWRZone
from app.analytics.hrv import HRVStats, HRVTrend
from app.analytics.recovery_score import (
    WellnessInput,
    compute_recovery_score,
)
from app.analytics.sleep import SleepSummary


def _make_hrv_stats(
    rolling_mean: float = 50.0,
    baseline_mean: float = 50.0,
    rolling_cv: float = 0.05,
    trend: HRVTrend = HRVTrend.STABLE,
) -> HRVStats:
    return HRVStats(
        rolling_mean=rolling_mean,
        rolling_cv=rolling_cv,
        trend=trend,
        baseline_mean=baseline_mean,
    )


def _make_sleep_summary(
    total_minutes: float = 480.0,
    efficiency: float = 0.90,
) -> SleepSummary:
    return SleepSummary(
        date=date(2025, 1, 15),
        total_minutes=total_minutes,
        deep_minutes=90.0,
        rem_minutes=120.0,
        light_minutes=240.0,
        awake_minutes=total_minutes * (1 - efficiency),
        efficiency=efficiency,
    )


def _make_acwr(acwr_value: float = 1.0) -> ACWRResult:
    return ACWRResult(
        acute_ewma=100.0,
        chronic_ewma=100.0 / acwr_value if acwr_value else 100.0,
        acwr_value=acwr_value,
        zone=ACWRZone.OPTIMAL,
        date=date(2025, 1, 15),
    )


def _make_wellness(
    mood: int = 4,
    soreness: int = 3,
    fatigue: int = 3,
) -> WellnessInput:
    return WellnessInput(mood=mood, soreness=soreness, fatigue=fatigue)


class TestAllComponentsPresent:
    """Tests with all four components available."""

    def test_perfect_recovery_score(self) -> None:
        """Perfect inputs produce a high recovery score."""
        hrv = _make_hrv_stats(rolling_mean=55.0, baseline_mean=50.0)  # 10% above baseline
        sleep = _make_sleep_summary(total_minutes=480.0, efficiency=1.0)  # 8h, perfect efficiency
        acwr = _make_acwr(acwr_value=1.0)  # perfect ACWR
        wellness = _make_wellness(mood=5, soreness=1, fatigue=1)  # best subjective

        score = compute_recovery_score(hrv, sleep, acwr, wellness)

        assert score.total_score >= 95.0
        assert "hrv" in score.available_components
        assert "sleep" in score.available_components
        assert "load" in score.available_components
        assert "subjective" in score.available_components

    def test_poor_recovery_score(self) -> None:
        """Poor inputs produce a low recovery score."""
        hrv = _make_hrv_stats(rolling_mean=35.0, baseline_mean=50.0)  # 30% below
        sleep = _make_sleep_summary(total_minutes=300.0, efficiency=0.70)  # short, poor efficiency
        acwr = _make_acwr(acwr_value=2.0)  # very high ACWR
        wellness = _make_wellness(mood=1, soreness=10, fatigue=10)  # worst subjective

        score = compute_recovery_score(hrv, sleep, acwr, wellness)

        assert score.total_score < 30.0

    def test_known_inputs_within_tolerance(self) -> None:
        """Known inputs produce a score within 1 point of expected.

        HRV: rolling_mean=50, baseline=50 -> ratio=1.0 -> component=50
        Sleep: 480 min (100% of target), efficiency=0.9 -> (100*0.5 + 90*0.5) = 95
        Load: ACWR=1.0 -> deviation=0 -> component=100
        Subjective: mood=3 (50/100), soreness=5 (60/100), fatigue=5 (60/100) -> avg=56.67

        Weighted: 50*0.4 + 95*0.3 + 100*0.2 + 56.67*0.1 = 20 + 28.5 + 20 + 5.67 = 74.17
        """
        hrv = _make_hrv_stats(rolling_mean=50.0, baseline_mean=50.0)
        sleep = _make_sleep_summary(total_minutes=480.0, efficiency=0.90)
        acwr = _make_acwr(acwr_value=1.0)
        wellness = _make_wellness(mood=3, soreness=5, fatigue=5)

        score = compute_recovery_score(hrv, sleep, acwr, wellness)

        assert abs(score.total_score - 74.2) < 1.0

    def test_score_clamped_0_100(self) -> None:
        """Score stays within 0-100 range."""
        hrv = _make_hrv_stats(rolling_mean=50.0, baseline_mean=50.0)
        sleep = _make_sleep_summary()
        acwr = _make_acwr()
        wellness = _make_wellness()

        score = compute_recovery_score(hrv, sleep, acwr, wellness)
        assert 0.0 <= score.total_score <= 100.0


class TestComponentBreakdown:
    """Tests that individual components are correctly reported."""

    def test_hrv_component_at_baseline(self) -> None:
        """Rolling mean == baseline -> HRV component = 50."""
        hrv = _make_hrv_stats(rolling_mean=50.0, baseline_mean=50.0)
        score = compute_recovery_score(hrv, None, None, None)

        assert score.hrv_component is not None
        assert abs(score.hrv_component - 50.0) < 0.1

    def test_hrv_component_above_baseline(self) -> None:
        """Rolling mean 10% above baseline -> HRV component = 100."""
        hrv = _make_hrv_stats(rolling_mean=55.0, baseline_mean=50.0)
        score = compute_recovery_score(hrv, None, None, None)

        assert score.hrv_component is not None
        assert abs(score.hrv_component - 100.0) < 0.1

    def test_hrv_component_below_baseline(self) -> None:
        """Rolling mean 30% below baseline -> HRV component = 0."""
        hrv = _make_hrv_stats(rolling_mean=35.0, baseline_mean=50.0)
        score = compute_recovery_score(hrv, None, None, None)

        assert score.hrv_component is not None
        assert abs(score.hrv_component - 0.0) < 0.1

    def test_sleep_component_perfect(self) -> None:
        """Full 8h sleep with perfect efficiency -> sleep component near 100."""
        sleep = _make_sleep_summary(total_minutes=480.0, efficiency=1.0)
        score = compute_recovery_score(None, sleep, None, None)

        assert score.sleep_component is not None
        assert abs(score.sleep_component - 100.0) < 0.1

    def test_load_component_optimal_acwr(self) -> None:
        """ACWR = 1.0 -> load component = 100."""
        acwr = _make_acwr(acwr_value=1.0)
        score = compute_recovery_score(None, None, acwr, None)

        assert score.load_component is not None
        assert abs(score.load_component - 100.0) < 0.1

    def test_load_component_high_acwr(self) -> None:
        """ACWR = 1.5 -> deviation = 0.5 -> load component = 50."""
        acwr = _make_acwr(acwr_value=1.5)
        score = compute_recovery_score(None, None, acwr, None)

        assert score.load_component is not None
        assert abs(score.load_component - 50.0) < 0.1


class TestMissingDataReweighting:
    """Tests for graceful handling of missing components."""

    def test_missing_all_returns_none(self) -> None:
        """No data at all -> total_score is None."""
        score = compute_recovery_score(None, None, None, None)

        assert score.total_score is None
        assert score.available_components == []

    def test_missing_hrv_reweights(self) -> None:
        """Missing HRV -> remaining components are re-weighted."""
        sleep = _make_sleep_summary(total_minutes=480.0, efficiency=1.0)
        acwr = _make_acwr(acwr_value=1.0)
        wellness = _make_wellness(mood=5, soreness=1, fatigue=1)

        score = compute_recovery_score(None, sleep, acwr, wellness)

        assert "hrv" not in score.available_components
        assert score.hrv_component is None
        assert len(score.available_components) == 3
        # All remaining at 100 -> score should be ~100
        assert score.total_score >= 95.0

    def test_only_hrv_available(self) -> None:
        """Only HRV available -> score based solely on HRV component."""
        hrv = _make_hrv_stats(rolling_mean=50.0, baseline_mean=50.0)
        score = compute_recovery_score(hrv, None, None, None)

        assert score.available_components == ["hrv"]
        # HRV at baseline -> component = 50 -> total = 50
        assert abs(score.total_score - 50.0) < 0.1

    def test_only_sleep_available(self) -> None:
        """Only sleep available -> score based solely on sleep component."""
        sleep = _make_sleep_summary(total_minutes=480.0, efficiency=0.90)
        score = compute_recovery_score(None, sleep, None, None)

        assert score.available_components == ["sleep"]
        # Duration: 480/480 = 1.0 -> 100*0.5 = 50; Efficiency: 0.9*100*0.5 = 45 -> total=95
        assert abs(score.total_score - 95.0) < 0.1

    def test_zero_baseline_hrv_excluded(self) -> None:
        """HRV with zero baseline mean is treated as missing."""
        hrv = _make_hrv_stats(rolling_mean=50.0, baseline_mean=0.0)
        score = compute_recovery_score(hrv, None, None, None)

        assert "hrv" not in score.available_components

    def test_zero_sleep_excluded(self) -> None:
        """Sleep with zero total minutes is treated as missing."""
        sleep = _make_sleep_summary(total_minutes=0.0)
        score = compute_recovery_score(None, sleep, None, None)

        assert "sleep" not in score.available_components

    def test_null_acwr_value_excluded(self) -> None:
        """ACWR with null value is treated as missing."""
        acwr = ACWRResult(
            acute_ewma=0.0,
            chronic_ewma=0.0,
            acwr_value=None,
            zone=ACWRZone.UNDERTRAINING,
            date=date(2025, 1, 15),
        )
        score = compute_recovery_score(None, None, acwr, None)

        assert "load" not in score.available_components

    def test_no_wellness_fields_excluded(self) -> None:
        """Wellness with all None fields is treated as missing."""
        wellness = WellnessInput(mood=None, soreness=None, fatigue=None)
        score = compute_recovery_score(None, None, None, wellness)

        assert "subjective" not in score.available_components


class TestSubjectiveComponent:
    """Tests for subjective wellness component details."""

    def test_best_subjective_score(self) -> None:
        """Best wellness values -> high subjective score."""
        wellness = _make_wellness(mood=5, soreness=1, fatigue=1)
        score = compute_recovery_score(None, None, None, wellness)

        assert score.subjective_component is not None
        assert score.subjective_component >= 95.0

    def test_worst_subjective_score(self) -> None:
        """Worst wellness values -> low subjective score."""
        wellness = _make_wellness(mood=1, soreness=10, fatigue=10)
        score = compute_recovery_score(None, None, None, wellness)

        assert score.subjective_component is not None
        assert score.subjective_component < 10.0

    def test_partial_wellness_data(self) -> None:
        """Only mood provided -> subjective computed from mood alone."""
        wellness = WellnessInput(mood=5, soreness=None, fatigue=None)
        score = compute_recovery_score(None, None, None, wellness)

        assert "subjective" in score.available_components
        assert score.subjective_component is not None
        # mood=5 -> (5-1)/4 * 100 = 100
        assert abs(score.subjective_component - 100.0) < 0.1
