import logging

from src.pipeline.pipeline import process_document


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


async def handle_file_upload_event(data: dict):
    """Обработка события загрузки файла."""
    file_data = data.get("file")
    if not file_data:
        return {"error": "No file data provided."}

    if "content" in file_data and "name" in file_data:
        import base64
        from io import BytesIO

        try:
            # Декодируем base64
            file_content = base64.b64decode(file_data["content"])
            file_obj = BytesIO(file_content)

            # Создаем объект, похожий на UploadFile
            class WebhookFile:
                def __init__(self, content: bytes, filename: str):
                    self.file = BytesIO(content)
                    self.filename = filename
                    self.content_type = file_data.get("mime_type", "application/octet-stream")

                async def read(self):
                    return self.file.read()

                def seek(self, position):
                    return self.file.seek(position)

            webhook_file = WebhookFile(file_content, file_data["name"])
            pipeline_response = await process_document(webhook_file)

            return pipeline_response

        except Exception as e:
            logger.error(f"Error processing base64 file: {str(e)}")
            return {"error": f"Error processing file: {str(e)}"}
