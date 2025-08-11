import os
import sys

import pytest
from fastapi.testclient import TestClient

project_root = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, project_root)

from src.main import app


@pytest.fixture
def client():
    """Создает тестовый клиент для FastAPI."""
    return TestClient(app)
