"""Service — fiches de poste domain."""
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select

from app.core.exceptions import ForbiddenException
from app.core.schemas import PaginationParams
from app.domains.directions.service import get_direction
from app.domains.fiches_de_poste.enums import FicheStatus
from app.domains.fiches_de_poste.exceptions import (
    FicheDePosteInvalidTransitionException,
    FicheDePosteNotFoundException,
)
from app.domains.fiches_de_poste.model import FicheDePoste
from app.domains.fiches_de_poste.schemas import FicheDePosteCreate, FicheDePosteUpdate
from app.domains.users.model import User


def _apply_filters(
    stmt: Select[Any],
    status: FicheStatus | None,
    direction_id: int | None,
) -> Select[Any]:
    if status is not None:
        stmt = stmt.where(FicheDePoste.status == status)
    if direction_id is not None:
        stmt = stmt.where(FicheDePoste.direction_id == direction_id)
    return stmt


def create_fiche(
    db: Session,
    payload: FicheDePosteCreate,
    current_user: User,
) -> FicheDePoste:
    get_direction(db, payload.direction_id)

    fiche = FicheDePoste(
        title=payload.title,
        description=payload.description,
        missions=payload.missions,
        required_skills=payload.required_skills,
        experience_level=payload.experience_level,
        direction_id=payload.direction_id,
        status=FicheStatus.DRAFT,
        created_by_id=current_user.id,
        updated_by_id=current_user.id,
    )
    db.add(fiche)
    db.flush()
    db.refresh(fiche)
    return fiche


def get_fiche(db: Session, fiche_id: int) -> FicheDePoste:
    fiche = db.scalars(
        select(FicheDePoste).where(
            FicheDePoste.id == fiche_id,
            FicheDePoste.is_deleted.is_(False),
        )
    ).first()
    if fiche is None:
        raise FicheDePosteNotFoundException()
    return fiche


def list_fiches(
    db: Session,
    params: PaginationParams,
    status: FicheStatus | None = None,
    direction_id: int | None = None,
) -> tuple[list[FicheDePoste], int]:
    base_query = _apply_filters(
        select(FicheDePoste).where(FicheDePoste.is_deleted.is_(False)),
        status,
        direction_id,
    ).order_by(FicheDePoste.id)
    items = list(
        db.scalars(
            base_query.offset(params.offset).limit(params.page_size)
        ).all()
    )

    count_query = _apply_filters(
        select(func.count()).select_from(FicheDePoste).where(
            FicheDePoste.is_deleted.is_(False)
        ),
        status,
        direction_id,
    )
    total_items = db.scalar(count_query)
    return items, int(total_items or 0)


def update_fiche(
    db: Session,
    fiche_id: int,
    payload: FicheDePosteUpdate,
    current_user: User,
) -> FicheDePoste:
    fiche = get_fiche(db, fiche_id)

    if fiche.created_by_id != current_user.id:
        raise ForbiddenException()
    if fiche.status != FicheStatus.DRAFT:
        raise FicheDePosteInvalidTransitionException()

    payload_data = payload.model_dump(exclude_unset=True)
    if "direction_id" in payload_data and payload_data["direction_id"] is not None:
        get_direction(db, payload_data["direction_id"])

    for field_name, field_value in payload_data.items():
        setattr(fiche, field_name, field_value)

    fiche.updated_by_id = current_user.id
    db.add(fiche)
    db.flush()
    db.refresh(fiche)
    return fiche


def validate_fiche(db: Session, fiche_id: int, current_user: User) -> FicheDePoste:
    fiche = get_fiche(db, fiche_id)
    if fiche.status != FicheStatus.DRAFT:
        raise FicheDePosteInvalidTransitionException()

    fiche.status = FicheStatus.VALIDATED
    fiche.validated_by_id = current_user.id
    fiche.updated_by_id = current_user.id
    db.add(fiche)
    db.flush()
    db.refresh(fiche)
    return fiche


def archive_fiche(db: Session, fiche_id: int, current_user: User) -> FicheDePoste:
    fiche = get_fiche(db, fiche_id)
    if fiche.status != FicheStatus.VALIDATED:
        raise FicheDePosteInvalidTransitionException()

    fiche.status = FicheStatus.ARCHIVED
    fiche.updated_by_id = current_user.id
    db.add(fiche)
    db.flush()
    db.refresh(fiche)
    return fiche
