"""Pydantic schemas — recruitment domain."""
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domains.recruitment.enums import BesoinPriority, BesoinStatus, ProjetStatus


class BesoinRecrutementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lieu_affectation: str
    positions_count: int | None
    desired_date: date | None
    justification: str | None
    priority: BesoinPriority
    status: BesoinStatus
    fiche_de_poste_id: int
    fiche_title: str | None = None
    direction_name: str | None = None
    director_name: str | None = None
    requester_name: str | None = None
    submitted_by_id: int | None
    processed_by_id: int | None
    created_by_id: int | None
    updated_by_id: int | None


class BesoinRecrutementCreate(BaseModel):
    lieu_affectation: str
    recruitment_reason: str
    priority: BesoinPriority
    positions_count: int = Field(ge=1)
    desired_date: date
    fiche_de_poste_id: int


class BesoinRecrutementUpdate(BaseModel):
    lieu_affectation: str | None = None
    recruitment_reason: str | None = None
    priority: BesoinPriority | None = None
    positions_count: int | None = None
    desired_date: date | None = None
    fiche_de_poste_id: int | None = None


class RejectBesoinRequest(BaseModel):
    reason: str = Field(min_length=10)


class ProjetRecrutementCreate(BaseModel):
    manager_id: int | None = None
    besoin_recrutement_id: int
    email_subject: str | None = None


class ProjetRecrutementUpdate(BaseModel):
    status: ProjetStatus | None = None
    manager_id: int | None = None
    email_subject: str | None = None


class ProjetRecrutementCardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    status: ProjetStatus
    besoin_recrutement_id: int
    nombre_postes: int | None
    direction_name: str | None
    director_name: str | None
    manager_name: str | None
    fiche_title: str | None
    besoin_title: str | None
    email_subject: str | None


class ProjetRecrutementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    manager_id: int
    manager_name: str | None = None
    status: ProjetStatus
    besoin_recrutement_id: int
    besoin_title: str | None = None
    fiche_title: str | None = None
    nombre_postes: int | None
    email_subject: str | None = None
    direction_name: str | None = None
    director_name: str | None = None
    archived_at: datetime | None = None
    created_by_id: int | None
    updated_by_id: int | None
