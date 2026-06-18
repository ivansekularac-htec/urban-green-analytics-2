from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.security.jwt import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/login")


def get_current_user_payload(token: str = Depends(oauth2_scheme)) -> dict:
    """
    Decode JWT token and return current user payload.
    """
    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    return payload


current_user_payload_dep = Depends(get_current_user_payload)


def require_roles(*allowed_roles: str) -> Callable:
    """
    Require at least one of the allowed roles from JWT payload.
    Admin is always allowed.
    """

    def dependency(payload: dict = current_user_payload_dep) -> dict:
        user_roles = [role.lower() for role in payload.get("roles", [])]
        normalized_allowed_roles = [role.lower() for role in allowed_roles]

        if "admin" in user_roles:
            return payload

        if not any(role in user_roles for role in normalized_allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )

        return payload

    return dependency
