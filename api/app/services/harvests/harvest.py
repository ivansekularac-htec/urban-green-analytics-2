"""
Service layer for Harvest.

Handles business logic and database operations for harvest records.

Ensures data integrity and foreign key validity for farm, crop, and quality grade relations.
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.crops.crop import Crop
from app.models.farms.farm import Farm
from app.models.harvests.harvest import Harvest
from app.models.harvests.quality_grade import QualityGrade
from app.schemas.harvests.harvest import (
    HarvestCreate,
    HarvestUpdate,
)


class HarvestService:
    # -------------------------------------------------
    # READ
    # -------------------------------------------------
    def get(self, db: Session, harvest_id: int):
        """
        Retrieve a single Harvest by ID.

        Args:
            db (Session): Active DB session.
            harvest_id (int): Harvest ID.

        Returns:
            Harvest: Requested entity.

        Raises:
            HTTPException: 404 if not found.
        """

        obj = db.query(Harvest).filter(Harvest.id == harvest_id).first()

        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Harvest not found",
            )

        return obj

    def get_all(self, db: Session):
        """
        Retrieve all Harvest records.

        Optionally filter by farm_id.

        Args:
            db (Session): Active DB session.
            farm_id (int | None): Optional farm filter.

        Returns:
            list[Harvest]: List of harvest records.
        """

        return db.query(Harvest).all()

    # -------------------------------------------------
    # CREATE
    # -------------------------------------------------
    def create(self, db: Session, data: HarvestCreate):
        """
        Create a new Harvest record.

        Validates existence of related farm, crop, and quality grade.

        Args:
            db (Session): Active DB session.
            data (HarvestCreate): Input payload.

        Returns:
            Harvest: Created entity.

        Raises:
            HTTPException: 404 if related entities are missing.
        """

        farm = db.query(Farm).filter(Farm.id == data.farm_id).first()
        if not farm:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Farm not found",
            )

        crop = db.query(Crop).filter(Crop.id == data.crop_id).first()
        if not crop:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Crop not found",
            )

        grade = db.query(QualityGrade).filter(QualityGrade.id == data.quality_grade_id).first()

        if not grade:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quality grade not found",
            )

        obj = Harvest(**data.model_dump())

        db.add(obj)
        db.commit()
        db.refresh(obj)

        return obj

    # -------------------------------------------------
    # UPDATE
    # -------------------------------------------------
    def update(self, db: Session, harvest_id: int, data: HarvestUpdate):
        """
        Update Harvest (partial update supported).

        Args:
            db (Session): Active DB session.
            harvest_id (int): Harvest ID.
            data (HarvestUpdate): Update payload.

        Returns:
            Harvest: Updated entity.

        Raises:
            HTTPException: 404 if not found.
        """

        obj = self.get(db, harvest_id)

        update_data = data.model_dump(exclude_unset=True)

        if "quality_grade_id" in update_data:
            grade = (
                db.query(QualityGrade)
                .filter(QualityGrade.id == update_data["quality_grade_id"])
                .first()
            )

            if not grade:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Quality grade not found",
                )

        for k, v in update_data.items():
            setattr(obj, k, v)

        db.commit()
        db.refresh(obj)

        return obj

    # -------------------------------------------------
    # DELETE
    # -------------------------------------------------
    def delete(self, db: Session, harvest_id: int):
        """
        Delete a Harvest by ID.

        Args:
            db (Session): Active DB session.
            harvest_id (int): Harvest ID.

        Returns:
            None

        Raises:
            HTTPException: 404 if not found.
        """

        obj = self.get(db, harvest_id)

        db.delete(obj)
        db.commit()

        return None
