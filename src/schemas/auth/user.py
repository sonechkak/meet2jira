
from pydantic import BaseModel


class UserCreateSchema(BaseModel):
    username: str
    password: str
    email: str | None = None
    full_name: str | None = None


class UserUpdateSchema(BaseModel):
    username: str | None = None
    email: str | None = None
    full_name: str | None = None
    password: str | None = None


class UserResponseSchema(BaseModel):
    status: str = "success"
    id: int = None
    username: str = None
    email: str | None = None
    full_name: str | None = None
    is_active: bool = True
    error: bool = False
    error_message: str | None = None
