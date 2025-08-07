import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent.parent
env_path = BASE_DIR / ".env.local"

load_dotenv(dotenv_path=env_path)


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Application
    app_name: str = Field(default="Meet2Jira", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    environment: str = Field(
        default="development", description="Environment (development/production)"
    )
    debug: bool = Field(default=True, description="Debug mode")
    secret_key: str = Field("super-key", description="Secret key for JWT tokens")

    # Database
    SQLALCHEMY_DATABASE_URI: str = Field(
        default="postgresql+asyncpg://meet2jira_user:meet2jira_password@127.0.0.1:5432/meet2jira",
        description="Database connection URI PostgreSQL",
    )
    SQLALCHEMY_ECHO: bool = Field(
        default=True, description="Enable SQLAlchemy echo for debugging"
    )

    # FastAPI
    api_prefix: str = Field(default="/api", description="API prefix")
    docs_url: str = Field(default="/docs", description="Swagger docs URL")
    redoc_url: str = Field(default="/redoc", description="ReDoc URL")

    # File Upload
    max_file_size: int = Field(
        default=10485760, description="Max file size in bytes (10MB)"
    )
    upload_dir: str = Field(
        default="./backend/static/images", description="Upload directory"
    )

    # Logging
    log_level: str = Field(default="DEBUG", description="Logging level")
    log_format: str = Field(default="json", description="Log format (json/text)")

    # Admin Fastadmin
    ADMIN_PREFIX: str = "/admin"
    ADMIN_SITE_NAME: str = "FastAdmin"
    ADMIN_SITE_FAVICON: str = "/admin/static/images/favicon.png"
    ADMIN_PRIMARY_COLOR: str = "#009485"
    ADMIN_SESSION_ID_KEY: str = "admin_session_id"
    ADMIN_SESSION_EXPIRED_AT: int = 144000
    ADMIN_DATE_FORMAT: str = "YYYY-MM-DD"
    ADMIN_DATETIME_FORMAT: str = "YYYY-MM-DD HH:mm"
    ADMIN_TIME_FORMAT: str = "HH:mm:ss"
    ADMIN_USER_MODEL: str = "src.models.user.User"
    ADMIN_USER_MODEL_USERNAME_FIELD: str = "username"
    ADMIN_SECRET_KEY: str = "ADMIN_SECRET_KEY"
    ADMIN_DISABLE_CROP_IMAGE: bool = False

    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379/0", description="Redis URL")

    # JIRA settings
    JIRA_SERVER_URL: str = Field(
        default=str(os.getenv("JIRA_API_URL")), description="Jira server URL"
    )
    JIRA_USERNAME: str = Field(
        default=str(os.getenv("JIRA_API_USER")), description="Jira username"
    )
    JIRA_API_TOKEN: str = Field(
        default=str(os.getenv("JIRA_API_TOKEN")), description="Jira API token"
    )
    JIRA_DEFAULT_PROJECT_KEY: str = Field(
        default=str(os.getenv("JIRA_DEFAULT_PROJECT_KEY")),
        description="Default Jira project key",
    )
    JIRA_EPIC_KEY: str = Field(
        default=str(os.getenv("JIRA_EPIC_KEY", "EPIC-1")), description="Jira epic key"
    )
    JIRA_EPIC_NAME: str = Field(
        default=str(os.getenv("JIRA_EPIC_NAME", "Epic Name")),
        description="Name for Jira epic",
    )
    JIRA_EPIC_URL: str = Field(
        default=str(
            os.getenv(
                "JIRA_EPIC_URL",
                f"{JIRA_SERVER_URL}/browse/{os.getenv('JIRA_EPIC_KEY', 'EPIC-1')}",
            )
        ),
        description="URL for Jira epic",
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Если URI не задан, строим его автоматически
        if not self.SQLALCHEMY_DATABASE_URI:
            self.SQLALCHEMY_DATABASE_URI = "postgresql+asyncpg://meet2jira_user:meet2jira_password@127.0.0.1:5432/meet2jira"

    @property
    def allowed_extensions(self) -> list[str]:
        """List of allowed file extensions for uploads."""
        return ["jpg", "jpeg", ".png", "gif", ".pdf"]

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return str(self.environment).lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return str(self.environment).lower() == "development"

    model_config = {
        "env_file": ".env.local" if environment == "local" else ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
        "validate_assignment": False,
    }


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings instance."""
    return settings
