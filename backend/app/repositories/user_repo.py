"""User repository for database operations."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.athlete_profile import AthleteProfile
from app.models.user import User


class UserRepository:
    """Database operations for User and AthleteProfile models."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_user_by_id(self, user_id: uuid.UUID) -> User | None:
        """Get a user by ID."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> User | None:
        """Get a user by email."""
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def list_athletes(self, team_id: uuid.UUID) -> list[User]:
        """List all active athletes for a team."""
        result = await self.db.execute(
            select(User).where(
                User.team_id == team_id,
                User.role == "athlete",
                User.is_active.is_(True),
            )
        )
        return list(result.scalars().all())

    async def list_coaches(self, team_id: uuid.UUID) -> list[User]:
        """List all active coaches for a team."""
        result = await self.db.execute(
            select(User).where(
                User.team_id == team_id,
                User.role == "coach",
                User.is_active.is_(True),
            )
        )
        return list(result.scalars().all())

    async def create_user(self, data: dict) -> User:
        """Create a new user."""
        user = User(**data)
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update_user(self, user_id: uuid.UUID, data: dict) -> User | None:
        """Update a user."""
        user = await self.get_user_by_id(user_id)
        if user is None:
            return None
        for key, value in data.items():
            setattr(user, key, value)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def deactivate_user(self, user_id: uuid.UUID) -> User | None:
        """Deactivate a user (soft delete)."""
        user = await self.get_user_by_id(user_id)
        if user is None:
            return None
        user.is_active = False
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def get_athlete_profile(self, user_id: uuid.UUID) -> AthleteProfile | None:
        """Get the athlete profile for a user."""
        result = await self.db.execute(
            select(AthleteProfile).where(AthleteProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create_athlete_profile(self, data: dict) -> AthleteProfile:
        """Create an athlete profile."""
        profile = AthleteProfile(**data)
        self.db.add(profile)
        await self.db.commit()
        await self.db.refresh(profile)
        return profile

    async def update_athlete_profile(
        self, user_id: uuid.UUID, data: dict
    ) -> AthleteProfile | None:
        """Update an athlete profile."""
        profile = await self.get_athlete_profile(user_id)
        if profile is None:
            return None
        for key, value in data.items():
            setattr(profile, key, value)
        await self.db.commit()
        await self.db.refresh(profile)
        return profile
