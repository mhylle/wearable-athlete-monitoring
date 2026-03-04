"""Team management API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.team import TeamResponse, TeamUpdateRequest
from app.auth.dependencies import require_coach
from app.db import get_db
from app.models.user import User
from app.repositories.team_repo import TeamRepository

team_router = APIRouter(prefix="/api/v1/team", tags=["team"])


@team_router.get("/", response_model=TeamResponse)
async def get_team(
    current_user: User = Depends(require_coach),
    db: AsyncSession = Depends(get_db),
) -> TeamResponse:
    """Get the current coach's team information."""
    if current_user.team_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No team assigned",
        )
    repo = TeamRepository(db)
    team = await repo.get_team(current_user.team_id)
    if team is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found",
        )
    return TeamResponse.model_validate(team)


@team_router.put("/", response_model=TeamResponse)
async def update_team(
    body: TeamUpdateRequest,
    current_user: User = Depends(require_coach),
    db: AsyncSession = Depends(get_db),
) -> TeamResponse:
    """Update the current coach's team information."""
    if current_user.team_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No team assigned",
        )
    repo = TeamRepository(db)
    update_data = body.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update",
        )
    team = await repo.update_team(current_user.team_id, update_data)
    if team is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found",
        )
    return TeamResponse.model_validate(team)
