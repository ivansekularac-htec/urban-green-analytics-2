from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt

from app.config import get_settings

settings = get_settings()


def create_access_token(data: dict) -> str:
    """
    Create JWT access token with expiration.
    """
    expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)

    payload = data.copy()
    payload.update({"exp": expire})

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> dict | None:
    """
    Decode and validate JWT access token.
    """
    try:
        return jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError:
        return None
