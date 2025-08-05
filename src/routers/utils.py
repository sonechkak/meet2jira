import logging

from fastapi import APIRouter, Request, Depends

from src.schemas.debug.utils_schemas import JiraInfoResponseSchema, CreateSimpleTaskSchema
from src.services.jira_service import get_jira_service, JiraService
from src.settings.config import settings

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


utils_router = APIRouter(
    prefix="/utils",
    responses={404: {"description": "Not found"}},
)


@utils_router.get('/list_endpoints/')
def list_endpoints(request: Request):
    url_list = [
        {'path': route.path, 'name': route.name}
        for route in request.app.routes
    ]
    return url_list


@utils_router.get('/debug_jira_info/')
async def debug_jira_info() -> JiraInfoResponseSchema:
    """
    Отладочная информация о Jira
    """
    try:
        jira_service = get_jira_service()

        # Получаем информацию о пользователе
        current_user = jira_service.jira.current_user()

        # Получаем все проекты
        projects = jira_service.jira.projects()

        # Получаем типы задач для первого проекта (если есть)
        issue_types = []
        if projects:
            try:
                project_meta = jira_service.jira.createmeta(
                    projectKeys=projects[0].key,
                    expand="projects.issuetypes.fields"
                )
                if project_meta.get('projects'):
                    issue_types = [
                        it['name'] for it in project_meta['projects'][0].get('issuetypes', [])
                    ]
            except Exception as e:
                issue_types = [f"Ошибка получения типов: {str(e)}"]

        return JiraInfoResponseSchema(
            status="success",
            current_user=current_user.displayName,
            total_projects=len(projects),
            projects=[{"key": p.key, "name": p.name} for p in projects],
            sample_issue_types=issue_types,
            jira_server=settings.JIRA_SERVER_URL,
            project_key=settings.JIRA_DEFAULT_PROJECT_KEY,
            epic_key=settings.JIRA_EPIC_KEY,
            epic_name=settings.JIRA_EPIC_NAME,
            epic_url=settings.JIRA_EPIC_URL,
        )

    except Exception as e:
        return JiraInfoResponseSchema(
            status="error",
            error=True,
            error_message=str(e),
            current_user="Не удалось получить информацию",
            total_projects=0,
            projects=[],
            sample_issue_types=[],
            jira_server=settings.JIRA_SERVER_URL,
            project_key=settings.JIRA_DEFAULT_PROJECT_KEY,
            epic_key=settings.JIRA_EPIC_KEY,
            epic_name=settings.JIRA_EPIC_NAME,
            epic_url=settings.JIRA_EPIC_URL,
        )


@utils_router.post("/debug/create-simple-task")
async def create_simple_task(
        project_key: str = "LEARNJIRA",
        jira_service: JiraService = Depends(get_jira_service)
) -> CreateSimpleTaskSchema:
    """
    Создание простой тестовой задачи
    """

    try:
        issue_dict = {
            'project': {'key': project_key},
            'summary': 'Тестовая задача из API',
            'description': '*Приоритет:* High\n*Исполнитель:* Тестовый пользователь\n*Описание:* Это тестовая задача для проверки интеграции с Jira API',
            'issuetype': {'name': 'Task'}
        }

        logger.debug(f"Пытаемся создать задачу в проекте: {project_key}")
        logger.debug(f"Структура задачи: {issue_dict}")

        # Создаем задачу
        new_issue = jira_service.jira.create_issue(fields=issue_dict)

        return CreateSimpleTaskSchema(
            status="success",
            task_id=new_issue.key,
            url=settings.JIRA_EPIC_URL,
        )

    except Exception as e:
        return CreateSimpleTaskSchema(
            status="error",
            error=True,
            error_message=str(e)
        )
