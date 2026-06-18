"""
Password hashing utilities.
"""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

from jose import jwt

from app.config import get_settings


def hash_password(password: str) -> str:
    """
    Hash a plain-text password using PBKDF2.
    """
    salt = secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100_000,
    ).hex()

    return f"pbkdf2_sha256${salt}${password_hash}"


def verify_password(
    plain_password: str,
    stored_password: str,
) -> bool:
    """
    Verify a plain-text password against a stored PBKDF2 hash.
    """
    try:
        _, salt, password_hash = stored_password.split("$")
    except ValueError:
        return False

    calculated_hash = hashlib.pbkdf2_hmac(
        "sha256",
        plain_password.encode("utf-8"),
        salt.encode("utf-8"),
        100_000,
    ).hex()

    return secrets.compare_digest(
        calculated_hash,
        password_hash,
    )


def create_access_token(
    subject: str,
    roles: list[str],
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed JWT access token.

    Args:
        subject: User identifier stored in the token subject claim.
        roles: Role names assigned to the user.
        expires_delta: Optional custom token expiration duration.

    Returns:
        str: Encoded JWT access token.
    """
    settings = get_settings()

    expire = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )

    payload: dict[str, Any] = {
        "sub": subject,
        "roles": roles,
        "exp": expire,
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT access token.

    Args:
        token: Encoded JWT access token.

    Returns:
        dict[str, Any]: Decoded token payload.

    Raises:
        JWTError: If the token is invalid or expired.
    """
    settings = get_settings()

    return jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )
