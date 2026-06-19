"""
JWT access-token utilities.

Tokens carry only the user id (``sub``); roles and active state are
re-fetched from the database on each request so revoking access is
immediate (no token blacklist needed).
"""

from datetime import UTC, datetime, timedelta

import jwt
from fastapi import HTTPException, status

from app.config import get_settings


def create_access_token(user_id: int) -> str:
    """Encode a JWT for the given user id."""
    settings = get_settings()
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.jwt_expires_minutes)
    payload = {"sub": str(user_id), "exp": expires_at}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> int:
    """Decode a JWT and return the user id.

    Raises ``HTTPException(401)`` for any decoding error (expired, tampered,
    malformed, missing claim) so callers don't need to distinguish causes.
    """
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
