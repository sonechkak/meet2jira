from pydantic import BaseModel


class JiraInfoResponseSchema(BaseModel):
    status: str = "success"
    error: bool = False
    error_message: str = None
    project_key: str = "MEET2JIRA"
    current_user: str = None
    total_projects: int = 0
    projects: list = []
    sample_issue_types: list = []
    jira_server: str = None
    epic_key: str = None
    epic_name: str = None
    epic_url: str = None


class CreateSimpleTaskSchema(BaseModel):
    status: str = "success"
    error: bool = False
    error_message: str = None
    task_id: str = None
    url: str = None
