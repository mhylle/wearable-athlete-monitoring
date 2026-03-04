"""Tests for sleep analysis computations."""

from datetime import date

from app.analytics.sleep import (
    SleepRecord,
    SleepSummary,
    compute_sleep_average,
    compute_sleep_summary,
)


def _make_records(
    target_date: date,
    total: float = 0.0,
    deep: float = 0.0,
    rem: float = 0.0,
    light: float = 0.0,
    awake: float = 0.0,
) -> list[SleepRecord]:
    """Helper to create sleep records for a date."""
    records: list[SleepRecord] = []
    if total > 0:
        records.append(SleepRecord(metric_type="sleep_total", value=total, date=target_date))
    if deep > 0:
        records.append(SleepRecord(metric_type="sleep_deep", value=deep, date=target_date))
    if rem > 0:
        records.append(SleepRecord(metric_type="sleep_rem", value=rem, date=target_date))
    if light > 0:
        records.append(SleepRecord(metric_type="sleep_light", value=light, date=target_date))
    if awake > 0:
        records.append(SleepRecord(metric_type="sleep_awake", value=awake, date=target_date))
    return records


class TestSleepSummary:
    """Tests for compute_sleep_summary."""

    def test_basic_summary(self) -> None:
        """Compute summary with all sleep metrics."""
        d = date(2025, 1, 15)
        records = _make_records(d, total=480.0, deep=90.0, rem=120.0, light=240.0, awake=30.0)
        summary = compute_sleep_summary(records, d)

        assert summary.date == d
        assert summary.total_minutes == 480.0
        assert summary.deep_minutes == 90.0
        assert summary.rem_minutes == 120.0
        assert summary.light_minutes == 240.0
        assert summary.awake_minutes == 30.0

    def test_sleep_efficiency(self) -> None:
        """Efficiency = (total - awake) / total."""
        d = date(2025, 1, 15)
        records = _make_records(d, total=480.0, awake=48.0)
        summary = compute_sleep_summary(records, d)

        expected_efficiency = (480.0 - 48.0) / 480.0
        assert abs(summary.efficiency - expected_efficiency) < 0.001

    def test_perfect_efficiency(self) -> None:
        """Zero awake minutes -> efficiency 1.0."""
        d = date(2025, 1, 15)
        records = _make_records(d, total=480.0, awake=0.0)
        summary = compute_sleep_summary(records, d)

        assert summary.efficiency == 1.0

    def test_derive_total_from_stages(self) -> None:
        """If total not provided, derive from stage breakdown."""
        d = date(2025, 1, 15)
        records = _make_records(d, deep=90.0, rem=120.0, light=240.0, awake=30.0)
        summary = compute_sleep_summary(records, d)

        assert summary.total_minutes == 480.0  # 90 + 120 + 240 + 30

    def test_no_records_for_date(self) -> None:
        """No matching records produce empty summary."""
        d = date(2025, 1, 15)
        other = date(2025, 1, 14)
        records = _make_records(other, total=480.0)
        summary = compute_sleep_summary(records, d)

        assert summary.total_minutes == 0.0
        assert summary.efficiency == 0.0

    def test_empty_records(self) -> None:
        """Empty records list produces zero summary."""
        d = date(2025, 1, 15)
        summary = compute_sleep_summary([], d)

        assert summary.total_minutes == 0.0
        assert summary.efficiency == 0.0

    def test_efficiency_capped_at_1(self) -> None:
        """Efficiency never exceeds 1.0 even with data anomalies."""
        d = date(2025, 1, 15)
        # Awake = 0, so efficiency = total/total = 1.0
        records = _make_records(d, total=480.0, awake=0.0)
        summary = compute_sleep_summary(records, d)
        assert summary.efficiency <= 1.0

    def test_efficiency_not_negative(self) -> None:
        """Efficiency is clamped to [0, 1] even if awake > total (data error)."""
        d = date(2025, 1, 15)
        # Awake > total is a data error; efficiency should be clamped to 0
        records = _make_records(d, total=100.0, awake=150.0)
        summary = compute_sleep_summary(records, d)
        assert summary.efficiency >= 0.0


class TestSleepAverage:
    """Tests for compute_sleep_average."""

    def test_7day_average(self) -> None:
        """Average over 7 days of sleep data."""
        summaries = []
        for i in range(7):
            summaries.append(
                SleepSummary(
                    date=date(2025, 1, 1 + i),
                    total_minutes=450.0 + i * 10,
                    deep_minutes=80.0 + i,
                    rem_minutes=100.0 + i * 2,
                    light_minutes=250.0,
                    awake_minutes=20.0 + i,
                    efficiency=0.90 + i * 0.01,
                )
            )

        avg = compute_sleep_average(summaries, days=7)

        assert avg.days == 7
        assert abs(avg.avg_total_minutes - sum(s.total_minutes for s in summaries) / 7) < 0.01
        assert abs(avg.avg_deep_minutes - sum(s.deep_minutes for s in summaries) / 7) < 0.01

    def test_average_uses_last_n_days(self) -> None:
        """Average uses only the last N summaries."""
        summaries = []
        for i in range(10):
            summaries.append(
                SleepSummary(
                    date=date(2025, 1, 1 + i),
                    total_minutes=400.0 if i < 3 else 500.0,
                    deep_minutes=80.0,
                    rem_minutes=100.0,
                    light_minutes=250.0,
                    awake_minutes=20.0,
                    efficiency=0.90,
                )
            )

        avg = compute_sleep_average(summaries, days=7)
        assert avg.days == 7
        assert avg.avg_total_minutes == 500.0  # last 7 are all 500

    def test_empty_summaries(self) -> None:
        """Empty list returns zero average."""
        avg = compute_sleep_average([], days=7)

        assert avg.days == 0
        assert avg.avg_total_minutes == 0.0
        assert avg.avg_efficiency == 0.0

    def test_fewer_than_requested_days(self) -> None:
        """If fewer summaries than requested, average all available."""
        summaries = [
            SleepSummary(
                date=date(2025, 1, 1),
                total_minutes=480.0,
                deep_minutes=90.0,
                rem_minutes=120.0,
                light_minutes=240.0,
                awake_minutes=30.0,
                efficiency=0.9375,
            ),
            SleepSummary(
                date=date(2025, 1, 2),
                total_minutes=420.0,
                deep_minutes=80.0,
                rem_minutes=110.0,
                light_minutes=200.0,
                awake_minutes=30.0,
                efficiency=0.9286,
            ),
        ]

        avg = compute_sleep_average(summaries, days=7)
        assert avg.days == 2
        assert abs(avg.avg_total_minutes - 450.0) < 0.01
