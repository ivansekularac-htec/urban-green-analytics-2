from fastapi import HTTPException

from app.schemas.auth.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.users.user import UserCreate, UserResponse
from app.security.jwt import create_access_token
from app.security.password import verify_password
from app.services.users.user import UserService


class AuthService:
    def __init__(self, user_service: UserService):
        self.user_service = user_service

    def login(self, data: LoginRequest) -> TokenResponse:
        user = self.user_service.get_by_email(data.email)

        if not user:
            raise HTTPException(401, "Invalid credentials")

        if not user.is_active:
            raise HTTPException(403, "User inactive")

        if not verify_password(data.password, user.password_hash):
            raise HTTPException(401, "Invalid credentials")

        roles = [ur.role.name for ur in user.user_roles or []]

        token = create_access_token(
            {
                "sub": str(user.id),
                "email": user.email,
                "roles": roles,
            }
        )

        return TokenResponse(access_token=token)

    def register(self, data: RegisterRequest):
        existing = self.user_service.get_by_email(data.email)

        if existing:
            raise HTTPException(400, "User already exists")

        user = self.user_service.create(
            UserCreate(
                email=data.email,
                password=data.password,
                full_name=data.full_name,
                is_active=True,
            )
        )

        return UserResponse.model_validate(user)
