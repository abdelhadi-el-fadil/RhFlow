"""
Service — "users" domain.

Holds user account business logic: CRUD operations, soft delete, and
read filters that enforce "not deleted" in one place.
"""
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.enums import UserRole
from app.core.schemas import PaginationParams
from app.core.security import hash_password
from app.domains.users.exceptions import (
    EmailAlreadyExistsException,
    UserNotFoundException,
)
from app.domains.users.model import User


def create_user(
    db: Session,
    email: str,
    password: str,
    full_name: str | None,
    gsm: str | None,
    role: UserRole,
) -> User:
    existing = db.scalars(
        select(User).where(
            User.email == email,
            User.is_deleted.is_(False),
        )
    ).first()
    if existing is not None:
        raise EmailAlreadyExistsException()

    user = User(
        email=email,
        hashed_password=hash_password(password),
        full_name=full_name,
        gsm=gsm,
        role=role,
    )
    db.add(user)
    db.flush()
    db.refresh(user)
    return user


def get_user(db: Session, user_id: int) -> User:
    user = db.scalars(
        select(User).where(User.id == user_id, User.is_deleted.is_(False))
    ).first()
    if user is None:
        raise UserNotFoundException()
    return user


def list_users(db: Session, params: PaginationParams) -> tuple[list[User], int]:
    base_query = select(User).where(User.is_deleted.is_(False)).order_by(User.id)
    items = list(db.scalars(
        base_query.offset(params.offset).limit(params.page_size)
    ).all())
    total_items = db.scalar(
        select(func.count()).select_from(User).where(User.is_deleted.is_(False))
    )
    return items, int(total_items or 0)


def update_user(
    db: Session,
    user_id: int,
    email: str | None = None,
    password: str | None = None,
    full_name: str | None = None,
    gsm: str | None = None,
    role: UserRole | None = None,
    enabled: bool | None = None,
) -> User:
    user = get_user(db, user_id)

    if email is not None and email != user.email:
        existing = db.scalars(select(User).where(User.email == email)).first()
        if existing is not None:
            raise EmailAlreadyExistsException()
        user.email = email

    if password is not None:
        user.hashed_password = hash_password(password)

    if full_name is not None:
        user.full_name = full_name

    if gsm is not None:
        user.gsm = gsm

    if role is not None:
        user.role = UserRole(role)

    if enabled is not None:
        user.enabled = enabled

    db.add(user)
    db.flush()
    db.refresh(user)
    return user


def soft_delete_user(db: Session, user_id: int) -> User:
    user = get_user(db, user_id)
    user.is_deleted = True
    user.deleted_at = datetime.now(timezone.utc)
    db.add(user)
    db.flush()
    return user
