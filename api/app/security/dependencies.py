from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models.users.user import User
from app.repositories.users.user import UserRepository
from app.security.jwt import decode_token
from app.security.roles import RoleName

settings = get_settings()

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.api_v1_prefix}/auth/login",
)


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_token(token)
    except JWTError as exc:
        raise credentials_exc from exc

    if payload.get("type") != "access":
        raise credentials_exc

    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exc

    user = UserRepository(db).get(int(user_id))
    if user is None or not user.is_active:
        raise credentials_exc

    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]


def require_roles(*allowed_roles: str):
    def checker(current_user: CurrentUserDep, db: Annotated[Session, Depends(get_db)]) -> User:
        role_names = UserRepository(db).get_role_names_for_user(current_user.id)

        if not any(role in allowed_roles for role in role_names):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions.",
            )

        return current_user

    return checker


def require_admin():
    return require_roles(RoleName.ADMIN)


def require_authenticated():
    return get_current_user
