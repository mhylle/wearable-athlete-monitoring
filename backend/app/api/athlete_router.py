"""Athlete management API endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.athlete import (
    AthleteCreateRequest,
    AthleteDetailResponse,
    AthleteListResponse,
    AthleteProfileResponse,
    AthleteProfileUpdateRequest,
    AthleteUpdateRequest,
)
from app.auth.dependencies import get_current_user, require_coach
from app.auth.password import hash_password
from app.db import get_db
from app.models.user import User
from app.repositories.user_repo import UserRepository

athlete_router = APIRouter(prefix="/api/v1/athletes", tags=["athletes"])


def _check_coach_or_self(current_user: User, athlete_id: uuid.UUID) -> None:
    """Raise 403 if the user is neither a coach nor the athlete themselves."""
    if current_user.role == "coach":
        return
    if current_user.id == athlete_id:
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied",
    )


@athlete_router.get("/", response_model=list[AthleteListResponse])
async def list_athletes(
    current_user: User = Depends(require_coach),
    db: AsyncSession = Depends(get_db),
) -> list[AthleteListResponse]:
    """List all athletes on the coach's team."""
    repo = UserRepository(db)
    if current_user.team_id is None:
        return []
    athletes = await repo.list_athletes(current_user.team_id)
    return [AthleteListResponse.model_validate(a) for a in athletes]


@athlete_router.post(
    "/", response_model=AthleteDetailResponse, status_code=status.HTTP_201_CREATED
)
async def create_athlete(
    body: AthleteCreateRequest,
    current_user: User = Depends(require_coach),
    db: AsyncSession = Depends(get_db),
) -> AthleteDetailResponse:
    """Create a new athlete (coach only). Also creates their AthleteProfile."""
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
            "role": "athlete",
            "full_name": body.full_name,
            "team_id": current_user.team_id,
        }
    )

    await repo.create_athlete_profile(
        {
            "user_id": user.id,
            "date_of_birth": body.date_of_birth,
            "position": body.position,
            "height_cm": body.height_cm,
            "weight_kg": body.weight_kg,
        }
    )

    return AthleteDetailResponse.model_validate(user)


@athlete_router.get("/{athlete_id}", response_model=AthleteDetailResponse)
async def get_athlete(
    athlete_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AthleteDetailResponse:
    """Get athlete detail (coach or self)."""
    _check_coach_or_self(current_user, athlete_id)
    repo = UserRepository(db)
    user = await repo.get_user_by_id(athlete_id)
    if user is None or user.role != "athlete":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Athlete not found",
        )
    return AthleteDetailResponse.model_validate(user)


@athlete_router.put("/{athlete_id}", response_model=AthleteDetailResponse)
async def update_athlete(
    athlete_id: uuid.UUID,
    body: AthleteUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AthleteDetailResponse:
    """Update athlete user fields (coach or self)."""
    _check_coach_or_self(current_user, athlete_id)
    repo = UserRepository(db)

    user = await repo.get_user_by_id(athlete_id)
    if user is None or user.role != "athlete":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Athlete not found",
        )

    update_data = body.model_dump(exclude_unset=True)
    if not update_data:
        return AthleteDetailResponse.model_validate(user)

    if "email" in update_data:
        existing = await repo.get_user_by_email(update_data["email"])
        if existing is not None and existing.id != athlete_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

    updated = await repo.update_user(athlete_id, update_data)
    return AthleteDetailResponse.model_validate(updated)


@athlete_router.delete("/{athlete_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_athlete(
    athlete_id: uuid.UUID,
    current_user: User = Depends(require_coach),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Deactivate an athlete (coach only)."""
    repo = UserRepository(db)
    user = await repo.get_user_by_id(athlete_id)
    if user is None or user.role != "athlete":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Athlete not found",
        )
    await repo.deactivate_user(athlete_id)


@athlete_router.get(
    "/{athlete_id}/profile", response_model=AthleteProfileResponse
)
async def get_athlete_profile(
    athlete_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AthleteProfileResponse:
    """Get athlete profile (coach or self)."""
    _check_coach_or_self(current_user, athlete_id)
    repo = UserRepository(db)
    profile = await repo.get_athlete_profile(athlete_id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Athlete profile not found",
        )
    return AthleteProfileResponse.model_validate(profile)


@athlete_router.put(
    "/{athlete_id}/profile", response_model=AthleteProfileResponse
)
async def update_athlete_profile(
    athlete_id: uuid.UUID,
    body: AthleteProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AthleteProfileResponse:
    """Update athlete profile (coach or self)."""
    _check_coach_or_self(current_user, athlete_id)
    repo = UserRepository(db)

    update_data = body.model_dump(exclude_unset=True)
    if not update_data:
        profile = await repo.get_athlete_profile(athlete_id)
        if profile is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Athlete profile not found",
            )
        return AthleteProfileResponse.model_validate(profile)

    profile = await repo.update_athlete_profile(athlete_id, update_data)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Athlete profile not found",
        )
    return AthleteProfileResponse.model_validate(profile)
