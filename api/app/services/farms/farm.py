"""
Service layer for Farm entity.

Handles business logic for farms including:
- retrieving farms
- creating farms with FK validation
- updating farm data safely
- deleting farms
- validating related entities (infrastructure type, growing system type)
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.farms.farm import Farm
from app.models.farms.growing_system_type import GrowingSystemType
from app.models.farms.infrastructure_type import InfrastructureType
from app.schemas.farms.farm import FarmCreate, FarmUpdate


class FarmService:
    # -------------------------------------------------
    # READ
    # -------------------------------------------------
    def get(self, db: Session, farm_id: int):
        """
        Retrieve a farm by its ID.
        """
        obj = db.query(Farm).filter(Farm.id == farm_id).first()

        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Farm not found",
            )

        return obj

    def get_all(self, db: Session):
        """
        Retrieve all farms.
        """
        return db.query(Farm).all()

    # -------------------------------------------------
    # CREATE
    # -------------------------------------------------
    def create(self, db: Session, data: FarmCreate):
        """
        Create a new farm.
        """

        infra = (
            db.query(InfrastructureType)
            .filter(InfrastructureType.id == data.infrastructure_type_id)
            .first()
        )

        if not infra:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Infrastructure type not found",
            )

        growing = (
            db.query(GrowingSystemType)
            .filter(GrowingSystemType.id == data.growing_system_type_id)
            .first()
        )

        if not growing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Growing system type not found",
            )

        obj = Farm(**data.model_dump())

        db.add(obj)
        db.commit()
        db.refresh(obj)

        return obj

    # -------------------------------------------------
    # UPDATE
    # -------------------------------------------------
    def update(self, db: Session, farm_id: int, data: FarmUpdate):
        """
        Update an existing farm.
        """

        obj = self.get(db, farm_id)

        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Farm not found",
            )

        update_data = data.model_dump(exclude_unset=True)

        if "infrastructure_type_id" in update_data:
            infra = (
                db.query(InfrastructureType)
                .filter(InfrastructureType.id == update_data["infrastructure_type_id"])
                .first()
            )

            if not infra:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Infrastructure type not found",
                )

        if "growing_system_type_id" in update_data:
            growing = (
                db.query(GrowingSystemType)
                .filter(GrowingSystemType.id == update_data["growing_system_type_id"])
                .first()
            )

            if not growing:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Growing system type not found",
                )

        for k, v in update_data.items():
            setattr(obj, k, v)

        db.commit()
        db.refresh(obj)

        return obj

    # -------------------------------------------------
    # DELETE
    # -------------------------------------------------
    def delete(self, db: Session, farm_id: int):

        obj = self.get(db, farm_id)

        db.delete(obj)
        db.commit()

        return None
