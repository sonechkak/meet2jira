import logging
import re
from datetime import datetime
from select import select
from typing import Optional

import bcrypt

from src.database import AsyncSessionLocal
from src.models.user import User
from src.repositories.auth import AuthRepository
from src.schemas.auth.user import UserCreateSchema, UserUpdateSchema

logger = logging.getLogger(__name__)


class AuthService:
    """Service class for handling authentication logic."""

    def __init__(self, auth_repository):
        self.auth_repository = auth_repository

    async def get_user_by_id(
        self, session: AsyncSessionLocal, user_id: str
    ) -> Optional[User]:
        """Retrieve a user by their ID."""
        if not user_id:
            raise ValueError("User ID is required to get the user.")
        return await self.auth_repository.get_user_by_id(session, user_id)

    async def get_user_by_username(
        self, session: AsyncSessionLocal, username: str
    ) -> Optional[User]:
        """Retrieve a user by their username."""
        if not username:
            raise ValueError("Username is required to get the user.")
        try:
            return await self.auth_repository.get_user_by_username(session, username)
        except Exception as e:
            # Log the error
            raise ValueError(f"Failed to retrieve user by username: {e}")

    async def get_user_by_email(
        self, session: AsyncSessionLocal, email: str
    ) -> Optional[User]:
        """Get user by email."""
        try:
            result = await session.execute(select(User).where(User.email == email))
            return result.scalar_one_or_none()
        except Exception as e:
            raise ValueError(f"Failed to retrieve user by email: {e}")

    async def create_user(
        self, session: AsyncSessionLocal, user_data: UserCreateSchema
    ) -> Optional[User]:
        """Create a new user."""
        try:
            # Check if username or email already exists
            if user_data.username:
                existing_user = await self.get_user_by_username()
                if existing_user:
                    logger.warning(
                        f"User with username {user_data.username} already exists"
                    )
                    return None

            # Check if email already exists
            if user_data.email:
                existing_user = await self.get_user_by_email(session, user_data.email)
                if existing_user:
                    logger.warning(f"User with email {user_data.email} already exists")
                    return None

            # Create new user
            user = User(
                username=user_data.username,
                email=user_data.email,
                full_name=user_data.full_name,
                timezone=user_data.timezone,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

            session.add(user)
            await session.commit()
            await session.refresh(user)

            logger.debug(f"Created new user: {user.username or user.id}")
            return user

        except Exception as e:
            logger.error(f"Error creating user: {e!s}")
            await session.rollback()
            return None

    async def update_user(
        self, session: AsyncSessionLocal, user_id: int, user_data: UserUpdateSchema
    ) -> Optional[User]:
        """Update user information."""
        try:
            user = await self.get_user_by_id(session, user_id)
            if not user:
                return None

            # Update fields if provided
            if user_data.username is not None:
                user.username = user_data.username
            if user_data.email is not None:
                user.email = user_data.email
            if user_data.full_name is not None:
                user.full_name = user_data.full_name
            if user_data.is_active is not None:
                user.is_active = user_data.is_active

            user.updated_at = datetime.utcnow()

            await session.commit()
            await session.refresh(user)

            logger.debug(f"Updated user: {user.username or user.id}")
            return user

        except Exception as e:
            logger.debug(f"Error updating user {user_id}: {e!s}")
            await session.rollback()
            return None

    async def authenticate_user(self, identifier: str) -> Optional[User]:
        """Authenticate user by identifier."""
        try:
            user = None

            # Authenticate by username or email
            if identifier:
                # Try username first
                user = await self.auth_repository.get_user_by_username(identifier)
                if not user:
                    # Try email
                    user = await self.auth_repository.get_user_by_email(identifier)

            if not user:
                logger.warning(f"User not found: {identifier}")
                return None

            # Check if user is active
            if not user.is_active:
                logger.error(f"User is inactive: {identifier}")
                return None
            logger.debug(f"User authenticated: {user.username or user.id}")
            return user

        except Exception as e:
            logger.error(f"Error authenticating user: {e!s}")
            return None

    async def login(
        self,
        identifier: str,
        password: str,
        remember_me: bool,
        captcha: Optional[str] = None,
    ) -> Optional[User]:
        """Login the user with provided credentials."""
        if not identifier or not password:
            raise ValueError("Логин и пароль обязательны для входа")

        valid, msg = self.validate_password(password)
        if not valid:
            raise ValueError(msg)

        user = await self.auth_repository.get_user_by_username(identifier)
        if not user:
            user = await self.auth_repository.get_user_by_email(identifier)
        if not user:
            raise ValueError("Неверный логин или пароль.")

        if not bcrypt.checkpw(password.encode(), user.hash_password.encode()):
            raise ValueError("Неверный логин или пароль")

        return user

    def validate_password(self, password: str) -> tuple[bool, str]:
        """Validate the password according to specified rules."""
        if len(password) < 8:
            return False, "Пароль должен содержать минимум 8 символов"

        # if not re.search(r'[A-Z]', password):
        #     return False, "Пароль должен содержать заглавные буквы"

        if not re.search(r"[a-z]", password):
            return False, "Пароль должен содержать строчные буквы"

        if not re.search(r"\d", password):
            return False, "Пароль должен содержать цифры"

        return True, "Пароль валиден"


# Global user service instance
user_service = AuthService(auth_repository=AuthRepository)
