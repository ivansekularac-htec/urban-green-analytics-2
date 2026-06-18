from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.database import DatabaseSession
from app.repositories.users.user import UserRepository
from app.schemas.auth.auth import LoginRequest, RefreshRequest, TokenResponse
from app.schemas.users.user import UserResponse
from app.security.dependencies import CurrentUserDep
from app.services.auth.auth import AuthService
from app.services.users.user import UserService

router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_auth_service(db: DatabaseSession) -> AuthService:
    user_repository = UserRepository(db)
    return AuthService(user_repository, UserService(user_repository))


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


@router.post("/login", response_model=TokenResponse)
def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    service: AuthServiceDep,
):
    return service.login(LoginRequest(email=form_data.username, password=form_data.password))


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, service: AuthServiceDep):
    return service.refresh(payload.refresh_token)


@router.get("/me", response_model=UserResponse)
def me(current_user: CurrentUserDep):
    """Return the currently authenticated user."""
    return current_user
