from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

"""
Commit or 409

This helper function provides commit or raises exception
"""


def commit_or_409(db):
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Database constraint violation",
        ) from exc
