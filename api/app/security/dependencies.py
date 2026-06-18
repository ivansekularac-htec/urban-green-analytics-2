"""
Authentication and authorization dependencies.

Four pieces interns can read top-to-bottom:

* :func:`get_current_user` decodes the JWT and loads the user.
* :func:`require_roles` returns a dependency that 403s unless the user
  has at least one of the listed roles. Use it on a route's
  ``dependencies=[...]`` or as the user-yielding parameter dependency.
* :func:`get_accessible_farm_ids` yields the set of farm ids the user
  may see (``None`` for Admin, meaning unrestricted).
* :func:`assert_farm_access` is a plain helper for write endpoints to
  check that the current user may act on a specific farm.
"""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.database import DatabaseSession
from app.models.users.user import User
from app.models.users.user_roles import UserRole
from app.security.jwt import decode_access_token
from app.security.roles import RoleName

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{get_settings().api_v1_prefix}/auth/login")


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: DatabaseSession,
) -> User:
    """Resolve the current authenticated user from the bearer token.

    Loads ``user_roles`` (and their ``role``) eagerly so authorization
    checks don't trigger lazy queries on a closed session.
    """
    user_id = decode_access_token(token)

    statement = (
        select(User)
        .where(User.id == user_id)
        .options(selectinload(User.user_roles).selectinload(UserRole.role))
    )
    user = db.scalars(statement).one_or_none()

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def _user_role_names(user: User) -> set[str]:
    return {ur.role.name for ur in user.user_roles}


def require_roles(*allowed: RoleName):
    """Build a dependency that requires the user to have any of ``allowed``.

    Usage::

        @router.get("", dependencies=[Depends(require_roles(RoleName.ADMIN))])
        def list_things(...): ...

    Or, when the endpoint also needs the user object::

        def create_harvest(
            payload: HarvestCreate,
            user: Annotated[User, Depends(require_roles(RoleName.ADMIN, RoleName.OPERATIONS_TEAM))],
        ): ...
    """
    allowed_names = {r.value for r in allowed}

    def dependency(user: CurrentUser) -> User:
        if not _user_role_names(user) & allowed_names:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role.",
            )
        return user

    return dependency


def get_accessible_farm_ids(user: CurrentUser) -> set[int] | None:
    """Return the set of farm ids the user may access, or ``None`` for Admin.

    ``None`` means *unrestricted* — list endpoints should skip the
    ``WHERE farm_id IN (...)`` filter entirely. A non-Admin with no
    farm assignments yields an empty set, which correctly returns no rows.
    """
    if RoleName.ADMIN.value in _user_role_names(user):
        return None
    return {ur.farm_id for ur in user.user_roles if ur.farm_id is not None}


AccessibleFarms = Annotated[set[int] | None, Depends(get_accessible_farm_ids)]


def assert_farm_access(
    user: User,
    farm_id: int,
    allowed_roles: tuple[RoleName, ...],
) -> None:
    """Ensure ``user`` may write on ``farm_id`` under one of ``allowed_roles``.

    Admin always passes. Otherwise the user must have at least one
    ``UserRole`` row whose role is in ``allowed_roles`` AND whose
    ``farm_id`` equals the target farm.
    """
    if RoleName.ADMIN.value in _user_role_names(user):
        return

    allowed_names = {r.value for r in allowed_roles}
    for ur in user.user_roles:
        if ur.farm_id == farm_id and ur.role.name in allowed_names:
            return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You do not have access to this farm.",
    )


def assert_farm_in_scope(farm_id: int, farms: set[int] | None) -> None:
    """For detail-read endpoints: hide rows outside the user's farm scope as 404.

    Pair with :data:`AccessibleFarms` — when ``farms`` is ``None`` the
    user is Admin (no scoping) and this is a no-op.
    """
    if farms is not None and farm_id not in farms:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found.",
        )
