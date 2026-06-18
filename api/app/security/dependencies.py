"""
Authentication dependencies.
"""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError

from app.database import DatabaseSession
from app.models.users.user import User
from app.repositories.users.user import UserRepository
from app.security.jwt import decode_token

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
)

TokenDep = Annotated[
    str,
    Depends(oauth2_scheme),
]


def get_current_user(
    db: DatabaseSession,
    token: TokenDep,
):
    """
    Resolve the currently authenticated user.
    """
    try:
        payload = decode_token(token)
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        ) from None

    user_id = payload.get("user_id")

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )

    user = UserRepository(db).get_with_roles(user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive",
        )

    return user


CurrentUserDep = Annotated[
    User,
    Depends(get_current_user),
]
