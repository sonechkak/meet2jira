import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from starlette.staticfiles import StaticFiles

from src.database import (
    create_db_and_tables,
    close_db_connection
)
from src.settings.config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Добавляем модели в globals()
from src.models.user import User as UserModel
from src.models.meeting import Meeting as MeetingModel

globals().update(User=UserModel, Meeting=MeetingModel)
os.environ.update(
    ADMIN_USER_MODEL="User",
    ADMIN_USER_MODEL_USERNAME_FIELD="username",
    ADMIN_SECRET_KEY="secret-key-123"
)


async def run_migrations():
    """Запуск миграций программно"""
    try:
        from alembic.config import Config
        from alembic import command

        # Создаем конфиг Alembic
        alembic_cfg = Config("alembic.ini")

        # Применяем миграции
        command.upgrade(alembic_cfg, "head")
        print("✅ Migrations applied successfully!")
        return True
    except Exception as e:
        print(f"⚠️  Warning: Could not run migrations: {e}")
        return False


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator:
    """
    Runs events before application startup and after application shutdown.
    """
    logger.info("Starting Meet2Jira App...")

    await create_db_and_tables()
    logger.info("Database tables created/verified.")

    # # Initialize Name service
    # try:
    #     name_service = await get_name_service()
    #     if name_service.bot:
    #         logger.info("Name initialized successfully")
    #     else:
    #         logger.warning("Name not initialized (token may be missing)")
    # except Exception as e:
    #     logger.error(f"Failed to initialize Name service: {e}")

    yield

    # Shutdown
    logger.info("Shutting down Meet2Jira App...")

    await close_db_connection()
    logger.info("Database connection closed.")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API for Meet2Jira, a tool to integrate meeting notes with Jira issues.",
    docs_url=settings.docs_url if settings.is_development else None,
    redoc_url=settings.redoc_url if settings.is_development else None,
    lifespan=lifespan,
)

# Подключение статических файлов
try:
    app.mount("/static", StaticFiles(directory="backend/static"), name="static")
except RuntimeError:
    # Папка не существует, создадим при первом запуске
    import os
    os.makedirs("backend/static/images", exist_ok=True)
    app.mount("/static", StaticFiles(directory="backend/static"), name="static")


@app.get("/", summary="Root Endpoint", tags=["Root"])
async def root():
    db_status = await create_db_and_tables()
    return {
        "message": "Welcome to the Meet2Jira API!",
        "version": settings.app_version,
        "environment": settings.environment,
        "database_status": "connected" if db_status else "disconnected",
        "database_uri": settings.SQLALCHEMY_DATABASE_URI,
        "docs_url": settings.docs_url,
        "redoc_url": settings.redoc_url,
        "api_prefix": settings.api_prefix,
    }

# Import admin
import src.admin.admin

# Include routers
from src.routers.auth import auth_router
from src.routers.file_processing import processing_router
from src.routers.utils import utils_router

# Mount admin app
from fastadmin import fastapi_app as admin_app

# Mount the admin app
app.mount(settings.ADMIN_PREFIX, admin_app)


# Include routers
app.include_router(auth_router, tags=["Authentication"])
app.include_router(processing_router, tags=["File Processing"])
app.include_router(utils_router, tags=["Utils"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="127.0.0.1",
        port=8000,
        reload=settings.debug,
    )
