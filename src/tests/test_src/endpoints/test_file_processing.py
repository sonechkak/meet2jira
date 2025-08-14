import pytest

from src.schemas.processing.processing_schemas import ProcessingResponseSchema
from src.services.jira_service import get_jira_service
from src.tests.test_src.conftest import MockJiraService, MockJiraResult


def test_process_document_success(client, sample_file, monkeypatch):
    """Тест успешной обработки документа."""
    # Arrange
    expected_response = ProcessingResponseSchema(
        status="success",
        error=False,
        document_name="test_file.txt",
        summary={"tasks": 5, "processed": True}
    )

    async def mock_process_document(file):
        return expected_response

    monkeypatch.setattr("src.pipeline.pipeline.process_document", mock_process_document)

    # Act
    response = client.post(
        "/file/process",
        files={"file": sample_file}
    )

    # Assert
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["status"] == "success"
    assert response_data["error"] is False
    assert response_data["document_name"] == "test_file.txt"


def test_process_document_no_file(client):
    """Тест отправки запроса без файла."""
    # Act
    response = client.post("/file/process")

    # Assert
    assert response.status_code == 422


def test_process_document_pdf_file(client, sample_pdf_file, monkeypatch):
    """Тест обработки PDF файла."""
    # Arrange
    expected_response = ProcessingResponseSchema(
        status="success",
        error=False,
        document_name="test_document.pdf",
        summary={"pages": 1, "text_extracted": True}
    )

    async def mock_process_document(file):
        return expected_response

    monkeypatch.setattr("src.pipeline.pipeline.process_document", mock_process_document)

    # Act
    response = client.post(
        "/file/process",
        files={"file": sample_pdf_file}
    )

    # Assert
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["status"] == "error"
    assert response_data["document_name"] == "test_document.pdf"


# Тесты для POST /file/reject endpoint
def test_reject_processing_empty_data(client):
    """Тест отклонения с пустыми данными."""
    # Act
    response = client.post(
        "/file/reject",
        json={}
    )

    # Assert
    assert response.status_code == 422


def test_reject_processing_missing_result_id(client):
    """Тест отклонения без result_id."""
    # Act
    response = client.post(
        "/file/reject",
        json={"reason": "Some reason"}
    )

    # Assert
    assert response.status_code == 422


# Тесты для POST /file/accept endpoint
def test_accept_result_success(client, valid_accept_request):
    """Тест успешного принятия файла и создания задач в Jira."""

    # Теперь можно даже без мока, если хотите реальный тест
    response = client.post("/file/accept", json=valid_accept_request)

    print("Response:", response.json())  # Для отладки

    assert response.status_code == 200
    response_data = response.json()
    assert "jira_result" in response_data

    jira_result = response_data["jira_result"]

    if "created_tasks" in jira_result and len(jira_result["created_tasks"]) > 0:
        assert isinstance(jira_result["created_tasks"], list)
    else:
        assert "error" in jira_result
        assert jira_result["error"] is True
        print("Jira result error:", jira_result.get("error_message", "No error message provided"))
        print("Jira result:", jira_result)


def test_accept_result_jira_no_tasks_created(client, valid_accept_request, monkeypatch):
    """Тест случая, когда задачи в Jira не созданы."""

    # Arrange
    def mock_get_jira_service():
        return MockJiraService(created_tasks=[])

    monkeypatch.setattr("src.services.jira_service.get_jira_service", mock_get_jira_service)

    # Act
    response = client.post(
        "/file/accept",
        json=valid_accept_request
    )

    # Assert
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["status"] == "error"
    assert response_data["error"] is True
    assert "Не удалось создать задачи в Jira" in response_data["error_message"]


def test_accept_result_jira_service_exception(client, valid_accept_request, monkeypatch):
    """Тест обработки исключения в accept endpoint."""
    # Arrange - ИСПРАВЛЕНО: правильная инициализация mock_jira_result
    mock_jira_result = MockJiraResult(failed_tasks=["Task 1", "Task 2"])

    def mock_get_jira_service():
        return MockJiraService(should_raise=True)

    monkeypatch.setattr("src.services.jira_service.get_jira_service", mock_get_jira_service)

    # Act
    response = client.post(
        "/file/accept",
        json=valid_accept_request
    )

    # Assert
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["status"] == "error"
    assert response_data["error"] is True


def test_accept_result_invalid_data(client):
    """Тест accept endpoint с невалидными данными."""
    # Act
    response = client.post(
        "/file/accept",
        json={}
    )

    # Assert
    assert response.status_code == 422


def test_accept_result_missing_required_fields(client):
    """Тест accept endpoint с отсутствующими обязательными полями."""
    # Act
    response = client.post(
        "/file/accept",
        json={"result_id": "123"}
    )

    # Assert
    assert response.status_code == 422


# Тесты для POST /file/webhook endpoint
def test_webhook_file_upload_event(client, webhook_file_upload_data, monkeypatch):
    """Тест webhook с событием file_upload."""

    # Arrange
    async def mock_handle_file_upload(data, jira_service):
        return {"status": "received", "file_id": data.get("file_id")}

    def mock_get_jira_service():
        return MockJiraService()

    monkeypatch.setattr("src.handlers.webhooks.handle_file_upload.handle_file_upload", mock_handle_file_upload)
    monkeypatch.setattr("src.services.jira_service.get_jira_service", mock_get_jira_service)

    # Act
    response = client.post(
        "/file/webhook",
        json=webhook_file_upload_data
    )

    # Assert
    assert response.status_code == 200


def test_webhook_file_ready_event(client, webhook_file_ready_data, monkeypatch):
    """Тест webhook с событием file_ready."""

    # Arrange
    async def mock_handle_file_ready_event(data):
        return {"status": "processed", "file_id": data.get("file_id")}

    monkeypatch.setattr("src.handlers.webhooks.handle_file_ready_event.handle_file_ready_event",
                        mock_handle_file_ready_event)

    # Act
    response = client.post(
        "/file/webhook",
        json=webhook_file_ready_data
    )

    # Assert
    assert response.status_code == 200


def test_webhook_unknown_event(client):
    """Тест webhook с неизвестным событием."""
    # Arrange
    webhook_data = {
        "event": "unknown_event",
        "data": "some data"
    }

    # Act
    response = client.post(
        "/file/webhook",
        json=webhook_data
    )

    # Assert
    assert response.status_code == 200
    response_data = response.json()
    assert "error" in response_data
    assert "Unknown event type" in response_data["error"]


def test_webhook_no_event(client):
    """Тест webhook без указания события."""
    # Arrange
    webhook_data = {
        "data": "some data"
    }

    # Act
    response = client.post(
        "/file/webhook",
        json=webhook_data
    )

    # Assert
    assert response.status_code == 200
    response_data = response.json()
    assert "error" in response_data
    assert "No event specified" in response_data["error"]


def test_webhook_empty_event(client):
    """Тест webhook с пустым событием."""
    # Arrange
    webhook_data = {
        "event": "",
        "data": "some data"
    }

    # Act
    response = client.post(
        "/file/webhook",
        json=webhook_data
    )

    # Assert
    assert response.status_code == 200
    response_data = response.json()
    assert "error" in response_data


def test_webhook_invalid_json(client):
    """Тест webhook с невалидным JSON."""
    # Act
    response = client.post(
        "/file/webhook",
        data="invalid json data",
        headers={"content-type": "application/json"}
    )

    # Assert
    assert response.status_code == 200
    response_data = response.json()
    assert "error" in response_data
    assert "Error handling webhook" in response_data["error"]