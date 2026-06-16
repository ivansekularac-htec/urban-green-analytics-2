"""
Service layer for Sensor.

Handles business logic and database operations for sensors.

Ensures referenced entities exist and serial numbers remain unique.
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.farms.farm import Farm
from app.models.sensors.sensor import Sensor
from app.models.sensors.sensor_type import SensorType
from app.schemas.sensors.sensor import (
    SensorCreate,
    SensorUpdate,
)


class SensorService:
    # -------------------------------------------------
    # READ
    # -------------------------------------------------

    def get(self, db: Session, sensor_id: int):
        """
        Retrieve a sensor by ID.

        Args:
            db (Session): Active DB session.
            sensor_id (int): Sensor ID.

        Returns:
            Sensor: Requested entity.

        Raises:
            HTTPException: 404 if not found.
        """

        obj = db.query(Sensor).filter(Sensor.id == sensor_id).first()

        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sensor not found",
            )

        return obj

    def get_all(self, db: Session):
        """
        Retrieve all sensors.

        Args:
            db (Session): Active DB session.

        Returns:
            list[Sensor]: All sensors.
        """

        return db.query(Sensor).all()

    # -------------------------------------------------
    # CREATE
    # -------------------------------------------------

    def create(
        self,
        db: Session,
        data: SensorCreate,
    ):
        """
        Create a new sensor.

        Validates farm, sensor type and serial uniqueness.

        Args:
            db (Session): Active DB session.
            data (SensorCreate): Input payload.

        Returns:
            Sensor: Created entity.
        """

        farm = db.query(Farm).filter(Farm.id == data.farm_id).first()

        if not farm:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Farm not found",
            )

        sensor_type = db.query(SensorType).filter(SensorType.id == data.sensor_type_id).first()

        if not sensor_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sensor type not found",
            )

        existing = db.query(Sensor).filter(Sensor.serial_number == data.serial_number).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Sensor with this serial number already exists",
            )

        obj = Sensor(**data.model_dump())

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
        sensor_id: int,
        data: SensorUpdate,
    ):
        """
        Update sensor.

        Args:
            db (Session): Active DB session.
            sensor_id (int): Sensor ID.
            data (SensorUpdate): Update payload.

        Returns:
            Sensor: Updated entity.
        """

        obj = self.get(db, sensor_id)

        update_data = data.model_dump(exclude_unset=True)

        if "farm_id" in update_data:
            farm = db.query(Farm).filter(Farm.id == update_data["farm_id"]).first()

            if not farm:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Farm not found",
                )

        if "sensor_type_id" in update_data:
            sensor_type = (
                db.query(SensorType).filter(SensorType.id == update_data["sensor_type_id"]).first()
            )

            if not sensor_type:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Sensor type not found",
                )

        if "serial_number" in update_data:
            existing = (
                db.query(Sensor)
                .filter(Sensor.serial_number == update_data["serial_number"])
                .filter(Sensor.id != sensor_id)
                .first()
            )

            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Sensor with this serial number already exists",
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
        sensor_id: int,
    ):
        """
        Delete sensor.

        Args:
            db (Session): Active DB session.
            sensor_id (int): Sensor ID.
        """

        obj = self.get(db, sensor_id)

        db.delete(obj)
        db.commit()

        return None
