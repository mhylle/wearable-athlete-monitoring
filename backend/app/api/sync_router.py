"""Sync API endpoints for triggering and monitoring data synchronization."""

import uuid

from fastapi import APIRouter, Depends, status

from app.auth.dependencies import require_coach
from app.models.user import User
from app.tasks.sync_tasks import (
    get_all_sync_statuses,
    get_sync_status,
    sync_all_athletes_task,
    sync_athlete_data_task,
)

router = APIRouter(prefix="/api/v1/sync", tags=["sync"])


@router.post(
    "/athlete/{athlete_id}",
    status_code=status.HTTP_202_ACCEPTED,
)
async def trigger_athlete_sync(
    athlete_id: uuid.UUID,
    current_user: User = Depends(require_coach),
) -> dict[str, str]:
    """Trigger a manual sync for one athlete. Coach only."""
    sync_athlete_data_task.delay(str(athlete_id))
    return {"status": "accepted", "athlete_id": str(athlete_id)}


@router.post(
    "/team",
    status_code=status.HTTP_202_ACCEPTED,
)
async def trigger_team_sync(
    current_user: User = Depends(require_coach),
) -> dict[str, str]:
    """Trigger a full team sync. Coach only."""
    sync_all_athletes_task.delay()
    return {"status": "accepted"}


@router.get("/status")
async def get_sync_statuses(
    current_user: User = Depends(require_coach),
) -> list[dict]:  # type: ignore[type-arg]
    """Return sync status for all athletes. Coach only."""
    return get_all_sync_statuses()


@router.get("/status/{athlete_id}")
async def get_athlete_sync_status(
    athlete_id: uuid.UUID,
    current_user: User = Depends(require_coach),
) -> dict:  # type: ignore[type-arg]
    """Return sync status for a specific athlete. Coach only."""
    status_data = get_sync_status(str(athlete_id))
    if status_data is None:
        return {"athlete_id": str(athlete_id), "status": "never_synced"}
    return status_data
