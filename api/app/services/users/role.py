"""
Service layer for Role.

Handles business logic and database operations for user roles.

Ensures data integrity and uniqueness constraints.
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.users.role import Role
from app.schemas.users.role import (
    RoleCreate,
    RoleUpdate,
)


class RoleService:
    # -------------------------------------------------
    # READ
    # -------------------------------------------------

    def get(self, db: Session, role_id: int):
        """
        Retrieve a single Role by ID.

        Args:
            db (Session): Active DB session.
            role_id (int): Role ID.

        Returns:
            Role: Requested entity.

        Raises:
            HTTPException: 404 if role does not exist.
        """

        obj = db.query(Role).filter(Role.id == role_id).first()

        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found",
            )

        return obj

    def get_all(self, db: Session):
        """
        Retrieve all Role records.

        Args:
            db (Session): Active DB session.

        Returns:
            list[Role]: All roles.
        """

        return db.query(Role).all()

    # -------------------------------------------------
    # CREATE
    # -------------------------------------------------

    def create(self, db: Session, data: RoleCreate):
        """
        Create a new Role.

        Ensures role name uniqueness.

        Args:
            db (Session): Active DB session.
            data (RoleCreate): Input payload.

        Returns:
            Role: Created entity.

        Raises:
            HTTPException: 400 if role name already exists.
        """

        existing = db.query(Role).filter(Role.name == data.name).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role with this name already exists",
            )

        obj = Role(**data.model_dump())

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
        role_id: int,
        data: RoleUpdate,
    ):
        """
        Update Role.

        Supports partial updates.

        Args:
            db (Session): Active DB session.
            role_id (int): Role ID.
            data (RoleUpdate): Update payload.

        Returns:
            Role: Updated entity.

        Raises:
            HTTPException: 404 if role does not exist.
            HTTPException: 400 if name already exists.
        """

        obj = self.get(db, role_id)

        update_data = data.model_dump(exclude_unset=True)

        if "name" in update_data:
            existing = (
                db.query(Role)
                .filter(Role.name == update_data["name"])
                .filter(Role.id != role_id)
                .first()
            )

            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Role with this name already exists",
                )

        for key, value in update_data.items():
            setattr(obj, key, value)

        db.commit()
        db.refresh(obj)

        return obj

    # -------------------------------------------------
    # DELETE
    # -------------------------------------------------

    def delete(self, db: Session, role_id: int):
        """
        Delete a Role.

        Args:
            db (Session): Active DB session.
            role_id (int): Role ID.

        Raises:
            HTTPException: 404 if role does not exist.
        """

        obj = self.get(db, role_id)

        db.delete(obj)
        db.commit()
