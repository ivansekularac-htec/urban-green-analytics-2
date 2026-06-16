"""
Service layer for QualityGrade.

Handles business logic and database operations for quality grades.

Ensures data integrity and uniqueness constraints.
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.harvests.quality_grade import QualityGrade
from app.schemas.harvests.quality_grade import (
    QualityGradeCreate,
    QualityGradeUpdate,
)


class QualityGradeService:
    # -------------------------------------------------
    # READ
    # -------------------------------------------------

    def get(self, db: Session, grade_id: int):
        """
        Retrieve a single QualityGrade by ID.

        Args:
            db (Session): Active DB session.
            grade_id (int): Quality grade ID.

        Returns:
            QualityGrade: Requested entity.

        Raises:
            HTTPException: 404 if not found.
        """

        obj = db.query(QualityGrade).filter(QualityGrade.id == grade_id).first()

        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quality grade not found",
            )

        return obj

    def get_all(self, db: Session):
        """
        Retrieve all QualityGrade records.

        Args:
            db (Session): Active DB session.

        Returns:
            list[QualityGrade]: All quality grades.
        """

        return db.query(QualityGrade).all()

    # -------------------------------------------------
    # CREATE
    # -------------------------------------------------

    def create(self, db: Session, data: QualityGradeCreate):
        """
        Create a new QualityGrade.

        Ensures code uniqueness before creation.

        Args:
            db (Session): Active DB session.
            data (QualityGradeCreate): Input payload.

        Returns:
            QualityGrade: Created entity.

        Raises:
            HTTPException: 400 if code already exists.
        """

        existing = db.query(QualityGrade).filter(QualityGrade.code == data.code).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Quality grade with this code already exists",
            )

        obj = QualityGrade(**data.model_dump())

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
        grade_id: int,
        data: QualityGradeUpdate,
    ):
        """
        Update QualityGrade (partial update supported).

        Args:
            db (Session): Active DB session.
            grade_id (int): Entity ID.
            data (QualityGradeUpdate): Update payload.

        Returns:
            QualityGrade: Updated entity.

        Raises:
            HTTPException: 404 if not found.
            HTTPException: 400 if code already exists.
        """

        obj = self.get(db, grade_id)

        update_data = data.model_dump(exclude_unset=True)

        if "code" in update_data:
            existing = (
                db.query(QualityGrade)
                .filter(QualityGrade.code == update_data["code"])
                .filter(QualityGrade.id != grade_id)
                .first()
            )

            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Quality grade with this code already exists",
                )

        for key, value in update_data.items():
            setattr(obj, key, value)

        db.commit()
        db.refresh(obj)

        return obj

    # -------------------------------------------------
    # DELETE
    # -------------------------------------------------

    def delete(self, db: Session, grade_id: int):
        """
        Delete a QualityGrade by ID.

        Args:
            db (Session): Active DB session.
            grade_id (int): Entity ID.

        Returns:
            None

        Raises:
            HTTPException: 404 if not found.
        """

        obj = self.get(db, grade_id)

        db.delete(obj)
        db.commit()

        return None


quality_grade_service = QualityGradeService()
