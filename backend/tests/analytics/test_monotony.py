"""Tests for monotony and strain calculations."""

import math
import statistics

import pytest

from app.analytics.monotony import compute_monotony, compute_strain


class TestComputeMonotony:
    """Tests for training monotony calculation."""

    def test_known_7_day_loads(self) -> None:
        """Known 7-day dataset."""
        loads = [100.0, 120.0, 80.0, 150.0, 90.0, 110.0, 130.0]
        mean = statistics.mean(loads)
        stdev = statistics.pstdev(loads)
        expected = mean / stdev
        result = compute_monotony(loads)
        assert result == pytest.approx(expected, abs=0.01)

    def test_all_same_loads_returns_inf(self) -> None:
        """std=0 when all loads identical -> monotony = inf."""
        loads = [100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0]
        result = compute_monotony(loads)
        assert math.isinf(result)

    def test_single_day_returns_inf(self) -> None:
        """Single day of data -> inf (cannot compute std)."""
        result = compute_monotony([100.0])
        assert math.isinf(result)

    def test_uses_last_window_days(self) -> None:
        """Only the last window_days entries should be used."""
        loads = [500.0, 500.0, 500.0, 100.0, 120.0, 80.0, 150.0, 90.0, 110.0, 130.0]
        # Should use last 7: [100, 120, 80, 150, 90, 110, 130]
        window = loads[-7:]
        expected = statistics.mean(window) / statistics.pstdev(window)
        result = compute_monotony(loads, window_days=7)
        assert result == pytest.approx(expected, abs=0.01)

    def test_high_variability_low_monotony(self) -> None:
        """High variability should produce lower monotony."""
        high_var = [10.0, 200.0, 10.0, 200.0, 10.0, 200.0, 10.0]
        low_var = [100.0, 105.0, 100.0, 105.0, 100.0, 105.0, 100.0]
        assert compute_monotony(high_var) < compute_monotony(low_var)


class TestComputeStrain:
    """Tests for training strain calculation."""

    def test_known_values(self) -> None:
        """Strain = weekly_load * monotony."""
        result = compute_strain(700.0, 5.0)
        assert result == pytest.approx(3500.0)

    def test_zero_monotony(self) -> None:
        result = compute_strain(700.0, 0.0)
        assert result == pytest.approx(0.0)

    def test_zero_load(self) -> None:
        result = compute_strain(0.0, 5.0)
        assert result == pytest.approx(0.0)

    def test_known_7_day_strain(self) -> None:
        """Compute strain from a known 7-day load set."""
        loads = [100.0, 120.0, 80.0, 150.0, 90.0, 110.0, 130.0]
        weekly_total = sum(loads)
        monotony = compute_monotony(loads)
        expected = weekly_total * monotony
        result = compute_strain(weekly_total, monotony)
        assert result == pytest.approx(expected, abs=0.01)
