from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt

from app.config import get_settings

settings = get_settings()


def create_access_token(
    data: dict,
) -> str:
    to_encode = data.copy()
    now = datetime.now(UTC)
    expire = now + timedelta(minutes=settings.access_token_expire_minutes)

    to_encode["iat"] = now
    to_encode["iss"] = settings.token_issuer
    to_encode["aud"] = settings.token_audience
    to_encode["exp"] = expire

    return jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm,
    )


def decode_token(
    token: str,
) -> dict:
    try:
        return jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
            issuer=settings.token_issuer,
            audience=settings.token_audience,
            options={"require": ["exp", "iat", "iss", "aud"]},
        )

    except JWTError as exc:
        raise ValueError("Invalid token") from exc
