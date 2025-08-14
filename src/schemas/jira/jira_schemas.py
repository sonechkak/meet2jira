
from pydantic import BaseModel


class TaskData(BaseModel):
    task_id: str
    title: str
    priority: str
    assignee: str
    time_estimate: str
    description: str
    acceptance_criteria: list[str]
    dependencies: list[str]


class JiraTaskRequest(BaseModel):
    tasks_text: str
    project_key: str = "MEET2JIRA"
    epic_key: str | None = None
    options: dict[str, str] | None = None


class ProcessTaskResponseSchema(BaseModel):
    status: str = "success"
    created_tasks: list[dict[str, str]] = []
    error: bool = False
    error_message: str = ""


class CreateJiraTaskResponse(BaseModel):
    status: str = "success"
    error: str | None = None
    title: str | None = None
    task_id: str | None = None
    url: str | None = None
