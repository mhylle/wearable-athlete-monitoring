"""Tests for EWMA calculations."""

import pytest

from app.analytics.ewma import compute_ewma, compute_ewma_single


class TestComputeEwmaSingle:
    """Tests for compute_ewma_single."""

    def test_basic_calculation(self) -> None:
        # gamma = 2 / (7+1) = 0.25
        # EWMA = 100 * 0.25 + 80 * 0.75 = 25 + 60 = 85
        result = compute_ewma_single(100.0, 80.0, 7)
        assert result == pytest.approx(85.0)

    def test_chronic_decay(self) -> None:
        # gamma = 2 / (28+1) = 2/29 ~ 0.06897
        # EWMA = 100 * 0.06897 + 50 * 0.93103 ~ 6.897 + 46.552 = 53.448
        gamma = 2.0 / 29
        expected = 100 * gamma + 50 * (1 - gamma)
        result = compute_ewma_single(100.0, 50.0, 28)
        assert result == pytest.approx(expected)

    def test_zero_load_today(self) -> None:
        # gamma = 0.25; EWMA = 0 * 0.25 + 80 * 0.75 = 60
        result = compute_ewma_single(0.0, 80.0, 7)
        assert result == pytest.approx(60.0)

    def test_zero_ewma_yesterday(self) -> None:
        # gamma = 0.25; EWMA = 100 * 0.25 + 0 * 0.75 = 25
        result = compute_ewma_single(100.0, 0.0, 7)
        assert result == pytest.approx(25.0)


class TestComputeEwma:
    """Tests for compute_ewma series."""

    def test_empty_list(self) -> None:
        assert compute_ewma([], 7) == []

    def test_single_value(self) -> None:
        result = compute_ewma([100.0], 7)
        assert len(result) == 1
        assert result[0] == pytest.approx(100.0)

    def test_first_day_is_seed(self) -> None:
        """First EWMA value should equal the first load."""
        loads = [200.0, 100.0, 150.0]
        result = compute_ewma(loads, 7)
        assert result[0] == pytest.approx(200.0)

    def test_known_series(self) -> None:
        """Hand-calculated 3-day EWMA with decay=7."""
        # gamma = 2/8 = 0.25
        # Day 0: EWMA = 100
        # Day 1: EWMA = 200 * 0.25 + 100 * 0.75 = 50 + 75 = 125
        # Day 2: EWMA = 50 * 0.25 + 125 * 0.75 = 12.5 + 93.75 = 106.25
        loads = [100.0, 200.0, 50.0]
        result = compute_ewma(loads, 7)
        assert result[0] == pytest.approx(100.0)
        assert result[1] == pytest.approx(125.0)
        assert result[2] == pytest.approx(106.25)

    def test_constant_load_converges(self) -> None:
        """A constant load should cause EWMA to converge to that load."""
        loads = [50.0] * 30
        result = compute_ewma(loads, 7)
        assert result[-1] == pytest.approx(50.0, abs=0.1)

    def test_missing_days_as_zeros(self) -> None:
        """Zero loads should pull EWMA down."""
        loads = [100.0, 0.0, 0.0, 0.0]
        result = compute_ewma(loads, 7)
        # Each zero-load day should decrease the EWMA
        assert result[1] < result[0]
        assert result[2] < result[1]
        assert result[3] < result[2]

    def test_output_length_matches_input(self) -> None:
        loads = [10.0, 20.0, 30.0, 40.0, 50.0]
        result = compute_ewma(loads, 7)
        assert len(result) == len(loads)
