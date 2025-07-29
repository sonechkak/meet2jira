from pydantic import BaseModel


class RootResponseSchema(BaseModel):
    status: str = "success"
    message: str = None
    error: bool = False
    error_message: str = None
    version: str = None
    environment: str = None
    database_status: str = None
    database_uri: str = None
    docs_url: str = None
    redoc_url: str = None