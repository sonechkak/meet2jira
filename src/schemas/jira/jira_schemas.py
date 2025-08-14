from typing import Dict, List, Optional

from pydantic import BaseModel


class TaskData(BaseModel):
    task_id: str
    title: str
    priority: str
    assignee: str
    time_estimate: str
    description: str
    acceptance_criteria: List[str]
    dependencies: List[str]


class JiraTaskRequest(BaseModel):
    tasks_text: str
    project_key: str = "MEET2JIRA"
    epic_key: Optional[str] = None
    options: Optional[Dict[str, str]] = None


class ProcessTaskResponseSchema(BaseModel):
    status: str = "success"
    created_tasks: List[Dict[str, str]] = []
    error: bool = False
    error_message: str = ""


class CreateJiraTaskResponse(BaseModel):
    status: str = "success"
    error: Optional[str] = None
    title: Optional[str] = None
    task_id: Optional[str] = None
    url: Optional[str] = None
