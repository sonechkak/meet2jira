from pydantic import BaseModel

# Response Schemas
class ProcessingResponseSchema(BaseModel):
    """Schema for the response of a processing operation."""
    success: bool
    model: str
    document_name: str
    summary: dict
    error: bool = False

class RejectProcessingResponseSchema(BaseModel):
    """Schema for the response when a file is rejected."""
    success: bool
    message: str


# Request Schemas

class RejectProcessingRequestSchema(BaseModel):
    """Schema for the request to reject a file."""
    success: bool
    message: str


class AcceptResultRequestSchema(BaseModel):
    result_id: str
    tasks_text: str
    project_key: str = "LEARNJIRA"
    epic_key: str = None


class RejectResultRequestSchema(BaseModel):
    result_id: str
    tasks_text: str
    reason: str = "Результат отклонен пользователем"

