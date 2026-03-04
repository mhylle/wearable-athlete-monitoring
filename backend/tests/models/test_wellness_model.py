"""Tests for the WellnessEntry model."""

from datetime import date

from app.models.wellness_entry import WellnessEntry


class TestWellnessEntryModel:
    """Test WellnessEntry model definition."""

    def test_table_name(self) -> None:
        assert WellnessEntry.__tablename__ == "wellness_entries"

    def test_columns_exist(self) -> None:
        column_names = {c.name for c in WellnessEntry.__table__.columns}
        expected = {
            "id", "athlete_id", "date", "srpe", "srpe_duration_min",
            "soreness", "fatigue", "mood", "sleep_quality", "notes",
            "created_at",
        }
        assert expected.issubset(column_names)

    def test_athlete_id_indexed(self) -> None:
        col = WellnessEntry.__table__.c.athlete_id
        assert col.index

    def test_athlete_id_foreign_key(self) -> None:
        col = WellnessEntry.__table__.c.athlete_id
        fk_targets = {fk.target_fullname for fk in col.foreign_keys}
        assert "users.id" in fk_targets

    def test_unique_constraint_athlete_date(self) -> None:
        """There should be a unique constraint on (athlete_id, date)."""
        constraints = WellnessEntry.__table__.constraints
        unique_constraints = [
            c for c in constraints
            if hasattr(c, "columns") and c.__class__.__name__ == "UniqueConstraint"
        ]
        col_sets = [frozenset(c.name for c in uc.columns) for uc in unique_constraints]
        assert frozenset({"athlete_id", "date"}) in col_sets

    def test_date_not_nullable(self) -> None:
        col = WellnessEntry.__table__.c.date
        assert not col.nullable

    def test_fixture_fields(self, sample_wellness_entry: WellnessEntry) -> None:
        assert sample_wellness_entry.srpe == 7
        assert sample_wellness_entry.fatigue == 5
        assert sample_wellness_entry.date == date(2026, 2, 28)

    def test_wellness_fields_nullable(self) -> None:
        """All wellness rating fields should be nullable."""
        for col_name in ("srpe", "soreness", "fatigue", "mood", "sleep_quality"):
            col = WellnessEntry.__table__.c[col_name]
            assert col.nullable, f"{col_name} should be nullable"
