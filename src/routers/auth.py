from fastapi import APIRouter
from fastapi.params import Depends
from src.dependencies.auth import get_auth_repository, get_auth_service
from src.repositories.auth import AuthRepository
from src.schemas.auth.login import LoginRequestSchema, LoginResponseSchema
from src.schemas.auth.user import UserCreateSchema, UserResponseSchema
from src.services.auth_service import AuthService

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


@auth_router.post("/login")
async def login(
    request: LoginRequestSchema, auth_service: AuthService = Depends(get_auth_service)
) -> LoginResponseSchema:
    """Login endpoint for user authentication."""

    try:
        user = await auth_service.login(
            identifier=request.identifier,
            password=request.password,
            remember_me=request.remember_me,
            captcha=request.captcha,
        )

        if not user:
            return LoginResponseSchema(
                status="error",
                error=True,
                error_message="Invalid credentials or user not found.",
            )

        return LoginResponseSchema(
            status="success",
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
        )

    except Exception as e:
        return LoginResponseSchema(
            status="error", error=True, error_message=f"Login failed: {str(e)}"
        )


@auth_router.post("/register")
async def register(
    user_data: UserCreateSchema,
    user_repository: AuthRepository = Depends(get_auth_repository),
) -> UserResponseSchema:
    """Register endpoint for new users."""
    try:
        if user_data.username:
            existing_user = await user_repository.get_user_by_username(
                user_data.username
            )
            if existing_user:
                return UserResponseSchema(
                    status="error", error=True, error_message="Username already exists."
                )

        if user_data.email:
            existing_user = await user_repository.get_user_by_email(user_data.email)
            if existing_user:
                return UserResponseSchema(
                    status="error", error=True, error_message="Email already exists."
                )

        new_user = await user_repository.create(obj_in=user_data)

        return UserResponseSchema(
            id=new_user.id,
            username=new_user.username,
            email=new_user.email,
            full_name=new_user.full_name,
            is_active=new_user.is_active,
        )

    except Exception as e:
        return UserResponseSchema(
            status="error", error=True, error_message=f"Registration failed: {str(e)}"
        )
