"""Tests for the Open Wearables API client."""

from datetime import UTC, datetime

import httpx
import pytest
import respx

from app.services.ow_client import OWClient


@pytest.fixture
def ow_client() -> OWClient:
    """Create an OW client with a test base URL."""
    client = httpx.AsyncClient(
        base_url="http://ow-test:8000",
        headers={"X-Open-Wearables-API-Key": "test-key"},
    )
    return OWClient(client=client)


class TestCreateUser:
    @respx.mock
    async def test_create_user(self, ow_client: OWClient) -> None:
        respx.post("http://ow-test:8000/api/v1/users").mock(
            return_value=httpx.Response(200, json={
                "id": "ow-user-1",
                "email": "test@example.com",
                "first_name": "Test",
                "last_name": "User",
            })
        )
        user = await ow_client.create_user("test@example.com", "Test", "User")
        assert user.id == "ow-user-1"
        assert user.email == "test@example.com"

    @respx.mock
    async def test_create_user_http_error(self, ow_client: OWClient) -> None:
        respx.post("http://ow-test:8000/api/v1/users").mock(
            return_value=httpx.Response(400, json={"detail": "Bad request"})
        )
        with pytest.raises(httpx.HTTPStatusError):
            await ow_client.create_user("bad@example.com", "Bad", "User")


class TestGetUser:
    @respx.mock
    async def test_get_user(self, ow_client: OWClient) -> None:
        respx.get("http://ow-test:8000/api/v1/users/ow-user-1").mock(
            return_value=httpx.Response(200, json={
                "id": "ow-user-1",
                "email": "test@example.com",
                "first_name": "Test",
                "last_name": "User",
            })
        )
        user = await ow_client.get_user("ow-user-1")
        assert user.id == "ow-user-1"

    @respx.mock
    async def test_get_user_not_found(self, ow_client: OWClient) -> None:
        respx.get("http://ow-test:8000/api/v1/users/nonexistent").mock(
            return_value=httpx.Response(404, json={"detail": "Not found"})
        )
        with pytest.raises(httpx.HTTPStatusError):
            await ow_client.get_user("nonexistent")


class TestGetUserConnections:
    @respx.mock
    async def test_get_connections(self, ow_client: OWClient) -> None:
        respx.get("http://ow-test:8000/api/v1/users/ow-user-1/connections").mock(
            return_value=httpx.Response(200, json={
                "data": [
                    {
                        "id": "conn-1",
                        "user_id": "ow-user-1",
                        "provider": "garmin",
                        "status": "active",
                    }
                ]
            })
        )
        connections = await ow_client.get_user_connections("ow-user-1")
        assert len(connections) == 1
        assert connections[0].provider == "garmin"
        assert connections[0].status == "active"

    @respx.mock
    async def test_get_connections_empty(self, ow_client: OWClient) -> None:
        respx.get("http://ow-test:8000/api/v1/users/ow-user-1/connections").mock(
            return_value=httpx.Response(200, json={"data": []})
        )
        connections = await ow_client.get_user_connections("ow-user-1")
        assert connections == []


class TestGetTimeseries:
    @respx.mock
    async def test_get_timeseries(self, ow_client: OWClient) -> None:
        respx.get("http://ow-test:8000/api/v1/users/ow-user-1/timeseries").mock(
            return_value=httpx.Response(200, json={
                "data": [
                    {"timestamp": "2026-02-28T07:00:00Z", "type": "resting_hr", "value": 52.0},
                    {"timestamp": "2026-02-28T07:00:00Z", "type": "hrv_rmssd", "value": 45.0},
                ]
            })
        )
        start = datetime(2026, 2, 28, 0, 0, 0, tzinfo=UTC)
        end = datetime(2026, 2, 28, 23, 59, 59, tzinfo=UTC)
        data = await ow_client.get_timeseries("ow-user-1", ["resting_hr", "hrv_rmssd"], start, end)
        assert len(data) == 2
        assert data[0].type == "resting_hr"
        assert data[1].value == 45.0


class TestGetWorkouts:
    @respx.mock
    async def test_get_workouts(self, ow_client: OWClient) -> None:
        respx.get("http://ow-test:8000/api/v1/users/ow-user-1/workouts").mock(
            return_value=httpx.Response(200, json={
                "data": [
                    {
                        "id": "workout-1",
                        "user_id": "ow-user-1",
                        "sport": "running",
                        "start_time": "2026-02-28T10:00:00Z",
                        "end_time": "2026-02-28T11:00:00Z",
                        "duration_seconds": 3600,
                        "details": {"hr_avg": 155.0, "distance_m": 10000.0},
                    }
                ]
            })
        )
        start = datetime(2026, 2, 28, 0, 0, 0, tzinfo=UTC)
        end = datetime(2026, 2, 28, 23, 59, 59, tzinfo=UTC)
        workouts = await ow_client.get_workouts("ow-user-1", start, end)
        assert len(workouts) == 1
        assert workouts[0].id == "workout-1"
        assert workouts[0].details is not None
        assert workouts[0].details.hr_avg == 155.0


class TestGetSleep:
    @respx.mock
    async def test_get_sleep(self, ow_client: OWClient) -> None:
        respx.get("http://ow-test:8000/api/v1/users/ow-user-1/sleep").mock(
            return_value=httpx.Response(200, json={
                "data": [
                    {
                        "id": "sleep-1",
                        "user_id": "ow-user-1",
                        "start_time": "2026-02-27T22:00:00Z",
                        "end_time": "2026-02-28T06:30:00Z",
                        "duration_minutes": 510.0,
                        "score": 82.0,
                        "details": {"deep_minutes": 90.0, "rem_minutes": 100.0},
                    }
                ]
            })
        )
        start = datetime(2026, 2, 27, 0, 0, 0, tzinfo=UTC)
        end = datetime(2026, 2, 28, 23, 59, 59, tzinfo=UTC)
        sleep = await ow_client.get_sleep("ow-user-1", start, end)
        assert len(sleep) == 1
        assert sleep[0].duration_minutes == 510.0
        assert sleep[0].details is not None
        assert sleep[0].details.deep_minutes == 90.0


class TestPagination:
    @respx.mock
    async def test_handles_pagination(self, ow_client: OWClient) -> None:
        # Page 1
        respx.get("http://ow-test:8000/api/v1/users/ow-user-1/connections").mock(
            side_effect=[
                httpx.Response(200, json={
                    "data": [{"id": "c1", "user_id": "u1", "provider": "garmin", "status": "active"}],
                    "next_cursor": "page2",
                }),
                httpx.Response(200, json={
                    "data": [{"id": "c2", "user_id": "u1", "provider": "fitbit", "status": "active"}],
                }),
            ]
        )
        connections = await ow_client.get_user_connections("ow-user-1")
        assert len(connections) == 2
        assert connections[0].id == "c1"
        assert connections[1].id == "c2"
