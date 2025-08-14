import logging
import os
import sys
from pathlib import Path

import pytest
from dotenv import load_dotenv


@pytest.fixture(autouse=True)
def disable_logging():
    """Отключает логирование во время тестов."""
    logging.disable(logging.INFO)
    yield
    logging.disable(logging.NOTSET)


@pytest.fixture(autouse=True, scope="session")
def load_local_dev_env():
    """Загружает локальные переменные окружения из .env.local."""
    python_path = Path(__file__).resolve().parent.parent
    env_file = python_path.parent / ".env.local"
    sys.path.append(str(python_path))
    if env_file.exists() and env_file.is_file():
        load_dotenv(env_file)
        return True
    return False


@pytest.fixture(autouse=True)
def cleanup_after_test(tmp_path, monkeypatch):
    """Переключаемся во временную директорию для каждого теста."""
    original_cwd = os.getcwd()
    monkeypatch.chdir(tmp_path)
    yield
    # Возвращаемся в исходную директорию после теста
    os.chdir(original_cwd)


@pytest.fixture(autouse=True)
def jira_client():
    """
    Фикстура для использования клиента Jira в тестах.
    """
    from src.services.jira_service import JiraService

    jira_service = JiraService(
        server_url=os.getenv("JIRA_API_URL"),
        username=os.getenv("JIRA_API_USER"),
        api_token=os.getenv("JIRA_API_TOKEN"),
    )
    jira_client = jira_service._get_jira_client()
    yield jira_client
