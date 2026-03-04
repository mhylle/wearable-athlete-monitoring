"""Team-related Pydantic schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel


class TeamResponse(BaseModel):
    """Team information response."""

    id: uuid.UUID
    name: str
    sport: str
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class TeamUpdateRequest(BaseModel):
    """Request body for updating team info."""

    name: str | None = None
    sport: str | None = None
