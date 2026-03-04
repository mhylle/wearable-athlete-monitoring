"""Coach management API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.coach import CoachInviteRequest, CoachResponse
from app.auth.dependencies import require_coach
from app.auth.password import hash_password
from app.db import get_db
from app.models.user import User
from app.repositories.user_repo import UserRepository

coach_router = APIRouter(prefix="/api/v1/coaches", tags=["coaches"])


@coach_router.get("/", response_model=list[CoachResponse])
async def list_coaches(
    current_user: User = Depends(require_coach),
    db: AsyncSession = Depends(get_db),
) -> list[CoachResponse]:
    """List all coaches on the team."""
    repo = UserRepository(db)
    if current_user.team_id is None:
        return []
    coaches = await repo.list_coaches(current_user.team_id)
    return [CoachResponse.model_validate(c) for c in coaches]


@coach_router.post(
    "/invite", response_model=CoachResponse, status_code=status.HTTP_201_CREATED
)
async def invite_coach(
    body: CoachInviteRequest,
    current_user: User = Depends(require_coach),
    db: AsyncSession = Depends(get_db),
) -> CoachResponse:
    """Invite a new coach to the team."""
    repo = UserRepository(db)

    existing = await repo.get_user_by_email(body.email)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = await repo.create_user(
        {
            "email": body.email,
            "hashed_password": hash_password(body.password),
            "role": "coach",
            "full_name": body.full_name,
            "team_id": current_user.team_id,
        }
    )

    return CoachResponse.model_validate(user)
