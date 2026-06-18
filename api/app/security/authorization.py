"""
Authorization dependencies.
"""

from fastapi import HTTPException, status

from app.constants.roles import ADMIN_ROLE
from app.models.users.user import User
from app.security.dependencies import CurrentUserDep


class RequireRoles:
    """
    Require one of the specified roles.
    """

    def __init__(
        self,
        *allowed_roles: str,
    ):
        self.allowed_roles = set(
            allowed_roles,
        )

    def __call__(
        self,
        current_user: CurrentUserDep,
    ) -> User:
        user_roles = {user_role.role.name for user_role in current_user.user_roles}

        #
        # Admin bypass
        #
        if ADMIN_ROLE in user_roles:
            return current_user

        #
        # Required role check
        #
        if not self.allowed_roles.intersection(
            user_roles,
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )

        return current_user
