import sys
import pytest
import logging
import shutil
import tempfile

from pathlib import Path
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


@pytest.fixture
def temp_media_root(settings):
    """Фикстура для временной медиа-папки."""
    tmpdir = tempfile.mkdtemp()
    settings.MEDIA_ROOT = tmpdir
    yield tmpdir
    shutil.rmtree(tmpdir, ignore_errors=True)
