"""Pydantic schemas — fiches de poste domain."""
from pydantic import BaseModel, ConfigDict

from app.domains.fiches_de_poste.enums import FicheStatus


class FicheDePosteCreate(BaseModel):
    title: str
    description: str
    missions: str
    required_skills: str
    experience_level: str
    direction_id: int


class FicheDePosteUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    missions: str | None = None
    required_skills: str | None = None
    experience_level: str | None = None
    direction_id: int | None = None


class FicheDePosteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    missions: str
    required_skills: str
    experience_level: str
    status: FicheStatus
    direction_id: int
    validated_by_id: int | None
    created_by_id: int | None
    updated_by_id: int | None
