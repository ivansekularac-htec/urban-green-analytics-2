from sqlalchemy.orm import Session

from app.repositories.users.user import UserRepository
from app.security.jwt import create_access_token
from app.security.password import verify_password


class AuthService:
    def __init__(self, db: Session):
        self.user_repository = UserRepository(db)

    def login(self, email: str, password: str) -> str | None:
        user = self.user_repository.get_by_email(email)

        if user is None:
            return None

        if not verify_password(password, user.password_hash):
            return None

        roles = [role.name for role in user.roles]
        farm_ids = [farm.farm_id for farm in user.farms] if hasattr(user, "farms") else []

        return create_access_token(
            {
                "sub": str(user.user_id),
                "email": user.email,
                "roles": roles,
                "farm_ids": farm_ids,
            }
        )
