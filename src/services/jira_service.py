import os
import re
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

from fastapi import HTTPException
from jira import JIRA

from src.schemas.jira.jira_schemas import JiraTaskRequest, JiraTaskResponse


@dataclass
class ParsedTask:
    task_id: str
    title: str
    priority: str
    assignee: str
    time_estimate: str
    description: str
    acceptance_criteria: List[str]
    dependencies: List[str]


class JiraService:
    """Сервис для работы с Jira API."""

    def __init__(self, server_url: str, username: str, api_token: str):
        """Инициализация сервиса Jira."""
        try:
            self.jira = JIRA(
                server=server_url,
                basic_auth=(username, api_token)
            )
            self.server_url = server_url
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка подключения к Jira: {str(e)}"
            )

    def parse_tasks_from_text(self, text: str) -> List[ParsedTask]:
        """Парсинг задач из текста."""
        tasks = []

        # Разделяем текст на блоки задач
        task_blocks = re.split(r'### TASK-\d+:', text)

        for i, block in enumerate(task_blocks[1:], 1):  # Пропускаем первый пустой блок
            try:
                task = self._parse_single_task(f"TASK-{i:03d}", block.strip())
                if task:
                    tasks.append(task)
            except Exception as e:
                print(f"Ошибка парсинга задачи {i}: {str(e)}")
                continue

        return tasks

    def _parse_single_task(self, task_prefix: str, block: str) -> Optional[ParsedTask]:
        """
        Парсинг одной задачи из текстового блока.
        """
        try:
            # Извлекаем заголовок
            title_match = re.search(r'^([^\n]+)', block)
            title = title_match.group(1).strip() if title_match else "Без названия"

            # Извлекаем приоритет
            priority_match = re.search(r'\*\*Приоритет:\*\*\s*(\w+)', block)
            priority = priority_match.group(1) if priority_match else "Medium"

            # Извлекаем исполнителя
            assignee_match = re.search(r'\*\*Исполнитель:\*\*\s*([^(]+)', block)
            assignee = assignee_match.group(1).strip() if assignee_match else "Не назначен"

            # Извлекаем время выполнения
            time_match = re.search(r'\*\*Время выполнения:\*\*\s*([^\n]+)', block)
            time_estimate = time_match.group(1).strip() if time_match else "Не указано"

            # Извлекаем описание
            desc_match = re.search(r'\*\*Описание:\*\*\s*([^*]+)', block)
            description = desc_match.group(1).strip() if desc_match else "Описание отсутствует"

            # Извлекаем критерии приемки
            criteria_section = re.search(r'\*\*Acceptance Criteria:\*\*\s*(.*?)\*\*Зависимости:', block, re.DOTALL)
            acceptance_criteria = []
            if criteria_section:
                criteria_text = criteria_section.group(1)
                # Ищем строки, начинающиеся с "-"
                criteria_lines = re.findall(r'^\s*-\s*(.+)$', criteria_text, re.MULTILINE)
                acceptance_criteria = [line.strip() for line in criteria_lines]

            # Извлекаем зависимости
            deps_match = re.search(r'\*\*Зависимости:\*\*\s*([^\n]+)', block)
            dependencies_text = deps_match.group(1).strip() if deps_match else "Нет"

            dependencies = []
            if dependencies_text and dependencies_text.lower() != "нет":
                # Парсим зависимости как список TASK-xxx
                deps = re.findall(r'TASK-\d+', dependencies_text)
                dependencies = deps

            return ParsedTask(
                task_id=f"{task_prefix}",
                title=title,
                priority=priority,
                assignee=assignee,
                time_estimate=time_estimate,
                description=description,
                acceptance_criteria=acceptance_criteria,
                dependencies=dependencies
            )

        except Exception as e:
            print(f"Ошибка парсинга задачи: {str(e)}")
            return None

    def _map_priority(self, priority: str) -> str:
        """Маппинг приоритетов на Jira приоритеты."""
        priority_mapping = {
            'high': 'High',
            'medium': 'Medium',
            'low': 'Low',
            'critical': 'Highest',
            'highest': 'Highest',
            'lowest': 'Lowest'
        }
        return priority_mapping.get(priority.lower(), 'Medium')

    def _get_user_account_id(self, display_name: str) -> Optional[str]:
        """Получение account_id пользователя по имени."""
        try:
            # Поиск пользователей по имени
            users = self.jira.search_users(display_name)

            if users:
                return users[0].accountId

            # Если не найден по имени, попробуем найти по email
            users = self.jira.search_users(display_name + "@")
            if users:
                return users[0].accountId

            return None
        except Exception as e:
            print(f"Ошибка поиска пользователя {display_name}: {str(e)}")
            return None

    def create_jira_task(self, task: ParsedTask, project_key: str, epic_key: Optional[str] = None) -> Dict[str, Any]:
        """Создание задачи в Jira."""
        try:
            # Формируем описание задачи
            description_parts = [
                f"*Исполнитель:* {task.assignee}",
                f"*Время выполнения:* {task.time_estimate}",
                f"*Описание:* {task.description}",
                ""
            ]

            if task.acceptance_criteria:
                description_parts.extend([
                    "*Критерии приемки:*",
                    ""
                ])
                for criteria in task.acceptance_criteria:
                    description_parts.append(f"* {criteria}")
                description_parts.append("")

            if task.dependencies:
                description_parts.extend([
                    f"*Зависимости:* {', '.join(task.dependencies)}",
                    ""
                ])

            description = "\n".join(description_parts)

            # Получаем account_id исполнителя
            assignee_account_id = self._get_user_account_id(task.assignee)

            # Данные для создания задачи
            issue_dict = {
                'project': {'key': project_key},
                'summary': f"{task.task_id}: {task.title}",
                'description': description,
                'issuetype': {'name': 'Task'},
                'priority': {'name': self._map_priority(task.priority)},
            }

            # Добавляем исполнителя если найден
            if assignee_account_id:
                issue_dict['assignee'] = {'accountId': assignee_account_id}

            # Привязываем к эпику если указан
            if epic_key:
                issue_dict['parent'] = {'key': epic_key}

            # Создаем задачу
            new_issue = self.jira.create_issue(fields=issue_dict)

            return {
                'success': True,
                'key': new_issue.key,
                'url': f"{self.server_url}/browse/{new_issue.key}",
                'title': task.title
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'title': task.title
            }

    async def process_tasks_to_jira(self, request: JiraTaskRequest) -> JiraTaskResponse:
        """Основной метод для обработки текста и создания задач в Jira."""
        try:
            tasks = self.parse_tasks_from_text(request.tasks_text)

            if not tasks:
                return JiraTaskResponse(
                    success=False,
                    created_tasks=[],
                    errors=["Не удалось найти задачи в тексте"]
                )

            created_tasks = []
            errors = []

            # Создаем задачи в Jira
            for task in tasks:
                result = self.create_jira_task(
                    task=task,
                    project_key=request.project_key,
                    epic_key=request.epic_key
                )

                if result['success']:
                    created_tasks.append({
                        'key': result['key'],
                        'url': result['url'],
                        'title': result['title']
                    })
                else:
                    errors.append(f"Задача '{result['title']}': {result['error']}")

            return JiraTaskResponse(
                success=len(created_tasks) > 0,
                created_tasks=created_tasks,
                errors=errors
            )

        except Exception as e:
            return JiraTaskResponse(
                success=False,
                created_tasks=[],
                errors=[f"Общая ошибка: {str(e)}"]
            )


def get_jira_service() -> JiraService:
    """Создание экземпляра JiraService из переменных окружения."""

    server_url = os.getenv('JIRA_SERVER_URL', 'https://sonyakarm.atlassian.net')
    username = os.getenv('JIRA_USERNAME', 'sonyakarm@icloud.com')
    api_token = os.getenv('JIRA_API_TOKEN', "ATATT3xFfGF0W4kLpVYxmT2rwIuB4rAJB0DmPYFfugK36k8Z3iboSEBAgrbeat6rkntLxj_2GVpINs0rpndjtyzjNrMd61JQdpI8kNfEpc-8eEWqTwMuFgmImTPTh-HkUDHKY2u1PQ18KoTCsJ8HBcCmvv4sb4D29lrkrRcVIAaeaSdYxId94XI=1A1937E5")
    print(server_url, username, api_token)

    if not all([server_url, username, api_token]):
        raise HTTPException(
            status_code=500,
            detail="Не настроены переменные окружения для Jira (JIRA_SERVER_URL, JIRA_USERNAME, JIRA_API_TOKEN)"
        )
    return JiraService(server_url, username, api_token)
