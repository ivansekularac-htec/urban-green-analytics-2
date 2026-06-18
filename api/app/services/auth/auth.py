from fastapi import HTTPException, status
from jose import JWTError

from app.repositories.users.user import UserRepository
from app.schemas.auth.auth import LoginRequest, TokenResponse
from app.security.jwt import create_access_token, create_refresh_token, decode_token
from app.security.password import verify_password
from app.services.users.user import UserService


class AuthService:
    def __init__(self, user_repository: UserRepository, user_service: UserService):
        self.user_repository = user_repository
        self.user_service = user_service

    def login(self, payload: LoginRequest) -> TokenResponse:
        user = self.user_repository.get_by_email(payload.email)

        if user is None or not verify_password(payload.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Inactive user.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        roles = self.user_repository.get_role_names_for_user(user.id)
        return self._build_token_response(user.id, user.email, roles)

    def refresh(self, refresh_token: str) -> TokenResponse:
        try:
            payload = decode_token(refresh_token)
        except JWTError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token.",
            ) from exc

        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token.",
            )

        user_id = int(payload["sub"])
        user = self.user_repository.get_with_roles(user_id)

        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token.",
            )

        roles = self.user_repository.get_role_names_for_user(user.id)
        return self._build_token_response(user.id, user.email, roles)

    def _build_token_response(self, user_id: int, email: str, roles: list[str]) -> TokenResponse:
        from app.config import get_settings

        settings = get_settings()
        return TokenResponse(
            access_token=create_access_token(user_id=user_id, email=email, roles=roles),
            refresh_token=create_refresh_token(user_id=user_id),
            expires_in=settings.jwt_access_token_expire_minutes * 60,
        )
