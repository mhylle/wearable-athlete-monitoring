"""Tests for ACWR calculations."""

from datetime import date

import pytest

from app.analytics.acwr import ACWRZone, classify_acwr_zone, compute_acwr


class TestClassifyACWRZone:
    """Tests for ACWR zone classification."""

    def test_undertraining(self) -> None:
        assert classify_acwr_zone(0.5) == ACWRZone.UNDERTRAINING
        assert classify_acwr_zone(0.7) == ACWRZone.UNDERTRAINING
        assert classify_acwr_zone(0.79) == ACWRZone.UNDERTRAINING

    def test_optimal(self) -> None:
        assert classify_acwr_zone(0.8) == ACWRZone.OPTIMAL
        assert classify_acwr_zone(1.0) == ACWRZone.OPTIMAL
        assert classify_acwr_zone(1.3) == ACWRZone.OPTIMAL

    def test_caution(self) -> None:
        assert classify_acwr_zone(1.31) == ACWRZone.CAUTION
        assert classify_acwr_zone(1.4) == ACWRZone.CAUTION
        assert classify_acwr_zone(1.5) == ACWRZone.CAUTION

    def test_high_risk(self) -> None:
        assert classify_acwr_zone(1.51) == ACWRZone.HIGH_RISK
        assert classify_acwr_zone(2.0) == ACWRZone.HIGH_RISK
        assert classify_acwr_zone(2.1) == ACWRZone.HIGH_RISK

    def test_boundary_values(self) -> None:
        assert classify_acwr_zone(0.8) == ACWRZone.OPTIMAL
        assert classify_acwr_zone(1.3) == ACWRZone.OPTIMAL
        assert classify_acwr_zone(1.5) == ACWRZone.CAUTION


class TestComputeACWR:
    """Tests for ACWR computation."""

    def test_empty_loads(self) -> None:
        result = compute_acwr([], date(2026, 1, 28))
        assert result.acwr_value is None
        assert result.zone == ACWRZone.UNDERTRAINING

    def test_all_zeros(self) -> None:
        """Chronic near zero should return None ACWR."""
        loads = [0.0] * 28
        result = compute_acwr(loads, date(2026, 1, 28))
        assert result.acwr_value is None
        assert result.zone == ACWRZone.UNDERTRAINING

    def test_constant_load_near_one(self) -> None:
        """Constant load should yield ACWR near 1.0 (optimal)."""
        loads = [100.0] * 35
        result = compute_acwr(loads, date(2026, 2, 4))
        assert result.acwr_value is not None
        assert result.acwr_value == pytest.approx(1.0, abs=0.01)
        assert result.zone == ACWRZone.OPTIMAL

    def test_spike_produces_high_acwr(self) -> None:
        """A sudden spike after low loads should produce high ACWR."""
        loads = [50.0] * 21 + [300.0] * 7
        result = compute_acwr(loads, date(2026, 1, 28))
        assert result.acwr_value is not None
        assert result.acwr_value > 1.3

    def test_low_recent_load_produces_low_acwr(self) -> None:
        """Low recent loads after high historical loads -> low ACWR."""
        loads = [200.0] * 21 + [30.0] * 7
        result = compute_acwr(loads, date(2026, 1, 28))
        assert result.acwr_value is not None
        assert result.acwr_value < 0.8
        assert result.zone == ACWRZone.UNDERTRAINING

    def test_known_28_day_reference(self) -> None:
        """Test with a known 28-day reference dataset.

        We use a stepped load pattern and verify ACWR within tolerance.
        Loads: 7 days at 100, 7 days at 150, 7 days at 200, 7 days at 250.
        This is a gradually increasing load, so acute > chronic -> ACWR > 1.
        """
        loads = [100.0] * 7 + [150.0] * 7 + [200.0] * 7 + [250.0] * 7
        result = compute_acwr(loads, date(2026, 1, 28))
        assert result.acwr_value is not None

        # Manually compute expected values:
        # Acute EWMA (decay=7, gamma=0.25) and Chronic EWMA (decay=28, gamma=2/29)
        from app.analytics.ewma import compute_ewma

        acute = compute_ewma(loads, 7)
        chronic = compute_ewma(loads, 28)
        expected_acwr = acute[-1] / chronic[-1]

        assert result.acwr_value == pytest.approx(expected_acwr, abs=0.01)
        assert result.acute_ewma == pytest.approx(acute[-1], abs=0.01)
        assert result.chronic_ewma == pytest.approx(chronic[-1], abs=0.01)

    def test_result_date(self) -> None:
        loads = [100.0] * 7
        result = compute_acwr(loads, date(2026, 2, 15))
        assert result.date == date(2026, 2, 15)
