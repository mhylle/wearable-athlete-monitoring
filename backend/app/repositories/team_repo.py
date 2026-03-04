"""Team repository for database operations."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.team import Team


class TeamRepository:
    """Database operations for Team model."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_team(self, team_id: uuid.UUID) -> Team | None:
        """Get a team by ID."""
        result = await self.db.execute(select(Team).where(Team.id == team_id))
        return result.scalar_one_or_none()

    async def create_team(self, data: dict) -> Team:
        """Create a new team."""
        team = Team(**data)
        self.db.add(team)
        await self.db.commit()
        await self.db.refresh(team)
        return team

    async def update_team(self, team_id: uuid.UUID, data: dict) -> Team | None:
        """Update an existing team."""
        team = await self.get_team(team_id)
        if team is None:
            return None
        for key, value in data.items():
            setattr(team, key, value)
        await self.db.commit()
        await self.db.refresh(team)
        return team
