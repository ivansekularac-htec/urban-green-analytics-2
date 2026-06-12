from pydantic import BaseModel, ConfigDict


class TimestampResponse(BaseModel):
    """Base response schema containing audit and identification fields."""

    id: int
    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)
