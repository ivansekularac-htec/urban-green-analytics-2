from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

from app.config import get_settings
from app.database import DatabaseSession
from app.models.users.user import User
from app.repositories.users.user import UserRepository
from app.security.jwt import decode_token

settings = get_settings()

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.api_v1_prefix}/auth/login",
)


def get_current_user(
    db: DatabaseSession,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> User:
    try:
        payload = decode_token(token)
    except Exception as err:
        raise HTTPException(status_code=401, detail="Unauthorized") from err

    user_id = payload.get("sub")

    try:
        user_id_int = int(user_id)
    except (TypeError, ValueError) as err:
        raise HTTPException(status_code=401, detail="Invalid token payload") from err

    user_repo = UserRepository(db)
    user = user_repo.get(user_id_int)

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="User inactive")

    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]


def _normalized_role_names(user: User) -> set[str]:
    return {
        ur.role.name.strip().lower()
        for ur in getattr(user, "user_roles", [])
        if ur.role is not None and ur.role.name
    }


def user_farm_ids(user: User) -> list[int]:
    return [ur.farm_id for ur in getattr(user, "user_roles", []) if ur.farm_id is not None]


def has_role(user: User, role_name: str) -> bool:
    return role_name.strip().lower() in _normalized_role_names(user)


def has_any_role(user: User, *role_names: str) -> bool:
    normalized = _normalized_role_names(user)
    return any(role.strip().lower() in normalized for role in role_names)


def is_admin(user: User) -> bool:
    return has_role(user, "admin")


def is_operations(user: User) -> bool:
    return has_any_role(user, "operations team", "operation")


def is_farm_manager(user: User) -> bool:
    return has_role(user, "farm manager")


def can_access_all_farms(
    current_user: CurrentUserDep,
) -> bool:
    return is_admin(current_user) or is_operations(current_user)


def get_accessible_farm_ids(
    current_user: CurrentUserDep,
) -> list[int]:
    return [
        user_role.farm_id for user_role in current_user.user_roles if user_role.farm_id is not None
    ]


AccessibleFarmIdsDep = Annotated[
    list[int],
    Depends(get_accessible_farm_ids),
]


def assert_farm_access(
    current_user: CurrentUserDep,
    farm_id: int,
) -> None:
    if can_access_all_farms(current_user):
        return

    if farm_id not in get_accessible_farm_ids(current_user):
        raise HTTPException(
            status_code=403,
            detail="Forbidden",
        )


def can_access_user(
    current_user: CurrentUserDep,
    target_user,
) -> bool:
    if is_admin(current_user):
        return True

    current_farm_ids = set(
        get_accessible_farm_ids(current_user),
    )

    target_farm_ids = {role.farm_id for role in target_user.user_roles if role.farm_id is not None}

    return bool(
        current_farm_ids.intersection(
            target_farm_ids,
        )
    )


def assert_user_access(
    current_user: CurrentUserDep,
    target_user,
) -> None:
    if not can_access_user(
        current_user,
        target_user,
    ):
        raise HTTPException(
            status_code=403,
            detail="Forbidden",
        )
