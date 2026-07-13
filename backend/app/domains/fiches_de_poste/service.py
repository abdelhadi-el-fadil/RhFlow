"""Service — fiches de poste domain."""
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.sql import Select

from app.core.enums import UserRole
from app.core.exceptions import ForbiddenException
from app.core.schemas import PaginationParams
from app.domains.directions.service import get_direction
from app.domains.fiches_de_poste.exceptions import (
    FicheDePosteNotFoundException,
)
from app.domains.fiches_de_poste.model import FicheDePoste
from app.domains.fiches_de_poste.schemas import FicheDePosteCreate, FicheDePosteUpdate
from app.domains.users.model import User


def _apply_filters(
    stmt: Select[Any],
    direction_id: int | None,
) -> Select[Any]:
    if direction_id is not None:
        stmt = stmt.where(FicheDePoste.direction_id == direction_id)
    return stmt


def create_fiche(
    db: Session,
    payload: FicheDePosteCreate,
    current_user: User,
) -> FicheDePoste:
    direction = get_direction(db, payload.direction_id)
    if (
        current_user.role == UserRole.DIRECTEUR 
        and direction.director_id != current_user.id
        ):
        raise ForbiddenException()

    fiche = FicheDePoste(
        title=payload.title,
        main_activities=payload.main_activities,
        missions=payload.missions,
        required_skills=payload.required_skills,
        experience_level=payload.experience_level,
        direction_id=payload.direction_id,
        formation_domain=payload.formation_domain,
        education_level=payload.education_level,
        technical_skills=payload.technical_skills,
        managerial_skills=payload.managerial_skills,
        created_by_id=current_user.id,
        updated_by_id=current_user.id,
    )
    db.add(fiche)
    db.flush()
    db.refresh(fiche)
    return fiche


def get_fiche(db: Session, fiche_id: int) -> FicheDePoste:
    fiche = db.scalars(
        select(FicheDePoste)
        .options(selectinload(FicheDePoste.direction))
        .where(
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
    direction_id: int | None = None,
) -> tuple[list[FicheDePoste], int]:
    base_query = _apply_filters(
        select(FicheDePoste)
        .options(selectinload(FicheDePoste.direction))
        .where(FicheDePoste.is_deleted.is_(False)),
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

    elevated_editor = current_user.role in {UserRole.ADMIN, UserRole.DRH}
    is_directeur = current_user.role == UserRole.DIRECTEUR

    if not elevated_editor and not is_directeur:
        raise ForbiddenException()

    if is_directeur:
        current_direction = get_direction(db, fiche.direction_id)
        if current_direction.director_id != current_user.id:
            raise ForbiddenException()

    payload_data = payload.model_dump(exclude_unset=True)
    if "direction_id" in payload_data and payload_data["direction_id"] is not None:
        next_direction = get_direction(db, payload_data["direction_id"])
        if is_directeur and next_direction.director_id != current_user.id:
            raise ForbiddenException()

    for field_name, field_value in payload_data.items():
        setattr(fiche, field_name, field_value)

    fiche.updated_by_id = current_user.id
    db.add(fiche)
    db.flush()
    db.refresh(fiche)
    return fiche


def delete_fiche(db: Session, fiche_id: int, current_user: User) -> FicheDePoste:
    fiche = get_fiche(db, fiche_id)

    elevated_editor = current_user.role in {UserRole.ADMIN, UserRole.DRH}
    if not elevated_editor:
        raise ForbiddenException()

    fiche.is_deleted = True
    fiche.deleted_at = datetime.now(timezone.utc)
    fiche.updated_by_id = current_user.id
    db.add(fiche)
    db.flush()
    return fiche
