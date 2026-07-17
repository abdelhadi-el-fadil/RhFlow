"""
Pydantic schemas — "directions" domain.
"""

from pydantic import BaseModel, ConfigDict, Field


class DirectionCreate(BaseModel):
    name: str = Field(max_length=150)
    code: str | None = Field(default=None, max_length=20)
    description: str | None = None
    director_id: int | None = None


class DirectionUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=150)
    code: str | None = Field(default=None, max_length=20)
    description: str | None = None
    director_id: int | None = None


class DirectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str
    description: str | None
    director_id: int | None
    director_name: str | None
    fiche_count: int
    created_by_id: int | None
    updated_by_id: int | None
