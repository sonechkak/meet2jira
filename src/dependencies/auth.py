from fastapi import Depends
from src.database import AsyncSessionLocal, get_async_session
from src.repositories.auth import AuthRepository
from src.services.auth_service import AuthService


def get_auth_repository(session: AsyncSessionLocal = Depends(get_async_session)):
    return AuthRepository(session)


def get_auth_service(auth_repo: AuthRepository = Depends(get_auth_repository)):
    return AuthService(auth_repo)
