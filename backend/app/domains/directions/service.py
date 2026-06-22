"""
Service — "directions" domain.

Contains CRUD operations with soft-delete filtering and audit population.
"""
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.schemas import PaginationParams
from app.domains.directions.exceptions import (
    DirectionCodeAlreadyExistsException,
    DirectionsNotFoundException,
)
from app.domains.directions.model import Direction
from app.domains.directions.schemas import DirectionCreate, DirectionUpdate
from app.domains.users.model import User


def create_direction(
    db: Session, payload: DirectionCreate, current_user: User
) -> Direction:
    existing = db.scalars(
        select(Direction).where(Direction.code == payload.code)
    ).first()
    if existing is not None:
        raise DirectionCodeAlreadyExistsException()

    direction = Direction(
        name=payload.name,
        code=payload.code,
        description=payload.description,
        director_id=payload.director_id,
        created_by_id=current_user.id,
        updated_by_id=current_user.id,
    )
    db.add(direction)
    db.flush()
    db.refresh(direction)
    return direction


def get_direction(db: Session, direction_id: int) -> Direction:
    direction = db.scalars(
        select(Direction).where(
            Direction.id == direction_id,
            Direction.is_deleted.is_(False),
        )
    ).first()
    if direction is None:
        raise DirectionsNotFoundException()
    return direction


def list_directions(
    db: Session, params: PaginationParams
) -> tuple[list[Direction], int]:
    base_query = (
        select(Direction)
        .where(Direction.is_deleted.is_(False))
        .order_by(Direction.id)
    )
    items = list(
        db.scalars(base_query.offset(params.offset).limit(params.page_size)).all()
    )
    total_items = db.scalar(
        select(func.count())
        .select_from(Direction)
        .where(Direction.is_deleted.is_(False))
    )
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