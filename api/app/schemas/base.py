from pydantic import BaseModel, ConfigDict

class AuditModelBase(BaseModel):
    id: int
    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)