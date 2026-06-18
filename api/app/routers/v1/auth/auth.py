"""
Authentication API routes.
"""

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.database import DatabaseSession
from app.repositories.users.user import UserRepository
from app.schemas.auth import RefreshRequest, TokenResponse
from app.schemas.users.user import UserResponse
from app.security.dependencies import CurrentActiveUser
from app.services.auth.auth import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])


def get_auth_service(db: DatabaseSession) -> AuthService:
    """Create and return an Auth service instance."""
    return AuthService(UserRepository(db))


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


@router.post("/login", response_model=TokenResponse)
def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    service: AuthServiceDep,
):
    """Authenticate with email + password and return a JWT access token.

    Uses the OAuth2 password form, so the ``username`` field carries the
    user's email.
    """
    return service.login(email=form_data.username, password=form_data.password)


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, service: AuthServiceDep):
    """Exchange a valid refresh token for a new access + refresh token pair."""
    return service.refresh(payload.refresh_token)


@router.get("/me", response_model=UserResponse)
def read_me(current_user: CurrentActiveUser):
    """Return the profile of the currently authenticated user."""
    return current_user
