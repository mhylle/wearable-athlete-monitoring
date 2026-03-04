"""Health Connect data ingest API -- receives data pushed from the mobile app."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.health_connect import HCSyncRequest, HCSyncResponse, HCSyncStatus
from app.auth.dependencies import get_current_user
from app.db import get_db
from app.models.user import User
from app.services import hc_sync_service

router = APIRouter(prefix="/api/v1/health-data", tags=["health-data"])


@router.post("/sync", response_model=HCSyncResponse)
async def sync_health_data(
    body: HCSyncRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> HCSyncResponse:
    """Receive a batch of Health Connect data from the mobile app.

    Athlete-only endpoint. The mobile app reads from Health Connect
    and pushes the data here.
    """
    return await hc_sync_service.ingest_health_data(db, current_user.id, body)


@router.get("/status", response_model=HCSyncStatus)
async def get_health_data_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> HCSyncStatus:
    """Get the Health Connect sync status for the current athlete."""
    status = await hc_sync_service.get_sync_status(db, current_user.id)
    return HCSyncStatus(**status)
