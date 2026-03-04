"""Tests for HRV rolling statistics and trend detection."""

from datetime import date, timedelta

from app.analytics.hrv import (
    DailyHRV,
    HRVStats,
    HRVTrend,
    classify_hrv_trend,
    compute_hrv_rolling_stats,
)


def _make_daily(values: list[float], start: date | None = None) -> list[DailyHRV]:
    """Helper to create a list of DailyHRV from raw values."""
    if start is None:
        start = date(2025, 1, 1)
    return [
        DailyHRV(date=start + timedelta(days=i), rmssd_value=v)
        for i, v in enumerate(values)
    ]


class TestRollingStats:
    """Tests for compute_hrv_rolling_stats."""

    def test_basic_7day_rolling_mean(self) -> None:
        """Rolling mean over 7 days matches expected value."""
        values = [50.0, 52.0, 48.0, 55.0, 53.0, 49.0, 51.0]
        daily = _make_daily(values)
        stats = compute_hrv_rolling_stats(daily, window=7)

        expected_mean = sum(values) / 7
        assert abs(stats.rolling_mean - expected_mean) < 0.01

    def test_rolling_mean_uses_last_window(self) -> None:
        """Rolling mean uses only the last N values in the window."""
        values = [30.0, 32.0, 28.0, 35.0, 33.0, 29.0, 31.0,  # first 7 (older)
                  60.0, 62.0, 58.0, 65.0, 63.0, 59.0, 61.0]  # last 7 (recent)
        daily = _make_daily(values)
        stats = compute_hrv_rolling_stats(daily, window=7)

        expected_mean = sum(values[-7:]) / 7
        assert abs(stats.rolling_mean - expected_mean) < 0.01

    def test_rolling_cv_calculation(self) -> None:
        """Rolling CV = std/mean for the window."""
        values = [50.0, 52.0, 48.0, 55.0, 53.0, 49.0, 51.0]
        daily = _make_daily(values)
        stats = compute_hrv_rolling_stats(daily, window=7)

        import statistics
        mean = statistics.mean(values)
        std = statistics.pstdev(values)
        expected_cv = std / mean

        assert abs(stats.rolling_cv - expected_cv) < 0.001

    def test_baseline_mean_uses_all_values(self) -> None:
        """Baseline mean is computed over all provided values."""
        values = [30.0, 60.0, 45.0]
        daily = _make_daily(values)
        stats = compute_hrv_rolling_stats(daily)

        expected = sum(values) / len(values)
        assert abs(stats.baseline_mean - expected) < 0.01

    def test_zero_cv_for_constant_values(self) -> None:
        """CV is zero when all values are identical."""
        values = [50.0] * 7
        daily = _make_daily(values)
        stats = compute_hrv_rolling_stats(daily, window=7)

        assert stats.rolling_cv == 0.0


class TestEdgeCases:
    """Edge case tests for HRV analysis."""

    def test_empty_input(self) -> None:
        """Empty input returns zeros and stable trend."""
        stats = compute_hrv_rolling_stats([])
        assert stats.rolling_mean == 0.0
        assert stats.rolling_cv == 0.0
        assert stats.trend == HRVTrend.STABLE
        assert stats.baseline_mean == 0.0

    def test_single_value(self) -> None:
        """Single value returns that value as mean, CV=0, stable trend."""
        daily = [DailyHRV(date=date(2025, 1, 1), rmssd_value=55.0)]
        stats = compute_hrv_rolling_stats(daily)

        assert stats.rolling_mean == 55.0
        assert stats.rolling_cv == 0.0
        assert stats.baseline_mean == 55.0
        assert stats.trend == HRVTrend.STABLE

    def test_fewer_than_window_days(self) -> None:
        """Fewer values than window size still computes from available data."""
        values = [50.0, 55.0, 52.0]
        daily = _make_daily(values)
        stats = compute_hrv_rolling_stats(daily, window=7)

        expected_mean = sum(values) / len(values)
        assert abs(stats.rolling_mean - expected_mean) < 0.01

    def test_two_values_has_nonzero_cv(self) -> None:
        """Two different values produce a nonzero CV."""
        daily = _make_daily([40.0, 60.0])
        stats = compute_hrv_rolling_stats(daily, window=7)
        assert stats.rolling_cv > 0


class TestTrendDetection:
    """Tests for HRV trend classification."""

    def test_improving_trend(self) -> None:
        """Mean increasing + CV stable/decreasing -> improving."""
        # Prior window: lower values, some variation
        prior = [40.0, 42.0, 38.0, 41.0, 39.0, 43.0, 40.0]
        # Recent window: higher values, less variation
        recent = [55.0, 56.0, 54.0, 55.0, 56.0, 55.0, 55.0]
        daily = _make_daily(prior + recent)
        stats = compute_hrv_rolling_stats(daily, window=7)

        assert stats.trend == HRVTrend.IMPROVING

    def test_declining_trend_mean_drop(self) -> None:
        """Mean decreasing -> declining."""
        prior = [60.0, 62.0, 58.0, 61.0, 59.0, 63.0, 60.0]
        recent = [45.0, 43.0, 47.0, 44.0, 46.0, 42.0, 45.0]
        daily = _make_daily(prior + recent)
        stats = compute_hrv_rolling_stats(daily, window=7)

        assert stats.trend == HRVTrend.DECLINING

    def test_declining_trend_cv_increase(self) -> None:
        """CV significantly increasing -> declining even if mean is similar."""
        prior = [50.0, 50.0, 50.0, 50.0, 50.0, 50.0, 50.0]
        recent = [30.0, 70.0, 25.0, 75.0, 35.0, 65.0, 50.0]
        daily = _make_daily(prior + recent)
        stats = compute_hrv_rolling_stats(daily, window=7)

        assert stats.trend == HRVTrend.DECLINING

    def test_stable_trend(self) -> None:
        """Similar mean and CV -> stable."""
        prior = [50.0, 52.0, 48.0, 51.0, 49.0, 53.0, 50.0]
        recent = [50.0, 51.0, 49.0, 52.0, 48.0, 51.0, 50.0]
        daily = _make_daily(prior + recent)
        stats = compute_hrv_rolling_stats(daily, window=7)

        assert stats.trend == HRVTrend.STABLE

    def test_insufficient_data_returns_stable(self) -> None:
        """Not enough data for two full windows -> stable."""
        values = [50.0, 52.0, 48.0, 55.0, 53.0, 49.0, 51.0]
        daily = _make_daily(values)
        stats = compute_hrv_rolling_stats(daily, window=7)

        assert stats.trend == HRVTrend.STABLE

    def test_classify_hrv_trend_wrapper(self) -> None:
        """classify_hrv_trend returns the trend from stats."""
        stats = HRVStats(
            rolling_mean=50.0,
            rolling_cv=0.05,
            trend=HRVTrend.IMPROVING,
            baseline_mean=48.0,
        )
        assert classify_hrv_trend(stats) == HRVTrend.IMPROVING
