from typing import Dict, Any
from pydantic import BaseModel


class LLMServiceResponseSchema(BaseModel):
    status: str = "success"
    error: bool = False
    error_message: str = None
    response_text: str = ""
    response_data: Dict[str, Any] = {}
    model_name: str = "model_name"
