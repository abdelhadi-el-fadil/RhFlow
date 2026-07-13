"""Pydantic schemas — fiches de poste domain."""
from pydantic import BaseModel, ConfigDict


class FicheDePosteCreate(BaseModel):
    title: str
    main_activities: str
    missions: str
    required_skills: str
    experience_level: str
    direction_id: int
    formation_domain: str | None = None
    education_level: str | None = None
    technical_skills: str | None = None
    managerial_skills: str | None = None


class FicheDePosteUpdate(BaseModel):
    title: str | None = None
    main_activities: str | None = None
    missions: str | None = None
    required_skills: str | None = None
    experience_level: str | None = None
    direction_id: int | None = None
    formation_domain: str | None = None
    education_level: str | None = None
    technical_skills: str | None = None
    managerial_skills: str | None = None


class FicheDePosteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    main_activities: str
    missions: str
    required_skills: str
    experience_level: str
    formation_domain: str | None
    education_level: str | None
    technical_skills: str | None
    managerial_skills: str | None
    direction_id: int
    direction_name: str | None
    validated_by_id: int | None
    created_by_id: int | None
    updated_by_id: int | None
