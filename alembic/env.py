import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool
from src.database import Base

config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import models

target_metadata = Base.metadata


def get_url():
    url = os.getenv(
        "SQLALCHEMY_DATABASE_URI",
        "postgresql+asyncpg://meet2jira_user:meet2jira_password@127.0.0.1:5432/meet2jira",
    )
    if url and "+asyncpg" in url:
        url = url.replace("+asyncpg", "+psycopg2")
    return url


def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode."""
    url = get_url()
    if not url:
        raise ValueError("SQLALCHEMY_DATABASE_URI not found")

    connectable = create_engine(url, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
