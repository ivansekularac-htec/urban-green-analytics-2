"""
Generic farm-scoped service utilities.

Extends BaseService with farm-level authorization: non-admin users may only
read and modify entities that belong to farms they are assigned to. Admins
(global scope) are unrestricted.
"""

from typing import TypeVar

from fastapi import HTTPException, status
from pydantic import BaseModel

from app.database import Base
from app.models.users.user import User
from app.repositories.base_repository import BaseRepository
from app.security.dependencies import scoped_farm_ids
from app.services.base_service import BaseService

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class ScopedService(BaseService[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Base service that restricts access to a user's assigned farms.

    ``farm_field`` is the attribute on the model that holds the owning farm id.
    For the Farm model itself this is its own primary key (``id``).
    """

    farm_field: str = "farm_id"

    def __init__(
        self,
        repository: BaseRepository[ModelType],
        entity_name: str,
        current_user: User,
    ):
        super().__init__(repository, entity_name)
        # None means global (Admin) access; otherwise the set of allowed farms.
        self.allowed_farm_ids = scoped_farm_ids(current_user)

    def _farm_id_of(self, item: ModelType) -> int:
        return getattr(item, self.farm_field)

    def get(self, item_id: int) -> ModelType:
        """Return an entity, hiding it (404) if it is outside the user's farms."""
        item = super().get(item_id)

        if (
            self.allowed_farm_ids is not None
            and self._farm_id_of(item) not in self.allowed_farm_ids
        ):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{self.entity_name} not found.",
            )

        return item

    def list(self, skip: int = 0, limit: int = 100) -> list[ModelType]:
        """List entities, filtered to the user's farms (Admins see all)."""
        return self.repository.list(
            skip=skip,
            limit=limit,
            farm_ids=self.allowed_farm_ids,
            farm_field=self.farm_field,
        )

    def create(self, payload: CreateSchemaType) -> ModelType:
        """Create an entity, rejecting farms outside the user's scope."""
        self._ensure_payload_in_scope(payload)
        return super().create(payload)

    def _ensure_payload_in_scope(self, payload: CreateSchemaType) -> None:
        if self.allowed_farm_ids is None:
            return

        farm_id = getattr(payload, "farm_id", None)

        if farm_id is not None and farm_id not in self.allowed_farm_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not allowed to write to this farm.",
            )
