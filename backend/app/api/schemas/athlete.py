"""Athlete-related Pydantic schemas."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, EmailStr


class AthleteListResponse(BaseModel):
    """Athlete summary for list endpoints."""

    id: uuid.UUID
    email: str
    full_name: str
    is_active: bool

    model_config = {"from_attributes": True}


class AthleteDetailResponse(BaseModel):
    """Detailed athlete response including profile info."""

    id: uuid.UUID
    email: str
    full_name: str
    is_active: bool
    team_id: uuid.UUID | None = None

    model_config = {"from_attributes": True}


class AthleteCreateRequest(BaseModel):
    """Request body for creating a new athlete."""

    email: EmailStr
    password: str
    full_name: str
    date_of_birth: date | None = None
    position: str | None = None
    height_cm: float | None = None
    weight_kg: float | None = None


class AthleteUpdateRequest(BaseModel):
    """Request body for updating athlete user fields."""

    full_name: str | None = None
    email: EmailStr | None = None


class AthleteProfileResponse(BaseModel):
    """Athlete profile response."""

    id: uuid.UUID
    user_id: uuid.UUID
    date_of_birth: date | None = None
    position: str | None = None
    height_cm: float | None = None
    weight_kg: float | None = None
    garmin_connected: bool = False
    ow_connection_id: str | None = None
    health_connect_connected: bool = False
    last_sync_at: datetime | None = None

    model_config = {"from_attributes": True}

    @classmethod
    def model_validate(cls, obj: object, **kwargs: object) -> "AthleteProfileResponse":
        """Custom validation to map last_health_connect_sync_at to last_sync_at."""
        instance = super().model_validate(obj, **kwargs)
        if hasattr(obj, "last_health_connect_sync_at") and obj.last_health_connect_sync_at:  # type: ignore[union-attr]
            instance.last_sync_at = obj.last_health_connect_sync_at  # type: ignore[union-attr]
        return instance


class AthleteProfileUpdateRequest(BaseModel):
    """Request body for updating athlete profile fields."""

    date_of_birth: date | None = None
    position: str | None = None
    height_cm: float | None = None
    weight_kg: float | None = None
