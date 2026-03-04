"""Coach-related Pydantic schemas."""

import uuid

from pydantic import BaseModel, EmailStr


class CoachResponse(BaseModel):
    """Coach information response."""

    id: uuid.UUID
    email: str
    full_name: str
    is_active: bool

    model_config = {"from_attributes": True}


class CoachInviteRequest(BaseModel):
    """Request body for inviting a new coach."""

    email: EmailStr
    full_name: str
    password: str
