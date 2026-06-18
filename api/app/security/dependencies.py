"""
Authentication dependencies.

Provides FastAPI dependencies that verify the bearer token and resolve the
current user. Shared across routers for protecting endpoints.
"""

from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.config import get_settings
from app.database import DatabaseSession
from app.models.users.user import User
from app.repositories.users.user import UserRepository
from app.security.jwt import ACCESS_TOKEN_TYPE, decode_token

ADMIN_ROLE_NAME = "Admin"

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{get_settings().api_v1_prefix.lstrip('/')}/auth/login"
)

_credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials.",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: DatabaseSession,
) -> User:
    """
    Decode the access token and return the authenticated user.

    Raises:
        HTTPException: 401 if the token is invalid, expired, not an access
            token, or the referenced user does not exist.
    """
    try:
        claims = decode_token(token)
    except jwt.PyJWTError as exc:
        raise _credentials_exception from exc

    if claims.get("type") != ACCESS_TOKEN_TYPE:
        raise _credentials_exception

    try:
        user_id = int(claims.get("sub"))
    except (TypeError, ValueError) as exc:
        raise _credentials_exception from exc

    user = UserRepository(db).get(user_id)

    if user is None:
        raise _credentials_exception

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_current_active_user(current_user: CurrentUser) -> User:
    """
    Ensure the authenticated user is active.

    Raises:
        HTTPException: 403 if the user account is inactive.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account.",
        )

    return current_user


CurrentActiveUser = Annotated[User, Depends(get_current_active_user)]


# ------------------------------------------------------
# Role-based access control
# ------------------------------------------------------


def _role_names(user: User) -> set[str]:
    """Return the set of role names assigned to the user."""
    return {user_role.role.name for user_role in user.user_roles}


def is_admin(user: User) -> bool:
    """Whether the user holds the Admin role (global access)."""
    return ADMIN_ROLE_NAME in _role_names(user)


def scoped_farm_ids(user: User) -> set[int] | None:
    """
    Return the farm ids the user is scoped to.

    Returns None for Admins, meaning unrestricted (global) access.
    """
    if is_admin(user):
        return None

    return {user_role.farm_id for user_role in user.user_roles if user_role.farm_id is not None}


def require_roles(*role_names: str):
    """
    Build a dependency that allows only users holding one of the given roles.

    Raises:
        HTTPException: 403 if the user has none of the required roles.
    """
    allowed = set(role_names)

    def checker(current_user: CurrentActiveUser) -> User:
        if not allowed & _role_names(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions.",
            )
        return current_user

    return checker


require_admin = require_roles(ADMIN_ROLE_NAME)
