"""
User service.
"""

from sqlalchemy.exc import IntegrityError

from app.models.users.user import User
from app.repositories.users.user import UserRepository
from app.schemas.users.user import UserCreate, UserUpdate
from app.security.password import hash_password
from app.services.base_service import BaseService


class UserService(BaseService[User, UserCreate, UserUpdate]):
    """
    Service for User business logic.
    """

    def __init__(self, repository: UserRepository):
        super().__init__(repository, "User")

    def create(self, payload: UserCreate) -> User:
        """
        Create a user with a hashed password.
        """
        data = payload.model_dump()
        password = data.pop("password")

        data["password_hash"] = hash_password(password)

        try:
            user = self.repository.create(data)
            self.repository.commit()
            return user
        except IntegrityError as exc:
            self._raise_integrity_conflict(exc)

    def update(self, item_id: int, payload: UserUpdate) -> User:
        """
        Update a user and hash the password if it is provided.
        """
        item = self.get(item_id)

        data = payload.model_dump(exclude_unset=True)

        if not data:
            return item

        password = data.pop("password", None)

        if password is not None:
            data["password_hash"] = hash_password(password)

        try:
            user = self.repository.update(item, data)
            self.repository.commit()
            return user
        except IntegrityError as exc:
            self._raise_integrity_conflict(exc)

    def get_by_email(self, email: str):
        return self.repository.get_by_email(email)

    def list_by_farm_ids(self, farm_ids: list[int], skip: int = 0, limit: int = 100):
        return self.repository.list_by_farm_ids(
            farm_ids=farm_ids,
            skip=skip,
            limit=limit,
        )
