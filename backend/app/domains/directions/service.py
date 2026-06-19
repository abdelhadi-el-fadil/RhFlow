"""
Service — "directions" domain.

Contains CRUD operations with soft-delete filtering and audit population.
"""
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.schemas import PaginationParams
from app.domains.directions.exceptions import (
    DirectionCodeAlreadyExistsException,
    DirectionsNotFoundException,
)
from app.domains.directions.model import Direction
from app.domains.users.model import User


def create_direction(
    db: Session, payload: dict[str, Any], current_user: User
) -> Direction:
    existing = db.scalars(
        select(Direction).where(Direction.code == payload["code"])
    ).first()
    if existing is not None:
        raise DirectionCodeAlreadyExistsException()

    direction = Direction(
        name=payload.get("name"),
        code=payload.get("code"),
        description=payload.get("description"),
        director_id=payload.get("director_id"),
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
    db: Session, direction_id: int, payload: dict[str, Any], current_user: User
) -> Direction:
    direction = get_direction(db, direction_id)

    new_code: str | None = payload.get("code")
    if new_code is not None and new_code != direction.code:
        existing = db.scalars(
            select(Direction).where(Direction.code == new_code)
        ).first()
        if existing is not None:
            raise DirectionCodeAlreadyExistsException()
        direction.code = new_code

    new_name: str | None = payload.get("name")
    if new_name is not None:
        direction.name = new_name

    if "description" in payload:
        direction.description = payload.get("description")

    if "director_id" in payload:
        direction.director_id = payload.get("director_id")

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