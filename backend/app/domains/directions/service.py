"""
Service — "directions" domain.

Contains CRUD operations with soft-delete filtering and audit population.
"""

import re
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.enums import UserRole
from app.core.exceptions import ForbiddenException
from app.core.schemas import PaginationParams
from app.domains.directions.exceptions import (
    DirectionCodeAlreadyExistsException,
    DirectionsNotFoundException,
)
from app.domains.directions.model import Direction
from app.domains.directions.schemas import DirectionCreate, DirectionUpdate
from app.domains.users.model import User


def _normalize_direction_code(name: str) -> str:
    collapsed = re.sub(r"[^A-Za-z0-9]+", "-", name).strip("-").upper()
    return (collapsed or "DIRECTION")[:20]


def _generate_direction_code(db: Session, name: str) -> str:
    base_code = _normalize_direction_code(name)
    candidate = base_code
    suffix = 1

    while (
        db.scalars(select(Direction).where(Direction.code == candidate)).first()
        is not None
    ):
        suffix_str = f"-{suffix}"
        candidate = f"{base_code[: max(1, 20 - len(suffix_str))]}{suffix_str}"
        suffix += 1

    return candidate


def create_direction(
    db: Session, payload: DirectionCreate, current_user: User
) -> Direction:
    code = payload.code or _generate_direction_code(db, payload.name)
    existing = db.scalars(select(Direction).where(Direction.code == code)).first()
    if existing is not None:
        raise DirectionCodeAlreadyExistsException()

    direction = Direction(
        name=payload.name,
        code=code,
        description=payload.description,
        director_id=payload.director_id,
        created_by_id=current_user.id,
        updated_by_id=current_user.id,
    )
    db.add(direction)
    db.flush()
    db.refresh(direction)
    return direction


def get_direction(
    db: Session,
    direction_id: int,
    current_user: User | None = None,
) -> Direction:
    direction = db.scalars(
        select(Direction)
        .options(selectinload(Direction.director), selectinload(Direction.fiches))
        .where(
            Direction.id == direction_id,
            Direction.is_deleted.is_(False),
        )
    ).first()
    if direction is None:
        raise DirectionsNotFoundException()
    if (
        current_user is not None
        and current_user.role == UserRole.DIRECTEUR
        and direction.director_id != current_user.id
    ):
        raise ForbiddenException()
    return direction


def list_directions(
    db: Session,
    params: PaginationParams,
    current_user: User,
) -> tuple[list[Direction], int]:
    base_query = (
        select(Direction)
        .options(selectinload(Direction.director), selectinload(Direction.fiches))
        .where(Direction.is_deleted.is_(False))
    )

    if current_user.role == UserRole.DIRECTEUR:
        base_query = base_query.where(Direction.director_id == current_user.id)

    base_query = base_query.order_by(Direction.id)

    items = list(
        db.scalars(base_query.offset(params.offset).limit(params.page_size)).all()
    )
    count_query = (
        select(func.count())
        .select_from(Direction)
        .where(Direction.is_deleted.is_(False))
    )

    if current_user.role == UserRole.DIRECTEUR:
        count_query = count_query.where(Direction.director_id == current_user.id)

    total_items = db.scalar(count_query)
    return items, int(total_items or 0)


def update_direction(
    db: Session, direction_id: int, payload: DirectionUpdate, current_user: User
) -> Direction:
    direction = get_direction(db, direction_id)

    if payload.code is not None and payload.code != direction.code:
        existing = db.scalars(
            select(Direction).where(Direction.code == payload.code)
        ).first()
        if existing is not None:
            raise DirectionCodeAlreadyExistsException()
        direction.code = payload.code

    if payload.name is not None:
        direction.name = payload.name

    if payload.description is not None:
        direction.description = payload.description

    if payload.director_id is not None:
        direction.director_id = payload.director_id

    direction.updated_by_id = current_user.id
    db.add(direction)
    db.flush()
    db.refresh(direction)
    return direction


def soft_delete_direction(db: Session, direction_id: int) -> Direction:
    direction = get_direction(db, direction_id)
    direction.is_deleted = True
    direction.deleted_at = datetime.now(timezone.utc)
    db.add(direction)
    db.flush()
    return direction
