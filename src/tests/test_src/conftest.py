import os
import sys
from io import BytesIO

import pytest
from fastapi.testclient import TestClient

project_root = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, project_root)

from src.main import app


@pytest.fixture
def client():
    """Создает тестовый клиент для FastAPI."""
    return TestClient(app)


@pytest.fixture
def sample_file():
    """Создает тестовый файл для загрузки."""
    file_content = b"Test file content for processing"
    return ("test_file.txt", BytesIO(file_content), "text/plain")


@pytest.fixture
def sample_pdf_file():
    """Создает тестовый PDF файл."""
    pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n"
    return ("test_document.pdf", BytesIO(pdf_content), "application/pdf")


@pytest.fixture
def valid_accept_request():
    """Валидные данные для accept endpoint."""
    return {
        "result_id": "result_12345",
        "tasks_text": "Задача 1: Разработать API\nЗадача 2: Написать тесты\nЗадача 3: Создать документацию",
        "project_key": "MYPROJ",
        "epic_key": "MYPROJ-100"
    }


@pytest.fixture
def valid_reject_request():
    """Валидные данные для reject endpoint."""
    return {
        "result_id": "result_12345",
        "reason": "Неверная обработка документа"
    }


@pytest.fixture
def webhook_file_upload_data():
    """Данные webhook для события загрузки файла."""
    return {
        "event": "file_upload",
        "file_id": "upload_123",
        "file_name": "important_document.pdf",
        "file_size": 1024000,
        "upload_time": "2024-01-15T10:30:00Z",
        "user_id": "user_456"
    }


@pytest.fixture
def sample_pdf_file():
    """Создает тестовый PDF файл."""
    pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n"
    return ("test_document.pdf", BytesIO(pdf_content), "application/pdf")


@pytest.fixture
def valid_accept_request():
    """Валидные данные для accept endpoint."""
    return {
        "result_id": "result_12345",
        "tasks_text": "Задача 1: Разработать API\nЗадача 2: Написать тесты\nЗадача 3: Создать документацию",
        "project_key": "MYPROJ",
        "epic_key": "MYPROJ-100"
    }


@pytest.fixture
def webhook_file_ready_data():
    """Данные webhook для события готовности файла."""
    return {
        "event": "file_ready",
        "file_id": "upload_123",
        "processing_status": "completed",
        "result_url": "https://example.com/results/upload_123",
        "processing_time": "2024-01-15T10:35:00Z"
    }


class MockJiraResult:
    """Мок для результата Jira операции."""

    def __init__(self, created_tasks=None, failed_tasks=None):
        self.created_tasks = created_tasks or []
        self.failed_tasks = failed_tasks or []

    def dict(self):
        return {
            "created_tasks": self.created_tasks,
            "failed_tasks": self.failed_tasks,
            "success_count": len(self.created_tasks),
            "error_count": len(self.failed_tasks)
        }


class MockJiraService:
    """Мок для JiraService."""

    def __init__(self, should_succeed=True, created_tasks=None, should_raise=False):
        self.should_succeed = should_succeed
        self.should_raise = should_raise

        if created_tasks is not None:
            self.created_tasks = created_tasks
        else:
            self.created_tasks = ["MYPROJ-101", "MYPROJ-102", "MYPROJ-103"] if should_succeed else []

    async def process_tasks_to_jira(self, request):
        if self.should_raise:
            raise Exception("Jira connection failed")

        if self.should_succeed and self.created_tasks:
            return MockJiraResult(created_tasks=self.created_tasks)
        else:
            return MockJiraResult(failed_tasks=["Task 1", "Task 2", "Task 3"])
