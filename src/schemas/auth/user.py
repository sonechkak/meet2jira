from typing import Optional

from pydantic import BaseModel


class UserCreateSchema(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    full_name: Optional[str] = None


class UserUpdateSchema(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None


class UserResponseSchema(BaseModel):
    status: str = "success"
    id: int = None
    username: str = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    is_active: bool = True
    error: bool = False
    error_message: Optional[str] = None
