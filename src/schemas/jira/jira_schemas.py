from typing import List, Optional, Dict

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
    project_key: str = "LEARNJIRA"
    epic_key: Optional[str] = None


class JiraTaskResponse(BaseModel):
    success: bool
    created_tasks: List[Dict[str, str]]
    errors: List[str]