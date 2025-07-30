import logging

from src.pipeline.pipeline import process_document
from src.schemas.jira.jira_schemas import JiraTaskRequest
from src.services.jira_service import JiraService

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


async def handle_file_upload(data: dict, jira_service: JiraService):
    """Обработка файла через веб-хук с автоматическим созданием задач в Jira."""

    file_data = data.get("file")
    if not file_data:
        return {"error": "No file data provided."}

    try:
        # 1. Обрабатываем файл (ваша существующая логика)
        webhook_file = await create_webhook_file_object(file_data)
        pipeline_response = await process_document(webhook_file)

        logger.info(f"Pipeline response: {pipeline_response}")

        # 2. Проверяем успешность обработки
        if pipeline_response.status == "success" and not pipeline_response.error:

            # 3. Извлекаем текст задач из ответа pipeline
            tasks_text = extract_tasks_from_summary(pipeline_response.summary)

            if tasks_text:
                # 4. Получаем параметры Jira из веб-хука или используем дефолтные
                project_key = data.get("project_key", "LEARNJIRA")
                epic_key = data.get("epic_key")

                logger.info(f"Creating Jira tasks for project: {project_key}")
                logger.info(f"Tasks text length: {len(tasks_text)} characters")

                # 5. Создаем задачи в Jira
                jira_request = JiraTaskRequest(
                    tasks_text=tasks_text,
                    project_key=project_key,
                    epic_key=epic_key
                )

                jira_result = await jira_service.process_tasks_to_jira(jira_request)
                logger.info(f"Jira creation result: {jira_result}")

                # 6. Возвращаем комбинированный результат
                if jira_result.created_tasks:
                    return {
                        "status": "success",
                        "message": "File processed and Jira tasks created successfully",
                        "pipeline_result": pipeline_response.dict(),
                        "jira_result": {
                            "created_tasks": jira_result.created_tasks,
                            "project_key": project_key,
                            "epic_key": epic_key,
                            "tasks_count": len(jira_result.created_tasks)
                        }
                    }
                else:
                    return {
                        "status": "partial_success",
                        "message": "File processed but failed to create Jira tasks",
                        "pipeline_result": pipeline_response.dict(),
                        "jira_error": jira_result.dict()
                    }
            else:
                logger.warning("No tasks extracted from pipeline response")
                return {
                    "status": "partial_success",
                    "message": "File processed but no tasks found for Jira creation",
                    "pipeline_result": pipeline_response.dict(),
                    "debug_summary": pipeline_response.summary
                }
        else:
            logger.error("Pipeline processing failed")
            return {
                "status": "error",
                "message": "Pipeline processing failed",
                "pipeline_result": pipeline_response.dict()
            }

    except Exception as e:
        logger.error(f"Error in webhook file processing: {str(e)}")
        return {
            "status": "error",
            "message": f"Processing failed: {str(e)}",
            "error_details": str(e)
        }


def extract_tasks_from_summary(summary: dict) -> str:
    """Извлекает текст задач из summary."""
    if not summary:
        return ""

    # Проверяем разные возможные поля с задачами
    if "content" in summary and summary["content"]:
        return summary["content"]

    if "summary" in summary and summary["summary"]:
        return summary["summary"]

    # Если есть другие поля, добавьте их сюда
    logger.warning(f"Could not extract tasks from summary keys: {list(summary.keys())}")
    return ""


async def create_webhook_file_object(file_data: dict):
    """Создает файловый объект из данных веб-хука."""
    from io import BytesIO
    import base64

    if "content" in file_data:
        # Декодируем base64
        try:
            file_content = base64.b64decode(file_data["content"])
        except Exception as e:
            raise ValueError(f"Invalid base64 content: {e}")
    else:
        raise ValueError("No file content provided")

    class WebhookFile:
        def __init__(self, content: bytes, filename: str):
            self.file = BytesIO(content)
            self.filename = filename
            self.content_type = file_data.get("mime_type", "text/plain")

        async def read(self):
            return self.file.read()

        def seek(self, position):
            return self.file.seek(position)

    return WebhookFile(file_content, file_data["name"])