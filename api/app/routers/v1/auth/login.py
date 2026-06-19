"""
Authentication routes — login and current user.

Login uses the OAuth2 password flow so FastAPI's docs page wires up an
``Authorize`` button for free; subsequent requests pass the bearer
token in the ``Authorization`` header.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy import select

from app.database import DatabaseSession
from app.models.users.user import User
from app.schemas.users.user import UserResponse
from app.security.dependencies import CurrentUser
from app.security.jwt import create_access_token
from app.security.password import verify_password

router = APIRouter(prefix="/auth", tags=["Auth"])


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/login", response_model=TokenResponse)
def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: DatabaseSession):
    """Exchange email + password for a JWT access token.

    The OAuth2 form uses ``username`` for the email — that's the spec, not
    a typo. We return the same generic 401 for unknown email, wrong
    password, or inactive account so attackers can't enumerate users.
    """
    user = db.scalars(select(User).where(User.email == form_data.username)).one_or_none()

    if (
        user is None
        or not user.is_active
        or not verify_password(form_data.password, user.password_hash)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return TokenResponse(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserResponse)
def me(user: CurrentUser):
    """Return the currently authenticated user."""
    return user
