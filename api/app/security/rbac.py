from typing import Annotated

from fastapi import Depends, HTTPException

from app.models.users.user import User
from app.routers.v1.auth.dependencies import get_current_user


def require_roles(*allowed_roles: str):
    def wrapper(
        user: Annotated[User, Depends(get_current_user)],
    ):
        user_roles = {role.role.name.lower() for role in user.user_roles or []}

        if "admin" in user_roles:
            return user

        allowed = {role.lower() for role in allowed_roles}

        if not user_roles.intersection(allowed):
            raise HTTPException(
                status_code=403,
                detail="Not enough permissions",
            )

        return user

    return wrapper
