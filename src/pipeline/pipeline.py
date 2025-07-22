import logging
import os
import tempfile
from typing import Dict

from fastapi import File

from .elements.base import Pipeline
from src.services.llm_service import LlmService
from src.tools.document_classify import DocumentClassifier
from src.tools.prompt_generator import PromptGenerator
from src.utils.file_utils import extract_text_from_file


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def process_document(file: File,
                           model: str = "llama3.2",
                           base_url: str = "http://localhost:11434") -> Dict[str, str]:
    """Функция для создания резюме документа с использованием Pipeline."""

    # Сохраняем файл временно
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_file_path = tmp_file.name

    try:
        # 1. Извлекаем текст из файла
        text = extract_text_from_file(tmp_file_path, file.content_type)

        if not text.strip():
            return {
                "error": "Не удалось извлечь текст из файла",
                "document_type": "unknown",
                "summary": "",
                "success": False
            }

        # 2. Классифицируем документ
        document_classifier = DocumentClassifier(document_content=text)
        document_type = document_classifier.run()

        prompt_generator = PromptGenerator(document_type=document_type, text=text)
        prompt = prompt_generator.run()

        # Создаем Pipeline с LlmService
        pipeline = Pipeline(
            model=model,
            tools=[],
            elements=[
                LlmService(prompt=prompt),
            ]
        )
        # Запускаем pipeline
        summary = pipeline.run()

        if summary:
            return {
                "summary": summary,
                "document_type": document_type,
                "document_name": file.filename,
                "success": True
            }
        else:
            return {
                "error": summary or "Не удалось получить ответ от модели",
                "document_type": pipeline.document_type or "unknown",
                "success": False
            }

    except Exception as e:
        logger.error(f"Ошибка при обработке документа: {str(e)}")
        return {
            "error": f"Ошибка при обработке документа: {str(e)}",
            "document_type": "unknown",
            "success": False
        }

    finally:
        # Удаляем временный файл
        os.unlink(tmp_file_path)
