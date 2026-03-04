"""Tests for the Open Wearables user service."""

import uuid
from unittest.mock import AsyncMock, MagicMock

from app.models.user import User
from app.services.ow_schemas import OWConnection, OWUser
from app.services.ow_user_service import (
    get_garmin_connection_status,
    provision_ow_user,
)


def _make_athlete(ow_user_id: str | None = None) -> User:
    return User(
        id=uuid.uuid4(),
        email="athlete@test.com",
        hashed_password="hashed",
        role="athlete",
        full_name="Test Athlete",
        ow_user_id=ow_user_id,
    )


class TestProvisionOWUser:
    async def test_creates_ow_user_and_stores_id(self) -> None:
        athlete = _make_athlete()
        mock_client = AsyncMock()
        mock_client.create_user.return_value = OWUser(
            id="ow-123",
            email="athlete@test.com",
            first_name="Test",
            last_name="Athlete",
        )
        mock_db = AsyncMock()
        mock_db.add = MagicMock()

        ow_id = await provision_ow_user(athlete, mock_client, mock_db)

        assert ow_id == "ow-123"
        assert athlete.ow_user_id == "ow-123"
        mock_client.create_user.assert_called_once_with(
            email="athlete@test.com",
            first_name="Test",
            last_name="Athlete",
        )
        mock_db.add.assert_called_once_with(athlete)
        mock_db.commit.assert_called_once()

    async def test_skips_if_already_provisioned(self) -> None:
        athlete = _make_athlete(ow_user_id="existing-ow-id")
        mock_client = AsyncMock()
        mock_db = AsyncMock()

        ow_id = await provision_ow_user(athlete, mock_client, mock_db)

        assert ow_id == "existing-ow-id"
        mock_client.create_user.assert_not_called()
        mock_db.commit.assert_not_called()

    async def test_handles_single_name(self) -> None:
        athlete = _make_athlete()
        athlete.full_name = "Madonna"
        mock_client = AsyncMock()
        mock_client.create_user.return_value = OWUser(
            id="ow-456",
            email="athlete@test.com",
            first_name="Madonna",
            last_name="",
        )
        mock_db = AsyncMock()
        mock_db.add = MagicMock()

        await provision_ow_user(athlete, mock_client, mock_db)

        mock_client.create_user.assert_called_once_with(
            email="athlete@test.com",
            first_name="Madonna",
            last_name="",
        )


class TestGetGarminConnectionStatus:
    async def test_returns_connected_when_active(self) -> None:
        athlete = _make_athlete(ow_user_id="ow-123")
        mock_client = AsyncMock()
        mock_client.get_user_connections.return_value = [
            OWConnection(
                id="conn-1",
                user_id="ow-123",
                provider="garmin",
                status="active",
            )
        ]

        status = await get_garmin_connection_status(athlete, mock_client)

        assert status.connected is True
        assert status.connection_id == "conn-1"

    async def test_returns_disconnected_when_no_garmin(self) -> None:
        athlete = _make_athlete(ow_user_id="ow-123")
        mock_client = AsyncMock()
        mock_client.get_user_connections.return_value = [
            OWConnection(
                id="conn-1",
                user_id="ow-123",
                provider="fitbit",
                status="active",
            )
        ]

        status = await get_garmin_connection_status(athlete, mock_client)

        assert status.connected is False

    async def test_returns_disconnected_when_no_ow_user(self) -> None:
        athlete = _make_athlete()
        mock_client = AsyncMock()

        status = await get_garmin_connection_status(athlete, mock_client)

        assert status.connected is False
        mock_client.get_user_connections.assert_not_called()

    async def test_returns_disconnected_when_garmin_inactive(self) -> None:
        athlete = _make_athlete(ow_user_id="ow-123")
        mock_client = AsyncMock()
        mock_client.get_user_connections.return_value = [
            OWConnection(
                id="conn-1",
                user_id="ow-123",
                provider="garmin",
                status="disconnected",
            )
        ]

        status = await get_garmin_connection_status(athlete, mock_client)

        assert status.connected is False
