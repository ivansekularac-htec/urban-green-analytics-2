"""
Service layer for InfrastructureType.

Handles business logic and database operations for farm infrastructure types.

Ensures data integrity and uniqueness constraints.
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.farms.infrastructure_type import InfrastructureType
from app.schemas.farms.infrastructure_type import (
    InfrastructureTypeCreate,
    InfrastructureTypeUpdate,
)


class InfrastructureTypeService:
    # -------------------------------------------------
    # READ
    # -------------------------------------------------
    def get(self, db: Session, type_id: int):
        """
        Retrieve a single InfrastructureType by ID.

        Args:
            db (Session): Active DB session.
            type_id (int): Infrastructure type ID.

        Returns:
            InfrastructureType: Requested entity.

        Raises:
            HTTPException: 404 if not found.
        """

        obj = db.query(InfrastructureType).filter(InfrastructureType.id == type_id).first()

        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Infrastructure type not found",
            )

        return obj

    def get_all(self, db: Session):
        """
        Retrieve all InfrastructureType records.

        Args:
            db (Session): Active DB session.

        Returns:
            list[InfrastructureType]: All infrastructure types.
        """

        return db.query(InfrastructureType).all()

    # -------------------------------------------------
    # CREATE
    # -------------------------------------------------
    def create(self, db: Session, data: InfrastructureTypeCreate):
        """
        Create a new InfrastructureType.

        Ensures name uniqueness before creation.

        Args:
            db (Session): Active DB session.
            data (InfrastructureTypeCreate): Input payload.

        Returns:
            InfrastructureType: Created entity.

        Raises:
            HTTPException: 400 if name already exists.
        """

        existing = db.query(InfrastructureType).filter(InfrastructureType.name == data.name).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Infrastructure type with this name already exists",
            )

        obj = InfrastructureType(**data.model_dump())

        db.add(obj)
        db.commit()
        db.refresh(obj)

        return obj

    # -------------------------------------------------
    # UPDATE
    # -------------------------------------------------
    def update(self, db: Session, type_id: int, data: InfrastructureTypeUpdate):
        """
        Update InfrastructureType (partial update supported).

        Args:
            db (Session): Active DB session.
            type_id (int): Entity ID.
            data (InfrastructureTypeUpdate): Update payload.

        Returns:
            InfrastructureType: Updated entity.

        Raises:
            HTTPException: 404 if not found.
            HTTPException: 400 if name already exists.
        """

        obj = self.get(db, type_id)

        update_data = data.model_dump(exclude_unset=True)

        if "name" in update_data:
            existing = (
                db.query(InfrastructureType)
                .filter(InfrastructureType.name == update_data["name"])
                .filter(InfrastructureType.id != type_id)
                .first()
            )

            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Infrastructure type with this name already exists",
                )

        for k, v in update_data.items():
            setattr(obj, k, v)

        db.commit()
        db.refresh(obj)

        return obj

    # -------------------------------------------------
    # DELETE
    # -------------------------------------------------
    def delete(self, db: Session, type_id: int):
        """
        Delete an InfrastructureType by ID.

        Args:
            db (Session): Active DB session.
            type_id (int): Entity ID.

        Returns:
            None

        Raises:
            HTTPException: 404 if not found.
        """

        obj = self.get(db, type_id)

        db.delete(obj)
        db.commit()

        return None
