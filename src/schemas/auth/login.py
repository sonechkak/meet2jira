from typing import Optional

from pydantic import BaseModel


class LoginRequestSchema(BaseModel):
    identifier: str
    password: str
    remember_me: bool = False
    captcha: str | None = None


class LoginResponseSchema(BaseModel):
    status: str
    id: int
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    is_active: bool
