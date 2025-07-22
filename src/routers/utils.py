import logging
import os

from fastapi import APIRouter, Request, Depends

from src.services.jira_service import get_jira_service, JiraService

logging.basicConfig(level=logging.INFO)
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
async def debug_jira_info():
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

        return {
            "success": True,
            "current_user": current_user,
            "total_projects": len(projects),
            "projects": [
                {
                    "key": p.key,
                    "name": p.name,
                    "id": p.id,
                    "projectTypeKey": getattr(p, 'projectTypeKey', 'unknown')
                }
                for p in projects
            ],
            "sample_issue_types": issue_types,
            "jira_server": os.getenv('JIRA_API_URL')
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "jira_server": os.getenv('JIRA_API_URL'),
            "username": os.getenv("JIRA_API_USER")
        }


@utils_router.post("/debug/create-simple-task")
async def create_simple_task(
        project_key: str = "LEARNJIRA",
        jira_service: JiraService = Depends(get_jira_service)
):
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

        logger.info(f"Пытаемся создать задачу в проекте: {project_key}")
        logger.info(f"Структура задачи: {issue_dict}")

        # Создаем задачу
        new_issue = jira_service.jira.create_issue(fields=issue_dict)

        return {
            "success": True,
            "key": new_issue.key,
            "url": f"{jira_service.server_url}/browse/{new_issue.key}",
            "message": "Тестовая задача создана успешно!",
            "summary": issue_dict['summary']
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "project_key": project_key,
            "attempted_structure": issue_dict
        }
