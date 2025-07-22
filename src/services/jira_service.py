import logging
import os
import re
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

from fastapi import HTTPException
from jira import JIRA

from src.models.parsed_task import ParsedTask
from src.schemas.jira.jira_schemas import JiraTaskRequest, JiraTaskResponse
from src.utils.file_utils import parse_tasks_from_text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JiraService:
    """Сервис для работы с Jira API."""

    def __init__(self, server_url: str, username: str, api_token: str):
        """Инициализация сервиса Jira."""
        self.jira = JIRA(
            server=server_url,
            basic_auth=(username, api_token)
        )
        self.server_url = server_url

    # def _map_priority(self, priority: str) -> str:
    #     """Маппинг приоритетов на Jira приоритеты."""
    #
    #     priority_mapping = {
    #         'high': 'High',
    #         'medium': 'Medium',
    #         'low': 'Low',
    #         'critical': 'Highest',
    #         'highest': 'Highest',
    #         'lowest': 'Lowest'
    #     }
    #     return priority_mapping.get(priority.lower(), 'Medium')

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
            logger.error(f"Ошибка поиска пользователя {display_name}: {str(e)}")
            return None

    def create_jira_task(self, task: ParsedTask, project_key: str, epic_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Создание задачи в Jira
        """
        try:
            # Проверяем существование проекта
            try:
                project = self.jira.project(project_key)
            except Exception as e:
                return {
                    'success': False,
                    'error': f'Проект "{project_key}" не найден. Доступные проекты: {self._get_available_projects()}',
                    'title': task.title
                }

            # Формируем описание задачи
            description_parts = [
                # f"*Исполнитель:* {task.assignee}",
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

            # # Получаем account_id исполнителя
            # assignee_account_id = self._get_user_account_id(task.assignee)

            # Данные для создания задачи
            issue_dict = {
                'project': {'key': project_key},
                'summary': f"{task.task_id}: {task.title}",
                'description': description,
                'issuetype': {'name': 'Task'},
                # 'priority': {'name': self._map_priority(task.priority)},
            }

            # # Добавляем исполнителя если найден
            # if assignee_account_id:
            #     issue_dict['assignee'] = {'accountId': assignee_account_id}

            # Привязываем к эпику если указан
            if epic_key:
                try:
                    # Проверяем существование эпика
                    epic_issue = self.jira.issue(epic_key)
                    issue_dict['parent'] = {'key': epic_key}
                except Exception:
                    logger.error(f"Предупреждение: Эпик {epic_key} не найден, создаем задачу без привязки к эпику")

            # Создаем задачу
            new_issue = self.jira.create_issue(fields=issue_dict)

            return {
                'success': True,
                'key': new_issue.key,
                'url': f"{self.server_url}/browse/{new_issue.key}",
                'title': task.title
            }

        except Exception as e:
            error_msg = str(e)
            return {
                'success': False,
                'error': error_msg,
                'title': task.title
            }

    def _get_available_projects(self) -> str:
        """
        Получение списка доступных проектов для вывода в ошибке
        """
        try:
            projects = self.jira.projects()
            project_keys = [p.key for p in projects[:5]]  # Показываем первые 5
            return ', '.join(project_keys)
        except:
            return "не удалось получить список"

    async def process_tasks_to_jira(self, request: JiraTaskRequest) -> JiraTaskResponse:
        """
        Основной метод для обработки текста и создания задач в Jira
        """
        try:
            # Парсим задачи из текста
            tasks = parse_tasks_from_text(request.tasks_text)

            if not tasks:
                return JiraTaskResponse(
                    success=False,
                    created_tasks=[],
                    errors=["Не удалось найти задачи в тексте"]
                )

            created_tasks = []
            errors = []

            # Создаем задачи в Jira
            for task in tasks[:1]:  # Ограничиваем создание задач первыми 1
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

    if not all([server_url, username, api_token]):
        raise HTTPException(
            status_code=500,
            detail="Не настроены переменные окружения для Jira (JIRA_SERVER_URL, JIRA_USERNAME, JIRA_API_TOKEN)"
        )
    return JiraService(server_url, username, api_token)
