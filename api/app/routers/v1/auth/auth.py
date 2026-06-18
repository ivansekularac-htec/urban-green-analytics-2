from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.database import DatabaseSession
from app.repositories.users.user import UserRepository
from app.schemas.auth.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.users.user import UserResponse
from app.services.auth.auth import AuthService
from app.services.users.user import UserService

router = APIRouter(prefix="/auth", tags=["Auth"])


def get_auth_service(db: DatabaseSession) -> AuthService:
    user_repository = UserRepository(db)
    user_service = UserService(user_repository)

    return AuthService(user_service)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


@router.post("/register", response_model=UserResponse)
def register(
    data: RegisterRequest,
    service: AuthServiceDep,
):
    return service.register(data)


@router.post("/login", response_model=TokenResponse)
def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    service: AuthServiceDep,
):
    return service.login(
        LoginRequest(
            email=form_data.username,
            password=form_data.password,
        )
    )
