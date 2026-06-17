"""
CRUD operations for infrastructure types.

This module provides functions for creating and retrieving
infrastructure type records from the database.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crud.helpers import commit_or_409
from app.models.farms.infrastructure_type import InfrastructureType
from app.schemas.farms.infrastructure_type import InfrastructureTypeCreate


def create(
    db: Session,
    payload: InfrastructureTypeCreate,
) -> InfrastructureType:
    """
    Create a new infrastructure type.

    Args:
        db: Active database session.
        payload: Infrastructure type data used to create the record.

    Returns:
        The newly created infrastructure type instance.
    """

    obj = InfrastructureType(**payload.model_dump())

    db.add(obj)
    commit_or_409(db)
    db.refresh(obj)

    return obj


def get(
    db: Session,
    infrastructure_type_id: int,
) -> InfrastructureType | None:
    """
    Retrieve an infrastructure type by its ID.

    Args:
        db: Active database session.
        infrastructure_type_id: Unique identifier of the infrastructure type.

    Returns:
        The infrastructure type instance if found, otherwise None.
    """

    return db.get(InfrastructureType, infrastructure_type_id)


def get_all(
    db: Session,
    skip: int,
    limit: int,
) -> list[InfrastructureType]:
    """
    Retrieve all infrastructure types.

    Args:
        db: Active database session.

    Returns:
        A list of all infrastructure type records.
    """

    stmt = select(InfrastructureType).offset(skip).limit(limit)

    return db.scalars(stmt).all()
