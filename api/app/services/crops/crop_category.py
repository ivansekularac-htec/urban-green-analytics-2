from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.crops.crop_category import CropCategory
from app.schemas.crops.crop_category import (
    CropCategoryCreate,
    CropCategoryUpdate,
)


class CropCategoryService:
    # ------------------------------------------------------
    # READ
    # ------------------------------------------------------
    def get(self, db: Session, category_id: int):
        obj = db.query(CropCategory).filter(CropCategory.id == category_id).first()

        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Crop category not found",
            )

        return obj

    def get_all(self, db: Session):
        return db.query(CropCategory).all()

    # ------------------------------------------------------
    # CREATE
    # ------------------------------------------------------
    def create(self, db: Session, data: CropCategoryCreate):
        existing = db.query(CropCategory).filter(CropCategory.name == data.name).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Crop category with this name already exists",
            )

        obj = CropCategory(**data.model_dump())

        db.add(obj)
        db.commit()
        db.refresh(obj)

        return obj

    # ------------------------------------------------------
    # UPDATE
    # ------------------------------------------------------
    def update(
        self,
        db: Session,
        obj_id: int,
        data: CropCategoryUpdate,
    ):
        obj = self.get(db, obj_id)

        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Crop category not found",
            )

        update_data = data.model_dump(exclude_unset=True)

        if "name" in update_data:
            existing = (
                db.query(CropCategory)
                .filter(CropCategory.name == update_data["name"])
                .filter(CropCategory.id != obj_id)
                .first()
            )

            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Crop category name already exists",
                )

        for key, value in update_data.items():
            setattr(obj, key, value)

        db.commit()
        db.refresh(obj)

        return obj

    # ------------------------------------------------------
    # DELETE
    # ------------------------------------------------------
    def delete(self, db: Session, obj_id: int):
        obj = self.get(db, obj_id)

        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Crop category not found",
            )

        db.delete(obj)
        db.commit()

        return None
