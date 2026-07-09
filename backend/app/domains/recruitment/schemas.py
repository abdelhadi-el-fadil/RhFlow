"""Pydantic schemas — recruitment domain."""
from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from app.domains.recruitment.enums import BesoinPriority, BesoinStatus, ProjetStatus


class BesoinRecrutementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    positions_count: int | None
    desired_date: date | None
    justification: str | None
    location: str | None = None
    recruitment_reason: str | None = None
    priority: BesoinPriority
    status: BesoinStatus
    rejection_reason: str | None
    fiche_de_poste_id: int
    fiche_title: str | None = None
    direction_name: str | None = None
    director_name: str | None = None
    requester_name: str | None = None
    submitted_by_id: int | None
    processed_by_id: int | None
    projet_id: int | None
    created_by_id: int | None
    updated_by_id: int | None


class BesoinRecrutementCreate(BaseModel):
    title: str | None = None
    location: str
    recruitment_reason: str
    priority: BesoinPriority
    positions_count: int = Field(ge=1)
    desired_date: date
    fiche_de_poste_id: int
    projet_id: int | None = None


class BesoinRecrutementUpdate(BaseModel):
    title: str | None = None
    location: str | None = None
    recruitment_reason: str | None = None
    priority: BesoinPriority | None = None
    positions_count: int | None = None
    desired_date: date | None = None
    fiche_de_poste_id: int | None = None


class RejectBesoinRequest(BaseModel):
    reason: str = Field(min_length=10)


class ProjetRecrutementCreate(BaseModel):
    title: str
    description: str | None = None
    start_date: date
    expected_end_date: date
    status: ProjetStatus = ProjetStatus.DRAFT
    manager_id: int
    besoin_recrutement_id: int | None = None
    fiche_de_poste_id: int | None = None
    nombre_postes: int | None = Field(default=None, ge=1)


class ProjetRecrutementUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    start_date: date | None = None
    expected_end_date: date | None = None
    status: ProjetStatus | None = None
    manager_id: int | None = None
    besoin_recrutement_id: int | None = None
    fiche_de_poste_id: int | None = None
    nombre_postes: int | None = Field(default=None, ge=1)
    email_subject: str | None = None


class ProjetRecrutementCardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    start_date: date
    status: ProjetStatus
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
    description: str | None
    start_date: date
    expected_end_date: date
    manager_id: int
    manager_name: str | None = None
    status: ProjetStatus
    besoin_recrutement_id: int | None
    besoin_title: str | None = None
    fiche_de_poste_id: int | None
    fiche_title: str | None = None
    nombre_postes: int | None
    email_subject: str | None = None
    direction_name: str | None = None
    director_name: str | None = None
    created_by_id: int | None
    updated_by_id: int | None
    besoins: list[BesoinRecrutementResponse] = Field(default_factory=list)
