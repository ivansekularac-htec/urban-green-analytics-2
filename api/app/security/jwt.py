from datetime import UTC, datetime, timedelta
from typing import Any

from jose import jwt

from app.config import get_settings

settings = get_settings()


def _utcnow() -> datetime:
    return datetime.now(UTC)


def create_access_token(*, user_id: int, email: str, roles: list[str]) -> str:
    expire = _utcnow() + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    payload = {
        "sub": str(user_id),
        "email": email,
        "roles": roles,
        "type": "access",
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(*, user_id: int) -> str:
    expire = _utcnow() + timedelta(minutes=settings.jwt_refresh_token_expire_minutes)
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )
