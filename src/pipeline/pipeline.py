import datetime
import json
import logging
import os
import tempfile

from fastapi import File

from src.schemas.processing.processing_schemas import ProcessingResponseSchema
from src.services.llm_service import LlmService
from src.tools.prompt_generator import PromptGenerator
from src.utils.files.text.extract_text_from_file import extract_text_from_file
from src.database import AsyncSessionLocal, get_db_session

from src.repositories.meeting import MeetingRepository
from src.schemas.model.meeting import MeetingCreateSchema
from src.services.meeting_service import MeetingService
from .elements.base import Pipeline

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


async def process_document(
    file: File, model: str = "yandex-gpt"
) -> ProcessingResponseSchema:
    """Функция для обработки документа с использованием Pipeline."""
    # Сохраняем файл временно
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_file_path = tmp_file.name

    try:
        # 1. Извлекаем текст из файла
        text = extract_text_from_file(tmp_file_path, file.content_type)
        if not text.strip():
            return ProcessingResponseSchema(
                status="error",
                error=True,
                error_message="Extracted text is empty",
                model=model,
                document_name=file.filename,
                summary={},
            )

        # Сохраняем извлеченный текст в БД
        meeting_data = {
            "title": f"Обработка файла {file.filename}",
            "file_name": file.filename,
            "description": f"Обработка файла {file.filename} с помощью модели {model}",
            "meeting_date": datetime.datetime.now(),
        }
        meeting_schema = MeetingCreateSchema(**meeting_data)

        logger.info(f"Создание записи встречи с данными: {meeting_schema}")

        try:
            async with get_db_session() as session:
                meeting_repo = MeetingRepository(session)
                meeting_service = MeetingService(meeting_repo)

                # Создаем запись встречи в БД
                created_meeting = await meeting_service.create_meeting(meeting_schema)
                logger.info(f"Создана запись встречи: {created_meeting}")

        except Exception as e:
            logger.error(f"Ошибка при создании записи встречи: {str(e)}")
            return ProcessingResponseSchema(
                status="error",
                error=True,
                error_message=f"Failed to create meeting record: {str(e)}",
                model=model,
                document_name=file.filename,
                summary={},
            )

        # 2. Генерируем промпт для LLM
        logger.info(f"Генерация промпта для модели {model} с текстом длиной {len(text)} символов")
        prompt_generator = PromptGenerator(text=text)
        prompt = prompt_generator.run()

        # 3. Создаем Pipeline с LlmService и запускаем его
        pipeline = Pipeline(
            model=model,
            tools=[],
            elements=[
                LlmService(prompt=prompt),
            ],
        )

        raw_result = pipeline.run()
        if raw_result and created_meeting:
            logger.info("Pipeline успешно выполнен.")
            async with get_db_session() as session:
                meeting_repo = MeetingRepository(session)
                meeting_service_update = MeetingService(meeting_repo)

                await meeting_service_update.update_meeting(
                    meeting_id=created_meeting.id,
                    meeting_data={
                        "status": "processed",
                        "summary": raw_result.get("results", []),
                    },
                )
                logger.info("Запись в БД успешно обновлена")
        else:
            logger.error("Pipeline вернул пустой результат.")

        summary_data = {
            "summary": "",
            "content": "",
            "key_points": [],
            "action_items": [],
        }

        llm_response_text = None
        if raw_result and isinstance(raw_result, dict):
            results = raw_result.get("results", [])
            if results and len(results) > 0:
                first_result = results[0]
                if isinstance(first_result, dict):
                    llm_response_text = first_result.get("response_text")

        if llm_response_text:
            logger.info(
                f"Получен ответ от LLM длиной: {len(llm_response_text)} символов"
            )
            logger.debug(f"LLM response_text: {llm_response_text[:200]}...")

            try:
                # Попытка парсинга как JSON
                parsed = json.loads(llm_response_text)
                summary_data.update(
                    {
                        "summary": parsed.get("summary", ""),
                        "content": parsed.get("content", parsed.get("text", "")),
                        "key_points": parsed.get("key_points", []),
                        "action_items": parsed.get("action_items", []),
                    }
                )
                logger.info("LLM ответ успешно распарсен как JSON")
            except json.JSONDecodeError as e:
                logger.warning(f"LLM ответ не является JSON: {e}")
                # Если не JSON, используем как есть
                summary_data.update(
                    {
                        "summary": llm_response_text[:500]
                        + ("..." if len(llm_response_text) > 500 else ""),
                        "content": llm_response_text,
                        "key_points": [],
                        "action_items": [],
                    }
                )
        else:
            logger.error("Не удалось извлечь response_text из результата LLM")

        logger.info(
            f"Финальные данные: summary={len(summary_data.get('summary', ''))}, content={len(summary_data.get('content', ''))}"
        )

        return ProcessingResponseSchema(
            status="success",
            error=False,
            model=model,
            document_name=file.filename,
            summary=summary_data,
        )

    except Exception as e:
        logger.error(f"Ошибка при обработке документа: {str(e)}")
        return ProcessingResponseSchema(
            status="error",
            error=True,
            error_message=str(e),
            model=model,
            document_name=file.filename,
            summary={"error": str(e)},
        )

    finally:
        # Удаляем временный файл
        os.unlink(tmp_file_path)
