import logging
from typing import Optional

from fastapi import HTTPException
from jira import JIRA

from src.models.parsed_task import ParsedTask
from src.repositories.meeting import MeetingRepository
from src.schemas.jira.jira_schemas import (
    CreateJiraTaskResponse,
    JiraTaskRequest,
    ProcessTaskResponseSchema,
)
from src.settings.config import settings
from src.utils.jira.parse_tasks_from_text import parse_tasks_from_text

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class JiraService:
    """Сервис для работы с Jira API."""

    def __init__(self, server_url: str, username: str, api_token: str):
        """Инициализация сервиса Jira."""
        self.jira = JIRA(server=server_url, basic_auth=(username, api_token))
        self.server_url = server_url
        self.meeting_repository = MeetingRepository("meetings")

    def _get_user_account_id(self, display_name: str) -> Optional[str]:
        """Получение account_id пользователя по имени (СИНХРОННЫЙ)."""
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

    def _get_available_projects(self) -> str:
        """Получение списка доступных проектов для вывода в ошибке (СИНХРОННЫЙ)."""
        try:
            projects = self.jira.projects()
            project_keys = [p.key for p in projects[:5]]  # Показываем первые 5
            return ", ".join(project_keys)
        except Exception as e:
            logger.error(f"Ошибка получения проектов: {str(e)}")
            return "не удалось получить список"

    def _check_project_exists(self, project_key: str) -> bool:
        """Проверка существования проекта (СИНХРОННЫЙ)."""
        try:
            self.jira.project(project_key)
            return True
        except Exception as e:
            logger.error(f"Проект {project_key} не найден: {str(e)}")
            return False

    def _check_epic_exists(self, epic_key: str) -> bool:
        """Проверка существования эпика (СИНХРОННЫЙ)."""
        try:
            issue = self.jira.issue(epic_key)
            # Проверяем, что это действительно эпик
            if issue.fields.issuetype.name.lower() in ['epic', 'эпик']:
                return True
            else:
                logger.warning(f"Задача {epic_key} существует, но это не эпик (тип: {issue.fields.issuetype.name})")
                return False
        except Exception as e:
            logger.error(f"Эпик {epic_key} не найден: {str(e)}")
            return False

    def create_jira_task(
            self, task: ParsedTask, project_key: str, epic_key: Optional[str] = None
    ) -> CreateJiraTaskResponse:
        """Создание задачи в Jira (СИНХРОННЫЙ метод)."""
        try:
            logger.info(f"Создание задачи: {task.task_id} - {task.title}")

            # Проверяем существование проекта (СИНХРОННО)
            if not self._check_project_exists(project_key):
                available_projects = self._get_available_projects()
                error_msg = f"Проект {project_key} не найден. Доступные проекты: {available_projects}"
                logger.error(error_msg)
                return CreateJiraTaskResponse(
                    status="error",
                    error=error_msg,
                )

            # Формируем описание задачи
            description_parts = [
                f"*Время выполнения:* {task.time_estimate}",
                "",
            ]

            # Добавляем описание если есть
            if hasattr(task, 'description') and task.description:
                description_parts.extend([f"*Описание:* {task.description}", ""])

            if task.acceptance_criteria:
                description_parts.extend(["*Критерии приемки:*", ""])
                for criteria in task.acceptance_criteria:
                    description_parts.append(f"* {criteria}")
                description_parts.append("")

            if task.dependencies:
                description_parts.extend(
                    [f"*Зависимости:* {', '.join(task.dependencies)}", ""]
                )

            description = "\n".join(description_parts)

            # Данные для создания задачи
            issue_dict = {
                "project": {"key": project_key},
                "summary": f"{task.task_id}: {task.title}",
                "description": description,
                "issuetype": {"name": "Task"},
            }

            # Привязываем к эпику если указан
            if epic_key and epic_key.strip():
                if self._check_epic_exists(epic_key):
                    try:
                        issue_dict["customfield_10014"] = epic_key
                        logger.info(f"Привязываем задачу к эпику {epic_key}")
                    except Exception as e:
                        logger.warning(f"Не удалось привязать к эпику через Epic Link: {str(e)}")
                        # Альтернативный способ - через parent
                        try:
                            issue_dict["parent"] = {"key": epic_key}
                        except Exception as e2:
                            logger.warning(f"Не удалось привязать к эпику через parent: {str(e2)}")
                else:
                    logger.warning(f"Эпик {epic_key} не найден, создаем задачу без привязки к эпику")

            logger.debug(f"Данные для создания задачи: {issue_dict}")

            # Создаем задачу
            new_issue = self.jira.create_issue(fields=issue_dict)

            success_url = f"{self.server_url}/browse/{new_issue.key}"
            logger.info(f"Задача успешно создана: {new_issue.key} - {success_url}")

            return CreateJiraTaskResponse(
                status="success",
                title=task.title,
                task_id=new_issue.key,
                url=success_url,
            )

        except Exception as e:
            error_msg = f"Ошибка при создании задачи '{task.title}': {str(e)}"
            logger.error(error_msg, exc_info=True)
            return CreateJiraTaskResponse(
                status="error",
                error=error_msg
            )

    async def process_tasks_to_jira(
            self, request: JiraTaskRequest
    ) -> ProcessTaskResponseSchema:
        """Основной метод для обработки текста и создания задач в Jira (АСИНХРОННЫЙ)."""
        try:
            logger.info(f"Начинаем обработку задач для проекта: {request.project_key}")
            logger.debug(f"Текст задач: {request.tasks_text[:200]}...")

            # Парсим задачи из текста (АСИНХРОННО)
            tasks = parse_tasks_from_text(request.tasks_text)

            logger.info(f"Распознано задач: {len(tasks) if tasks else 0}")

            if not tasks:
                error_msg = "Не удалось распознать задачи в тексте. Убедитесь, что текст содержит задачи в формате: '### TASK-001: Название задачи' или в виде нумерованного списка."
                logger.error(error_msg)
                return ProcessTaskResponseSchema(
                    status="error",
                    created_tasks=[],
                    error=True,
                    error_message=error_msg,
                )

            created_tasks = []
            errors = []

            # Создаем задачи в Jira
            tasks_to_process = tasks[:5]
            logger.info(f"Обрабатываем {len(tasks_to_process)} задач")

            for i, task in enumerate(tasks_to_process, 1):
                logger.info(f"Обработка задачи {i}/{len(tasks_to_process)}: {task.task_id}")

                result = self.create_jira_task(
                    task=task,
                    project_key=request.project_key,
                    epic_key=request.epic_key,
                )

                if result.status == "success":
                    # Добавляем информацию о созданной задаче
                    task_info = {
                        "key": result.task_id,
                        "title": result.title,
                        "url": result.url,
                        "summary": f"{result.task_id}: {result.title}"  # Для совместимости
                    }
                    created_tasks.append(task_info)
                    logger.info(f"Задача успешно создана: {result.task_id}")
                else:
                    error_info = {
                        "task_id": task.task_id,
                        "task_title": task.title,
                        "error": result.error
                    }
                    errors.append(error_info)
                    logger.error(f"Ошибка создания задачи {task.task_id}: {result.error}")

            # Определяем общий статус
            if created_tasks and not errors:
                status = "success"
                error_message = f"Все {len(created_tasks)} задач успешно созданы в Jira."
            elif created_tasks and errors:
                status = "partial_success"
                error_message = f"Создано {len(created_tasks)} задач, {len(errors)} ошибок."
            else:
                status = "error"
                error_message = "Ни одна задача не была создана в Jira."

            logger.info(f"Обработка завершена. Статус: {status}. Создано: {len(created_tasks)}, Ошибок: {len(errors)}")

            return ProcessTaskResponseSchema(
                status=status,
                created_tasks=created_tasks,
                errors=errors,  # Добавляем список ошибок
                error=bool(errors),
                error_message=error_message,
                success=len(created_tasks) > 0,  # Добавляем флаг успеха для клиента
            )

        except Exception as e:
            error_msg = f"Критическая ошибка при обработке задач: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return ProcessTaskResponseSchema(
                status="error",
                created_tasks=[],
                error=True,
                error_message=error_msg,
            )


async def get_jira_service() -> JiraService:
    """Создание экземпляра JiraService из переменных окружения."""
    server_url = settings.JIRA_SERVER_URL
    username = settings.JIRA_USERNAME
    api_token = settings.JIRA_API_TOKEN

    if not all([server_url, username, api_token]):
        error_msg = "Не настроены переменные окружения для Jira (JIRA_SERVER_URL, JIRA_USERNAME, JIRA_API_TOKEN)"
        logger.error(error_msg)
        raise HTTPException(
            status_code=500,
            detail=error_msg,
        )

    logger.info(f"Инициализация JiraService для сервера: {server_url}")
    return JiraService(server_url=server_url, username=username, api_token=api_token)