import logging
import typing as tp
import uuid

import bcrypt
from fastadmin import SqlAlchemyModelAdmin, register
from sqlalchemy import select, update

from src.database import AsyncSessionLocal
from src.models.meeting import Meeting
from src.models.user import User

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


@register(User, sqlalchemy_sessionmaker=AsyncSessionLocal)
class UserAdmin(SqlAlchemyModelAdmin):
    exclude = ("hash_password",)
    list_display = ("id", "username", "is_superuser", "is_active")
    list_display_links = ("id", "username")
    list_filter = ("id", "username", "is_superuser", "is_active")
    search_fields = ("username",)

    async def authenticate(
        self, username: str, password: str
    ) -> uuid.UUID | int | None:
        sessionmaker = self.get_sessionmaker()
        async with sessionmaker() as session:
            query = select(User).where(
                (User.username == username)
                & (User.is_superuser.is_(True))
                & (User.is_active.is_(True))
            )
            result = await session.scalars(query)
            user = result.first()

            if not user:
                logger.debug(f"❌ User '{username}' not found or not authorized")
                return None

            logger.debug(f"✅ User found: {user.username} (ID: {user.id})")

            password_valid = bcrypt.checkpw(
                password.encode(), user.hash_password.encode()
            )
            logger.debug(f"🔑 Password validation: {password_valid}")

            if not password_valid:
                logger.debug(f"❌ Invalid password for: {username}")
                return None

            logger.debug(f"✅ Authentication successful: {username}")
            return user.id

    async def change_password(self, id: uuid.UUID | int, password: str) -> None:
        sessionmaker = self.get_sessionmaker()
        async with sessionmaker() as session:
            hash_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            query = (
                update(self.model_cls)
                .where(User.id.in_([id]))
                .values(hash_password=hash_password)
            )
            await session.execute(query)
            await session.commit()

    async def orm_save_upload_field(self, obj: tp.Any, field: str, base64: str) -> None:
        sessionmaker = self.get_sessionmaker()
        async with sessionmaker() as session:
            query = (
                update(self.model_cls)
                .where(User.id.in_([obj.id]))
                .values(**{field: base64})
            )
            await session.execute(query)
            await session.commit()


@register(Meeting, sqlalchemy_sessionmaker=AsyncSessionLocal)
class MeetingAdmin(SqlAlchemyModelAdmin):
    list_display = ("title", "description", "created_at", "updated_at")
    list_display_links = ("title",)
    list_filter = ("created_at", "updated_at")
    search_fields = ("title", "description")
