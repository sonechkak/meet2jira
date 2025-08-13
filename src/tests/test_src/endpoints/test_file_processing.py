import aifc  # noqa
import pytest

from io import BytesIO
from sqlalchemy import text

from src.database import get_db_session


@pytest.mark.asyncio
async def test_db_connection():
    """Тест подключения к БД"""
    try:
        async with get_db_session() as session:
            result = await session.execute(text("SELECT 1 as test_value"))
            assert result is not None
            print("✅ Database connection test passed")
    except Exception as e:
        pytest.fail(f"Database connection failed: {e}")



def test_file_processing_endpoint_with_mocker(client, mocker):
    # Mock the file processing function
    mock_process_document = mocker.patch('src.routers.file_processing.process_document')
    mock_response = {
        "status": "success",
        "error": False,
        "error_message": None,
        "document_name": "test_file.txt",
        "summary": {},
        "model": "test-model"
    }
    mock_process_document.return_value = mock_response

    # Simulate a file upload request using BytesIO
    file_content = BytesIO(b"This is a test file content")
    response = client.post(
        '/file/process',
        files={'file': file_content},
    )

    # Assert the response status code and content
    assert response.status_code == 200
    result = response.json()

    assert result['status'] == 'success'
    assert result['error'] == False  # noqa: E712
    assert result['document_name'] == 'test_file.txt'

    # Verify that the file processing function was called once
    mock_process_document.assert_called_once()
