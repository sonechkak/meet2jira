import logging
import re
from typing import List

from src.models.parsed_task import ParsedTask
from src.utils.jira.parse_single_task import parse_single_task

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def parse_tasks_from_text(text: str) -> List[ParsedTask]:
    """Parse multiple tasks from a text string."""
    tasks = []

    # Split the text into blocks based on the TASK-xxx pattern
    task_blocks = re.split(r"### TASK-\d+:", text)

    for i, block in enumerate(
        task_blocks[1:], 1
    ):  # Missing the first block as it doesn't start with TASK-xxx
        try:
            task = parse_single_task(f"TASK-{i:03d}", block.strip())
            if task:
                tasks.append(task)
        except Exception as e:
            logger.error(f"Ошибка парсинга задачи {i}: {str(e)}")
            continue

    return tasks
