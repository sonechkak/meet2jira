import logging
import re
from typing import Optional

from src.models.parsed_task import ParsedTask

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def parse_single_task(task_prefix: str, block: str) -> Optional[ParsedTask]:
    """Parse a single task from a text block."""

    try:
        # Extracting the task ID
        title_match = re.search(r"^([^\n]+)", block)
        origin_title = title_match.group(1).strip() if title_match else "Без названия"

        title_words = origin_title.split()[
            :5
        ]  # Ограничиваем заголовок первыми 5 словами
        short_title = " ".join(title_words)
        if len(short_title) > 100:  # Ограничиваем длину заголовка до 80 символов
            title = short_title[:77] + "..."
        else:
            title = short_title

        # # Извлекаем приоритет
        # priority_match = re.search(r'\*\*Приоритет:\*\*\s*(\w+)', block)
        # priority = priority_match.group(1) if priority_match else "Medium"

        # # Извлекаем исполнителя
        # assignee_match = re.search(r'\*\*Исполнитель:\*\*\s*([^(]+)', block)
        # assignee = assignee_match.group(1).strip() if assignee_match else "Не назначен"

        # Извлекаем время выполнения
        time_match = re.search(r"\*\*Время выполнения:\*\*\s*([^\n]+)", block)
        time_estimate = time_match.group(1).strip() if time_match else "Не указано"

        # Извлекаем описание
        desc_match = re.search(r"\*\*Описание:\*\*\s*([^*]+)", block)
        description = (
            desc_match.group(1).strip() if desc_match else "Описание отсутствует"
        )

        # Извлекаем критерии приемки
        criteria_section = re.search(
            r"\*\*Acceptance Criteria:\*\*\s*(.*?)\*\*Зависимости:", block, re.DOTALL
        )
        acceptance_criteria = []
        if criteria_section:
            criteria_text = criteria_section.group(1)
            # Ищем строки, начинающиеся с "-"
            criteria_lines = re.findall(r"^\s*-\s*(.+)$", criteria_text, re.MULTILINE)
            acceptance_criteria = [line.strip() for line in criteria_lines]

        # Извлекаем зависимости
        deps_match = re.search(r"\*\*Зависимости:\*\*\s*([^\n]+)", block)
        dependencies_text = deps_match.group(1).strip() if deps_match else "Нет"

        dependencies = []
        if dependencies_text and dependencies_text.lower() != "нет":
            # Парсим зависимости как список TASK-xxx
            deps = re.findall(r"TASK-\d+", dependencies_text)
            dependencies = deps

        return ParsedTask(
            task_id=f"{task_prefix}",
            title=title,
            # priority=priority,
            # assignee=assignee,
            time_estimate=time_estimate,
            description=description,
            acceptance_criteria=acceptance_criteria,
            dependencies=dependencies,
        )

    except Exception as e:
        logger.error(f"Ошибка парсинга задачи: {str(e)}")
        return None
