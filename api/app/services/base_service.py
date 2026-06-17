"""
Generic service utilities for CRUD operations.
"""

from typing import Generic, NoReturn, TypeVar

from fastapi import HTTPException, status
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError

from app.database import Base
from app.repositories.base_repository import BaseRepository

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseService(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Base service for common CRUD operations.
    """

    def __init__(self, repository: BaseRepository[ModelType], entity_name: str):
        """
        Initialize the service with a repository and entity name.

        Args:
            repository: Repository instance used for database operations.
            entity_name: Human-readable entity name used in error messages.
        """
        self.repository = repository
        self.entity_name = entity_name

    def get(self, item_id: int) -> ModelType:
        """
        Return a single entity by ID.

        Args:
            item_id: Primary key of the entity.

        Returns:
            The requested ORM model instance.

        Raises:
            HTTPException: If the entity does not exist.
        """
        item = self.repository.get(item_id)

        if item is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{self.entity_name} not found.",
            )

        return item

    def list(self, skip: int = 0, limit: int = 100) -> list[ModelType]:
        """
        Return a paginated list of entities.

        Args:
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            A list of ORM model instances.
        """
        return self.repository.list(skip=skip, limit=limit)

    def create(self, payload: CreateSchemaType) -> ModelType:
        """
        Create a new entity.

        Args:
            payload: Pydantic schema containing data for the new entity.

        Returns:
            The created ORM model instance.
        """
        data = payload.model_dump()

        try:
            item = self.repository.create(data)
            self.repository.commit()
            return item
        except IntegrityError as exc:
            self._raise_integrity_conflict(exc)

    def update(self, item_id: int, payload: UpdateSchemaType) -> ModelType:
        """
        Update an existing entity by ID.

        Only fields explicitly provided in the request payload are updated.
        If no fields are provided, the existing entity is returned unchanged.

        Args:
            item_id: Primary key of the entity to update.
            payload: Pydantic schema containing fields to update.

        Returns:
            The updated ORM model instance.

        Raises:
            HTTPException: If the entity does not exist.
        """
        item = self.get(item_id)

        data = payload.model_dump(exclude_unset=True)

        if not data:
            return item

        try:
            updated_item = self.repository.update(item, data)
            self.repository.commit()
            return updated_item
        except IntegrityError as exc:
            self._raise_integrity_conflict(exc)

    def delete(self, item_id: int) -> None:
        """
        Delete an existing entity by ID.

        Args:
            item_id: Primary key of the entity to delete.

        Raises:
            HTTPException: If the entity does not exist.
        """
        item = self.get(item_id)

        try:
            self.repository.delete(item)
            self.repository.commit()
        except IntegrityError as exc:
            self._raise_integrity_conflict(exc)

    def _raise_integrity_conflict(self, error: IntegrityError) -> NoReturn:
        """
        Roll back the failed transaction and raise an HTTP conflict error.

        Integrity errors include unique constraint violations, foreign key
        violations, and restricted delete operations.
        """
        self.repository.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{self.entity_name} violates a database constraint.",
        ) from error
