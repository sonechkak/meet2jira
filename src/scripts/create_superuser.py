import asyncio
import logging
import sys
from pathlib import Path

import bcrypt

from src.database import AsyncSessionLocal
from src.models.user import User

# Добавляем корень проекта в Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


async def create_superuser():
    """Создание суперпользователя"""

    logger.debug("🔐 Creating superuser for FastAdmin...")

    # Данные по умолчанию
    username = "admin"
    email = "admin@meet2jira.com"
    password = "admin123"
    full_name = "Administrator"

    logger.debug(f"Creating user: {username} / {email}")

    # Хешируем пароль
    hash_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    async with AsyncSessionLocal() as session:
        try:
            # Создаем нового суперпользователя
            superuser = User(
                username=username,
                email=email,
                full_name=full_name,
                hash_password=hash_password,
                is_superuser=True,
                is_active=True,
                is_verified=True,
                is_staff=True,
                is_admin=True,
            )

            session.add(superuser)
            await session.commit()

            logger.debug(f"✅ Superuser '{username}' created successfully!")
            logger.debug(f"📧 Email: {email}")
            logger.debug(f"🔑 Password: {password}")
            logger.debug(f"🌐 Admin URL: http://localhost:8000/admin")

        except Exception as e:
            logger.error(f"❌ Error creating superuser: {e}")
            # Возможно пользователь уже существует
            logger.debug("User might already exist. Try different credentials.")


if __name__ == "__main__":
    asyncio.run(create_superuser())
