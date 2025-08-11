import aifc  # noqa
from io import BytesIO


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
