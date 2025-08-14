from typing import Any

from pydantic import BaseModel, Field


# Response Schemas
class ProcessingResponseSchema(BaseModel):
    status: str
    error: bool
    error_message: str | None = None
    model: str = "default_model"
    document_name: str
    summary: dict[str, Any] = Field(default_factory=dict)


class RejectProcessingResponseSchema(BaseModel):
    """Schema for the response when a file is rejected."""

    status: str = "success"
    error: bool = False
    error_message: str = None


class AcceptResultResponseSchema(BaseModel):
    """Schema for the response when a result is accepted."""

    status: str = "success"
    error: bool = False
    error_message: str = None
    message: str = None
    result_id: str = None
    tasks_text: str = None
    project_key: str = "MEET2JIRA"
    epic_key: str = None
    jira_result: dict = None


# Request Schemas
class RejectProcessingRequestSchema(BaseModel):
    """Schema for the request to reject a file."""

    success: bool
    message: str


class AcceptResultRequestSchema(BaseModel):
    result_id: str
    tasks_text: str
    project_key: str = "MEET2JIRA"
    epic_key: str = None


class RejectResultRequestSchema(BaseModel):
    result_id: str
    tasks_text: str
    reason: str = "Результат отклонен пользователем"
