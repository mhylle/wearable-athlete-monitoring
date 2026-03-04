"""Tests for the Team model."""

from app.models.team import Team


class TestTeamModel:
    """Test Team model definition and attributes."""

    def test_table_name(self) -> None:
        assert Team.__tablename__ == "teams"

    def test_columns_exist(self) -> None:
        column_names = {c.name for c in Team.__table__.columns}
        assert "id" in column_names
        assert "name" in column_names
        assert "sport" in column_names
        assert "created_at" in column_names

    def test_id_is_primary_key(self) -> None:
        col = Team.__table__.c.id
        assert col.primary_key

    def test_name_not_nullable(self) -> None:
        col = Team.__table__.c.name
        assert not col.nullable

    def test_sport_has_default(self) -> None:
        """Sport column should have a Python-side default of 'football'."""
        col = Team.__table__.c.sport
        assert col.default is not None
        assert col.default.arg == "football"

    def test_created_at_has_server_default(self) -> None:
        col = Team.__table__.c.created_at
        assert col.server_default is not None

    def test_fixture_fields(self, sample_team: Team) -> None:
        assert sample_team.name == "Test FC"
        assert sample_team.sport == "football"
        assert sample_team.id is not None
