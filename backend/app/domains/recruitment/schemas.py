"""Pydantic schemas — recruitment domain."""
from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from app.domains.recruitment.enums import BesoinStatus, ProjetStatus


class BesoinRecrutementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    positions_count: int | None
    desired_date: date | None
    justification: str | None
    status: BesoinStatus
    rejection_reason: str | None
    fiche_de_poste_id: int
    submitted_by_id: int | None
    processed_by_id: int | None
    projet_id: int | None
    created_by_id: int | None
    updated_by_id: int | None
    is_deleted: bool


class BesoinRecrutementCreate(BaseModel):
    title: str
    description: str | None = None
    positions_count: int | None = None
    desired_date: date | None = None
    justification: str | None = None
    fiche_de_poste_id: int
    projet_id: int | None = None


class BesoinRecrutementUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    positions_count: int | None = None
    desired_date: date | None = None
    justification: str | None = None
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


class ProjetRecrutementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    start_date: date
    expected_end_date: date
    status: ProjetStatus
    manager_id: int
    created_by_id: int | None
    updated_by_id: int | None
    besoins: list[BesoinRecrutementResponse] = Field(default_factory=list)
