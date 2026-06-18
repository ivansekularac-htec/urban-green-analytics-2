"""
auth.py
Authentication and authorization dependencies.
"""

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.users.user import User
from app.repositories.users.user import UserRepository
from app.security.password import decode_access_token

ADMIN_ROLE = "Admin"
FARM_MANAGER_ROLE = "Farm Manager"
OPERATIONS_ROLE = "Operations Team"

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
)

TokenDep = Annotated[str, Depends(oauth2_scheme)]
DbDep = Annotated[Session, Depends(get_db)]


def get_current_user(
    token: TokenDep,
    db: DbDep,
) -> User:
    """Return the authenticated user from a valid JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")

        if user_id is None:
            raise credentials_exception

    except JWTError as exc:
        raise credentials_exception from exc

    user_repository = UserRepository(db)
    user = user_repository.get(int(user_id))

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account.",
        )

    return user


def require_roles(
    *allowed_roles: str,
) -> Callable[[User], User]:
    """Require the current user to have at least one allowed role."""

    def role_checker(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        user_roles = {
            user_role.role.name
            for user_role in current_user.user_roles
            if user_role.role is not None
        }

        if ADMIN_ROLE in user_roles:
            return current_user

        if not user_roles.intersection(set(allowed_roles)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions.",
            )

        return current_user

    return role_checker


def user_has_role(
    user: User,
    role_name: str,
) -> bool:
    """Return whether user has the given role."""
    return any(
        user_role.role is not None and user_role.role.name == role_name
        for user_role in user.user_roles
    )


def user_has_farm_access(
    user: User,
    farm_id: int,
) -> bool:
    """Return whether user has access to a specific farm."""
    for user_role in user.user_roles:
        if user_role.role is None:
            continue

        if user_role.role.name == ADMIN_ROLE:
            return True

        if user_role.role.name == FARM_MANAGER_ROLE and user_role.farm_id == farm_id:
            return True

    return False


def require_farm_access(
    user: User,
    farm_id: int,
) -> None:
    """Raise 403 if user cannot access the given farm."""
    if not user_has_farm_access(user, farm_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions for this farm.",
        )


def get_managed_farm_ids(user: User) -> list[int]:
    """Return farm IDs managed by the user."""
    return [
        user_role.farm_id
        for user_role in user.user_roles
        if user_role.role is not None
        and user_role.role.name == FARM_MANAGER_ROLE
        and user_role.farm_id is not None
    ]


AdminUserDep = Annotated[
    User,
    Depends(require_roles(ADMIN_ROLE)),
]

FarmReadUserDep = Annotated[
    User,
    Depends(require_roles(ADMIN_ROLE, FARM_MANAGER_ROLE)),
]

SensorReadUserDep = Annotated[
    User,
    Depends(require_roles(ADMIN_ROLE, FARM_MANAGER_ROLE, OPERATIONS_ROLE)),
]

HarvestReadUserDep = Annotated[
    User,
    Depends(require_roles(ADMIN_ROLE, FARM_MANAGER_ROLE, OPERATIONS_ROLE)),
]

HarvestWriteUserDep = Annotated[
    User,
    Depends(require_roles(ADMIN_ROLE, OPERATIONS_ROLE)),
]

AuthenticatedUserDep = Annotated[
    User,
    Depends(get_current_user),
]
