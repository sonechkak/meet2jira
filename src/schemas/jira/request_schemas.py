from pydantic import BaseModel


class ProcessAndCreateTasksRequest(BaseModel):
    tasks_text: str
    project_key: str = "LEARNJIRA"
    epic_key: str = None


class AcceptResultRequest(BaseModel):
    result_id: str
    tasks_text: str
    project_key: str = "LEARNJIRA"
    epic_key: str = None


class RejectResultRequest(BaseModel):
    result_id: str
    tasks_text: str
    reason: str = "Результат отклонен пользователем"
