from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.database import DatabaseSession
from app.repositories.users.user import UserRepository
from app.schemas.auth import TokenResponse
from app.schemas.users.user import UserResponse
from app.security.dependencies import CurrentUserDep
from app.services.auth import AuthService


def get_auth_service(
    db: DatabaseSession,
) -> AuthService:
    return AuthService(
        UserRepository(db),
    )


AuthServiceDep = Annotated[
    AuthService,
    Depends(get_auth_service),
]

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    form_data: Annotated[
        OAuth2PasswordRequestForm,
        Depends(),
    ],
    service: AuthServiceDep,
):
    return TokenResponse(
        access_token=service.login(
            email=form_data.username,
            password=form_data.password,
        ),
    )


@router.get(
    "/me",
    response_model=UserResponse,
)
def me(
    current_user: CurrentUserDep,
):
    return current_user
