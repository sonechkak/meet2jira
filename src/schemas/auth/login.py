
from pydantic import BaseModel


class LoginRequestSchema(BaseModel):
    identifier: str
    password: str
    remember_me: bool = False
    captcha: str | None = None


class LoginResponseSchema(BaseModel):
    status: str = "success"
    id: int = None
    username: str = None
    email: str | None = None
    full_name: str | None = None
    is_active: bool = True
    error: bool = False
    error_message: str | None = None
