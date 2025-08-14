import logging
import re
from typing import List

from src.models.parsed_task import ParsedTask
from src.utils.jira.parse_single_task import parse_single_task

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def parse_tasks_from_text(text: str) -> List[ParsedTask]:
    """Parse multiple tasks from a text string."""

    if not text or not text.strip():
        logger.warning("Пустой текст для парсинга задач")
        return []

    tasks = []

    # Разделяем текст на блоки задач по шаблону
    task_pattern = r"### ([A-Z]+-\d+):\s*(.*?)(?=### [A-Z]+-\d+:|$)"
    matches = re.findall(task_pattern, text, re.DOTALL | re.MULTILINE)

    if not matches:
        # Если не найдено совпадений по шаблону, пробуем нумерованный список
        logger.debug("Паттерн ### не найден, пробуем нумерованный список")
        numbered_pattern = r"^\d+\.\s*(.+)$"
        numbered_matches = re.findall(numbered_pattern, text, re.MULTILINE)

        for i, task_text in enumerate(numbered_matches, 1):
            try:
                task = parse_single_task(f"TASK-{i:03d}", task_text.strip())
                if task:
                    tasks.append(task)
            except Exception as e:
                logger.error(f"Ошибка парсинга задачи {i}: {str(e)}")
                continue
    else:
        # Если найдены совпадения по шаблону, обрабатываем их
        for task_key, task_content in matches:
            try:
                # Очищаем контент и извлекаем только заголовок
                cleaned_content = clean_task_content(task_content)

                task = parse_single_task(task_key, cleaned_content)
                if task:
                    tasks.append(task)
            except Exception as e:
                logger.error(f"Ошибка парсинга задачи {task_key}: {str(e)}")
                continue

            logger.info(f"Успешно распарсено {len(tasks)} задач")
            return tasks

def clean_task_content(content: str) -> str:
    """Очистка контента задачи от лишней информации."""

    # Убираем переводы строк и лишние пробелы
    content = content.strip()

    # Если контент содержит **Приоритет:** или другие метки, берем только первую строку
    lines = content.split('\n')
    if lines:
        first_line = lines[0].strip()

        # Убираем **Приоритет:** и подобные метки из первой строки
        title = re.sub(r'\*\*[^*]+\*\*.*', '', first_line).strip()

        if title:
            return title

    return content[:100].replace('\n', ' ').strip()
