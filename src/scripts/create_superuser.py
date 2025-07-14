import asyncio
import sys
from pathlib import Path

from src.database import AsyncSessionLocal
from src.models.user import User

# Добавляем корень проекта в Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
print(f"Project root added to sys.path: {project_root}")

from src.settings.config import settings
from src.database import get_db_session
from sqlalchemy import select
import bcrypt


async def create_superuser():
    """Создание суперпользователя"""

    print("🔐 Creating superuser for FastAdmin...")

    # Данные по умолчанию
    username = "admin"
    email = "admin@meet2jira.com"
    password = "admin123"
    full_name = "Administrator"

    print(f"Creating user: {username} / {email}")

    # Хешируем пароль
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    async with AsyncSessionLocal() as session:
        try:
            # Создаем нового суперпользователя
            superuser = User(
                username=username,
                email=email,
                full_name=full_name,
                hashed_password=hashed_password,
                is_superuser=True,
                is_active=True,
                is_verified=True,
                is_staff=True,
                is_admin=True,
            )

            session.add(superuser)
            await session.commit()

            print(f"✅ Superuser '{username}' created successfully!")
            print(f"📧 Email: {email}")
            print(f"🔑 Password: {password}")
            print(f"🌐 Admin URL: http://localhost:8000/admin")

        except Exception as e:
            print(f"❌ Error creating superuser: {e}")
            # Возможно пользователь уже существует
            print("User might already exist. Try different credentials.")


if __name__ == "__main__":
    asyncio.run(create_superuser())
