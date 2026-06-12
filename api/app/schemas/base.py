from pydantic import BaseModel, ConfigDict


class BaseResponse(BaseModel):
    """
    Base schema for API responses.

    Provides fields common to all response models:
    - id: Unique record identifier.
    - created_at: Unix timestamp when the record was created.
    - updated_at: Unix timestamp when the record was last updated.

    The `from_attributes=True` configuration allows Pydantic
    to create response objects directly from SQLAlchemy ORM models.
    """

    id: int
    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)
