import logging
import uuid
from typing import Optional, Any

import bcrypt
from fastadmin import SqlAlchemyModelAdmin, register, action
from sqlalchemy import select, update

from src.database import AsyncSessionLocal
from src.models.meeting import Meeting
from src.models.user import User

logger = logging.getLogger(__name__)

logger.info("🔄 Registering FastAdmin models...")


@register(User, sqlalchemy_sessionmaker=AsyncSessionLocal)
class UserAdmin(SqlAlchemyModelAdmin):
    exclude = ("hashed_password",)
    list_display = ("id", "username", "is_superuser", "is_active")
    list_display_links = ("id", "username")
    list_filter = ("username", "is_superuser", "is_active")
    search_fields = ("username",)

    async def authenticate(self, username: str, password: str) -> uuid.UUID | int | None:
        """ИСПРАВЛЕНО: правильная аутентификация с детальным логированием"""
        print(f"🔐 FastAdmin authenticate called with: username='{username}', password='{'*' * len(password)}'")
        logger.info(f"🔐 Attempting authentication for: {username}")

        sessionmaker = self.get_sessionmaker()
        print(f"📊 Using sessionmaker: {sessionmaker}")

        async with sessionmaker()  as session:
            try:
                print(f"💾 Session created: {session}")

                # ИСПРАВЛЕНО: правильный запрос без filter_by с password
                query = select(User).where(User.username == username)
                print(f"🔍 Executing query: {query}")

                result = await session.execute(query)
                user = result.scalars().first()

                if not user:
                    print(f"❌ User not found in database: {username}")
                    logger.warning(f"❌ User not found: {username}")
                    return None

                print(f"✅ User found in database:")
                print(f"   - ID: {user.id}")
                print(f"   - Username: {user.username}")
                print(f"   - Email: {user.email}")
                print(f"   - Is Active: {user.is_active}")
                print(f"   - Is Superuser: {user.is_superuser}")
                print(f"   - Password hash length: {len(user.hashed_password) if user.hashed_password else 0}")

                # Проверяем статус пользователя
                if not user.is_active:
                    print("❌ User is not active")
                    logger.warning("❌ User is not active")
                    return None

                if not user.is_superuser:
                    print("❌ User is not superuser")
                    logger.warning("❌ User is not superuser")
                    return None

                # ИСПРАВЛЕНО: правильное имя поля hashed_password
                print("🔐 Checking password...")
                try:
                    password_valid = bcrypt.checkpw(password.encode(), user.hashed_password.encode())
                    print(f"🔑 Password check result: {password_valid}")
                except Exception as pwd_error:
                    print(f"❌ Password check error: {pwd_error}")
                    return None

                if not password_valid:
                    print("❌ Invalid password")
                    logger.warning("❌ Invalid password")
                    return None

                print(f"✅ Authentication successful for: {username}, returning user.id: {user.id}")
                logger.info(f"✅ Authentication successful for: {username}")
                return user.id

            except Exception as e:
                print(f"❌ Authentication exception: {e}")
                logger.error(f"❌ Authentication error: {e}")
                import traceback
                traceback.print_exc()
                return None

    async def change_password(self, id: uuid.UUID | int, password: str) -> None:
        sessionmaker = self.get_sessionmaker()
        async with sessionmaker() as session:
            hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            query = update(self.model_cls).where(User.id.in_([id])).values(hashed_password=hashed_password)
            await session.execute(query)
            await session.commit()

    async def orm_save_upload_field(self, obj: Any, field: str, base64: str) -> None:
        sessionmaker = self.get_sessionmaker()
        async with sessionmaker() as session:
            # convert base64 to bytes, upload to s3/filestorage, get url and save or save base64 as is to db (don't recomment it)
            query = update(self.model_cls).where(User.id.in_([obj.id])).values(**{field: base64})
            await session.execute(query)
            await session.commit()


@register(Meeting, sqlalchemy_sessionmaker=AsyncSessionLocal)
class MeetingAdmin(SqlAlchemyModelAdmin):
    """Admin interface for Meeting model."""

    list_display = ("id", "meeting_name", "meeting_date", "is_active")
    list_display_links = ("id", "meeting_name")
    list_filter = ("id", "meeting_name", "meeting_date", "is_active")
    search_fields = ("meeting_name",)

logger.info(f"✅ FastAdmin models registered!. Models: {UserAdmin.__name__}, {MeetingAdmin.__name__}")
