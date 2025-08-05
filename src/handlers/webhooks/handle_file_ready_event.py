import logging
from io import BytesIO

import aiohttp

from src.pipeline.pipeline import process_document

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


async def handle_file_ready_event(data: dict):
    """Обработка события готовности файла (по ссылке)."""
    file_data = data.get("file")
    if not file_data or "download_url" not in file_data:
        return {"error": "No download URL provided."}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(file_data["download_url"]) as response:
                if response.status == 200:
                    file_content = await response.read()

                    class WebhookFile:
                        def __init__(self, content: bytes, filename: str):
                            self.file = BytesIO(content)
                            self.filename = filename
                            self.content_type = response.headers.get("content-type", "application/octet-stream")

                        async def read(self):
                            return self.file.read()

                        def seek(self, position):
                            return self.file.seek(position)

                    webhook_file = WebhookFile(file_content, file_data["name"])
                    pipeline_response = await process_document(webhook_file)

                    return pipeline_response
                else:
                    return {"error": f"Failed to download file: {response.status}"}

    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        return {"error": f"Error downloading file: {str(e)}"}
