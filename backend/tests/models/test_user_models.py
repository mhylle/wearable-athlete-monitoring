"""Tests for User and AthleteProfile models."""

from app.models.athlete_profile import AthleteProfile
from app.models.user import User


class TestUserModel:
    """Test User model definition and attributes."""

    def test_table_name(self) -> None:
        assert User.__tablename__ == "users"

    def test_columns_exist(self) -> None:
        column_names = {c.name for c in User.__table__.columns}
        expected = {"id", "email", "hashed_password", "role", "full_name", "team_id", "ow_user_id", "is_active", "created_at"}
        assert expected.issubset(column_names)

    def test_email_unique(self) -> None:
        col = User.__table__.c.email
        assert col.unique

    def test_email_not_nullable(self) -> None:
        col = User.__table__.c.email
        assert not col.nullable

    def test_email_indexed(self) -> None:
        col = User.__table__.c.email
        assert col.index

    def test_role_not_nullable(self) -> None:
        col = User.__table__.c.role
        assert not col.nullable

    def test_team_id_nullable(self) -> None:
        col = User.__table__.c.team_id
        assert col.nullable

    def test_team_id_foreign_key(self) -> None:
        col = User.__table__.c.team_id
        fk_targets = {fk.target_fullname for fk in col.foreign_keys}
        assert "teams.id" in fk_targets

    def test_is_active_default(self) -> None:
        col = User.__table__.c.is_active
        assert col.default is not None
        assert col.default.arg is True

    def test_fixture_fields(self, sample_user: User) -> None:
        assert sample_user.email == "athlete@test.com"
        assert sample_user.role == "athlete"
        assert sample_user.is_active is True


class TestAthleteProfileModel:
    """Test AthleteProfile model definition."""

    def test_table_name(self) -> None:
        assert AthleteProfile.__tablename__ == "athlete_profiles"

    def test_columns_exist(self) -> None:
        column_names = {c.name for c in AthleteProfile.__table__.columns}
        expected = {"id", "user_id", "date_of_birth", "position", "height_cm", "weight_kg", "garmin_connected", "ow_connection_id"}
        assert expected.issubset(column_names)

    def test_user_id_unique(self) -> None:
        col = AthleteProfile.__table__.c.user_id
        assert col.unique

    def test_user_id_foreign_key(self) -> None:
        col = AthleteProfile.__table__.c.user_id
        fk_targets = {fk.target_fullname for fk in col.foreign_keys}
        assert "users.id" in fk_targets

    def test_garmin_connected_default(self) -> None:
        col = AthleteProfile.__table__.c.garmin_connected
        assert col.default is not None
        assert col.default.arg is False

    def test_fixture_fields(self, sample_athlete_profile: AthleteProfile) -> None:
        assert sample_athlete_profile.position == "midfielder"
        assert sample_athlete_profile.height_cm == 180.0
