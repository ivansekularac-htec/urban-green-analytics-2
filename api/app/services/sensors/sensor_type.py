"""
Service layer for SensorType.

Handles business logic and database operations for sensor types.

Ensures data integrity and uniqueness constraints.
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.sensors.sensor_type import SensorType
from app.schemas.sensors.sensor_type import (
    SensorTypeCreate,
    SensorTypeUpdate,
)


class SensorTypeService:
    # -------------------------------------------------
    # READ
    # -------------------------------------------------

    def get(self, db: Session, sensor_type_id: int):
        """
        Retrieve a single SensorType by ID.

        Args:
            db (Session): Active DB session.
            sensor_type_id (int): Sensor type ID.

        Returns:
            SensorType: Requested entity.

        Raises:
            HTTPException: 404 if not found.
        """

        obj = db.query(SensorType).filter(SensorType.id == sensor_type_id).first()

        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sensor type not found",
            )

        return obj

    def get_all(self, db: Session):
        """
        Retrieve all SensorType records.

        Args:
            db (Session): Active DB session.

        Returns:
            list[SensorType]: All sensor types.
        """

        return db.query(SensorType).all()

    # -------------------------------------------------
    # CREATE
    # -------------------------------------------------

    def create(
        self,
        db: Session,
        data: SensorTypeCreate,
    ):
        """
        Create a new SensorType.

        Ensures name uniqueness and valid optimal range.

        Args:
            db (Session): Active DB session.
            data (SensorTypeCreate): Input payload.

        Returns:
            SensorType: Created entity.

        Raises:
            HTTPException: 400 if validation fails.
        """

        existing = db.query(SensorType).filter(SensorType.name == data.name).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Sensor type with this name already exists",
            )

        if (
            data.optimal_min is not None
            and data.optimal_max is not None
            and data.optimal_min > data.optimal_max
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="optimal_min cannot be greater than optimal_max",
            )

        obj = SensorType(**data.model_dump())

        db.add(obj)
        db.commit()
        db.refresh(obj)

        return obj

    # -------------------------------------------------
    # UPDATE
    # -------------------------------------------------

    def update(
        self,
        db: Session,
        sensor_type_id: int,
        data: SensorTypeUpdate,
    ):
        """
        Update SensorType (partial update supported).

        Args:
            db (Session): Active DB session.
            sensor_type_id (int): Entity ID.
            data (SensorTypeUpdate): Update payload.

        Returns:
            SensorType: Updated entity.

        Raises:
            HTTPException: 404 if not found.
            HTTPException: 400 if validation fails.
        """

        obj = self.get(db, sensor_type_id)

        update_data = data.model_dump(exclude_unset=True)

        if "name" in update_data:
            existing = (
                db.query(SensorType)
                .filter(SensorType.name == update_data["name"])
                .filter(SensorType.id != sensor_type_id)
                .first()
            )

            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Sensor type with this name already exists",
                )

        optimal_min = update_data.get(
            "optimal_min",
            obj.optimal_min,
        )

        optimal_max = update_data.get(
            "optimal_max",
            obj.optimal_max,
        )

        if optimal_min is not None and optimal_max is not None and optimal_min > optimal_max:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="optimal_min cannot be greater than optimal_max",
            )

        for key, value in update_data.items():
            setattr(obj, key, value)

        db.commit()
        db.refresh(obj)

        return obj

    # -------------------------------------------------
    # DELETE
    # -------------------------------------------------

    def delete(
        self,
        db: Session,
        sensor_type_id: int,
    ):
        """
        Delete a SensorType by ID.

        Args:
            db (Session): Active DB session.
            sensor_type_id (int): Entity ID.

        Returns:
            None

        Raises:
            HTTPException: 404 if not found.
        """

        obj = self.get(db, sensor_type_id)

        db.delete(obj)
        db.commit()

        return None
