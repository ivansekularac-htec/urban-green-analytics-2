"""
Authentication API routes.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models.users.user import User
from app.models.users.user_roles import UserRole
from app.schemas.auth.token import TokenResponse
from app.security.jwt import create_access_token
from app.security.password import verify_password

router = APIRouter(tags=["Auth"])


@router.post("/login", response_model=TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> TokenResponse:
    """
    Authenticate user and return JWT access token.

    The OAuth2 username field is used as the user's email address.
    """
    statement = (
        select(User)
        .where(User.email == form_data.username)
        .options(
            selectinload(User.user_roles).selectinload(UserRole.role),
        )
    )

    user = db.scalar(statement)

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    roles = [user_role.role.name for user_role in user.user_roles]

    farm_ids = [user_role.farm_id for user_role in user.user_roles if user_role.farm_id is not None]

    access_token = create_access_token(
        {
            "sub": str(user.id),
            "email": user.email,
            "roles": roles,
            "farm_ids": farm_ids,
        }
    )

    return TokenResponse(access_token=access_token)
