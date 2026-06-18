"""
JWT token utilities.

Builds and verifies signed JSON Web Tokens for authentication. Tokens carry
the user id (``sub``), email, and role names, plus standard ``type``, ``iat``
and ``exp`` claims.
"""

from datetime import UTC, datetime, timedelta

import jwt

from app.config import get_settings

ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"


def create_access_token(user_id: int, email: str, roles: list[str]) -> str:
    """
    Create a signed access token for the given user.

    Args:
        user_id: Primary key of the authenticated user (stored in ``sub``).
        email: User email, included as a convenience claim.
        roles: Names of the roles assigned to the user.

    Returns:
        The encoded JWT as a string.
    """
    settings = get_settings()

    issued_at = datetime.now(UTC)
    expires_at = issued_at + timedelta(minutes=settings.access_token_expire_minutes)

    payload = {
        "sub": str(user_id),
        "email": email,
        "roles": roles,
        "type": ACCESS_TOKEN_TYPE,
        "iat": issued_at,
        "exp": expires_at,
    }

    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(user_id: int) -> str:
    """
    Create a signed refresh token for the given user.

    Refresh tokens carry minimal claims; roles are re-fetched when a new
    access token is issued, so role changes take effect on refresh.
    """
    settings = get_settings()

    issued_at = datetime.now(UTC)
    expires_at = issued_at + timedelta(days=settings.refresh_token_expire_days)

    payload = {
        "sub": str(user_id),
        "type": REFRESH_TOKEN_TYPE,
        "iat": issued_at,
        "exp": expires_at,
    }

    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    """
    Decode and verify a JWT.

    Args:
        token: The encoded JWT string.

    Returns:
        The decoded claims.

    Raises:
        jwt.PyJWTError: If the token is invalid, expired, or has a bad signature.
    """
    settings = get_settings()

    return jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )
