"""
JWT utilities.
"""

from datetime import UTC, datetime, timedelta

import jwt

from app.config import get_settings


def create_access_token(
    *,
    user_id: int,
    email: str,
) -> str:
    """
    Create a signed JWT access token.
    """
    settings = get_settings()

    expire = datetime.now(UTC) + timedelta(
        minutes=settings.jwt_access_token_expire_minutes,
    )

    payload = {
        "sub": email,
        "user_id": user_id,
        "exp": expire,
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_token(token: str) -> dict:
    """
    Decode and validate a JWT token.

    Raises:
        jwt.InvalidTokenError: If token is invalid or expired.
    """
    settings = get_settings()

    return jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )
