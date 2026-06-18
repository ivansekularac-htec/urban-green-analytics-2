"""
auth.py
Authentication endpoints.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.database import DatabaseSession
from app.dependencies.auth import AdminUserDep
from app.schemas.auth import RegisterRequest, Token
from app.services.auth_service import AuthService

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

OAuth2FormDep = Annotated[OAuth2PasswordRequestForm, Depends()]


@router.post(
    "/register",
    response_model=Token,
    status_code=status.HTTP_201_CREATED,
)
def register(
    register_data: RegisterRequest,
    db: DatabaseSession,
    current_user: AdminUserDep,
) -> Token:
    """Register a new user."""
    auth_service = AuthService(db)

    return auth_service.register_user(register_data)


@router.post(
    "/login",
    response_model=Token,
)
def login(
    form_data: OAuth2FormDep,
    db: DatabaseSession,
) -> Token:
    """Authenticate a user."""
    auth_service = AuthService(db)

    return auth_service.login_user(
        email=form_data.username,
        password=form_data.password,
    )
