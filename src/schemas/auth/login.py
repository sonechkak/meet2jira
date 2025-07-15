from pydantic import BaseModel


class LoginRequestSchema(BaseModel):
    identifier: str
    password: str
    remember_me: bool = False
    captcha: str | None = None

class LoginResponseSchema(BaseModel):
    message: str
    user_id: int | None = None
    username: str | None = None
    email: str | None = None
