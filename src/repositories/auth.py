from operator import or_
from typing import Optional

from select import select

from src.database import AsyncSessionLocal
from src.models.user import User
from src.repositories.base import BaseRepository
from src.schemas.auth.user import (
    UserUpdateSchema,
    UserCreateSchema
)


class AuthRepositoryError(Exception):
    """Base class for authentication repository errors."""
    pass


class AuthRepository(
    BaseRepository[User, UserCreateSchema, UserUpdateSchema]
):
    """Repository for user authentication and management."""

    def __init__(self, db: AsyncSessionLocal):
        super().__init__(User, db)

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get a user by username."""
        return await self.get_by_field("username", username.lower())

    async def get_user_by_email(self, email: str) -> User | None:
        """Get a user by email."""
        return await self.get_by_field("email", email.lower())

    async def get_user_by_identifier(self, identifier: str) -> Optional[User]:
        """Get user by username or email."""
        query = select(User).where(
            or_(
                User.username == identifier.lower(),
                User.email == identifier.lower()
            )
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def verify_user(self, user_id: int) -> Optional[User]:
        """Verify user by ID."""
        user = await self.get(user_id)
        if user:
            user.is_verified = True
            await self.db.commit()
            await self.db.refresh(user)
        return user
