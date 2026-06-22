"""Pydantic schemas — offres domain."""
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.domains.offres.enums import OffreStatus


class OffreCreate(BaseModel):
    title: str
    description: str | None = None
    requirements: str | None = None
    deadline: date | None = None
    besoin_id: int


class OffreResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    requirements: str | None
    published_at: datetime | None
    deadline: date | None
    status: OffreStatus
    besoin_id: int
    published_by_id: int | None
    created_by_id: int | None
    updated_by_id: int | None
    is_deleted: bool


class OffrePublicResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    title: str
    description: str | None
    requirements: str | None
    published_at: datetime | None
    deadline: date | None
