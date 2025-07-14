from pydantic import BaseModel


class LoginRequestSchema(BaseModel):
    username: str
    password: str


class LoginResponseSchema(BaseModel):
    message: str
    user_id: int | None = None
    username: str | None = None
    email: str | None = None
