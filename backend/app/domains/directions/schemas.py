"""
Pydantic schemas — "directions" domain.
"""
from pydantic import BaseModel, ConfigDict


class DirectionCreate(BaseModel):
    name: str
    code: str
    description: str | None = None
    director_id: int | None = None


class DirectionUpdate(BaseModel):
    name: str | None = None
    code: str | None = None
    description: str | None = None
    director_id: int | None = None


class DirectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str
    description: str | None
    director_id: int | None
    created_by_id: int | None
    updated_by_id: int | None
    is_deleted: bool
