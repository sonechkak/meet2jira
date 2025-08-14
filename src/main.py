import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from src.database import close_db_connection, create_db_and_tables
from src.schemas.main.root_schemas import RootResponseSchema
from src.settings.config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


from src.models.meeting import Meeting as MeetingModel

# Добавляем модели в globals()
from src.models.user import User as UserModel

globals().update(User=UserModel, Meeting=MeetingModel)
os.environ.update(
    ADMIN_USER_MODEL="User",
    ADMIN_USER_MODEL_USERNAME_FIELD="username",
    ADMIN_SECRET_KEY="secret-key-123",
)


async def run_migrations():
    """Запуск миграций программно"""
    try:
        from alembic import command
        from alembic.config import Config

        # Создаем конфиг Alembic
        alembic_cfg = Config("alembic.ini")

        # Применяем миграции
        command.upgrade(alembic_cfg, "head")
        logging.debug("Migrations applied successfully.")
        return True
    except Exception as e:
        logger.error("Failed to apply migrations: %s", e)
        return False


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator:
    """
    Runs events before application startup and after application shutdown.
    """
    logger.debug("Starting Meet2Jira App...")

    await create_db_and_tables()
    logger.debug("Database tables created/verified.")

    # # Initialize Name service
    # try:
    #     name_service = await get_name_service()
    #     if name_service.bot:
    #         logger.debug("Name initialized successfully")
    #     else:
    #         logger.debug("Name not initialized (token may be missing)")
    # except Exception as e:
    #     logger.error(f"Failed to initialize Name service: {e}")

    yield

    # Shutdown
    logger.debug("Shutting down Meet2Jira App...")

    await close_db_connection()
    logger.debug("Database connection closed.")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API for Meet2Jira, a tool to integrate meeting notes with Jira issues.",
    docs_url=settings.docs_url,
    redoc_url=settings.redoc_url,
    lifespan=lifespan,
)

# Подключение статических файлов
static_path = Path("static")
static_path.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


# CORS для фронтенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


UPLOAD_DIR = "static/img/uploaded_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.get("/", summary="Root Endpoint", tags=["Root"])
async def root() -> RootResponseSchema:
    """Root endpoint that returns basic information about the API."""
    db_status = await create_db_and_tables()
    raw_result = {
        "status": "success",
        "message": "Welcome to Meet2Jira API",
        "version": settings.app_version,
        "environment": settings.environment,
        "database_status": "connected" if db_status else "disconnected",
        "database_uri": settings.SQLALCHEMY_DATABASE_URI,
        "docs_url": settings.docs_url,
        "redoc_url": settings.redoc_url,
    }
    validated_result = RootResponseSchema.model_validate(raw_result)
    return validated_result


# Mount admin app
from fastadmin import fastapi_app as admin_app

# Include routers
from src.routers.auth import auth_router
from src.routers.file_processing import processing_router
from src.routers.meeting import meeting_router
from src.routers.utils import utils_router

# Mount the admin app
app.mount(settings.ADMIN_PREFIX, admin_app)

# Import admin
from src.admin.admin import MeetingAdmin, UserAdmin  # noqa: F401

# Include routers
app.include_router(auth_router, tags=["Authentication"])
app.include_router(processing_router, tags=["File Processing"])
app.include_router(utils_router, tags=["Utils"])
app.include_router(meeting_router, tags=["Meeting"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="127.0.0.1",
        port=8000,
        reload=settings.debug,
    )
