"""
User repository.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.users.user import User
from app.models.users.user_roles import UserRole
from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    """
    Repository for User database operations.
    """

    def __init__(self, db: Session):
        super().__init__(User, db)

    def get_by_email(self, email: str):
        return self.db.query(User).filter(User.email == email).first()

    from sqlalchemy import select

    def list_by_farm_ids(self, farm_ids: list[int], skip: int = 0, limit: int = 100) -> list[User]:
        if not farm_ids:
            return []

        stmt = (
            select(User)
            .join(User.user_roles)
            .where(
                UserRole.farm_id.in_(farm_ids),
            )
            .distinct()
            .offset(skip)
            .limit(limit)
        )

        return list(self.db.scalars(stmt).all())
