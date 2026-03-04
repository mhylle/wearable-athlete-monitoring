"""Async HTTP client for the Open Wearables REST API."""

from datetime import datetime

import httpx

from app.config import settings
from app.services.ow_schemas import (
    OWConnection,
    OWDataPoint,
    OWSleep,
    OWUser,
    OWWorkout,
)


class OWClient:
    """Wraps Open Wearables API with typed methods and automatic pagination."""

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client
        self._owns_client = client is None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=settings.OW_API_URL,
                headers={"X-Open-Wearables-API-Key": settings.OW_API_KEY},
                timeout=30.0,
            )
            self._owns_client = True
        return self._client

    async def close(self) -> None:
        if self._client and self._owns_client:
            await self._client.aclose()
            self._client = None

    async def _get(self, path: str, params: dict[str, str] | None = None) -> dict:  # type: ignore[type-arg]
        client = await self._get_client()
        response = await client.get(path, params=params)
        response.raise_for_status()
        return response.json()  # type: ignore[no-any-return]

    async def _post(self, path: str, json: dict[str, str] | None = None) -> dict:  # type: ignore[type-arg]
        client = await self._get_client()
        response = await client.post(path, json=json)
        response.raise_for_status()
        return response.json()  # type: ignore[no-any-return]

    async def _get_paginated(self, path: str, params: dict[str, str] | None = None, key: str = "data") -> list[dict]:  # type: ignore[type-arg]
        """Fetch all pages of a paginated endpoint."""
        all_items: list[dict] = []  # type: ignore[type-arg]
        params = dict(params) if params else {}
        while True:
            data = await self._get(path, params=params)
            items = data.get(key, [])
            if isinstance(items, list):
                all_items.extend(items)
            else:
                all_items.append(items)
            cursor = data.get("next_cursor")
            if not cursor:
                break
            params["cursor"] = cursor
        return all_items

    # --- User operations ---

    async def create_user(self, email: str, first_name: str, last_name: str) -> OWUser:
        """Create a new user in Open Wearables."""
        data = await self._post(
            "/api/v1/users",
            json={"email": email, "first_name": first_name, "last_name": last_name},
        )
        return OWUser.model_validate(data)

    async def get_user(self, ow_user_id: str) -> OWUser:
        """Get an Open Wearables user by ID."""
        data = await self._get(f"/api/v1/users/{ow_user_id}")
        return OWUser.model_validate(data)

    # --- Connection operations ---

    async def get_user_connections(self, ow_user_id: str) -> list[OWConnection]:
        """Get all provider connections for a user."""
        items = await self._get_paginated(f"/api/v1/users/{ow_user_id}/connections")
        return [OWConnection.model_validate(item) for item in items]

    # --- Data operations ---

    async def get_timeseries(
        self,
        ow_user_id: str,
        types: list[str],
        start: datetime,
        end: datetime,
        resolution: str = "raw",
    ) -> list[OWDataPoint]:
        """Fetch time-series data points for a user."""
        params: dict[str, str] = {
            "types": ",".join(types),
            "start": start.isoformat(),
            "end": end.isoformat(),
            "resolution": resolution,
        }
        items = await self._get_paginated(f"/api/v1/users/{ow_user_id}/timeseries", params=params)
        return [OWDataPoint.model_validate(item) for item in items]

    async def get_workouts(
        self,
        ow_user_id: str,
        start: datetime,
        end: datetime,
    ) -> list[OWWorkout]:
        """Fetch workouts/activities for a user."""
        params: dict[str, str] = {
            "start": start.isoformat(),
            "end": end.isoformat(),
        }
        items = await self._get_paginated(f"/api/v1/users/{ow_user_id}/workouts", params=params)
        return [OWWorkout.model_validate(item) for item in items]

    async def get_sleep(
        self,
        ow_user_id: str,
        start: datetime,
        end: datetime,
    ) -> list[OWSleep]:
        """Fetch sleep records for a user."""
        params: dict[str, str] = {
            "start": start.isoformat(),
            "end": end.isoformat(),
        }
        items = await self._get_paginated(f"/api/v1/users/{ow_user_id}/sleep", params=params)
        return [OWSleep.model_validate(item) for item in items]
