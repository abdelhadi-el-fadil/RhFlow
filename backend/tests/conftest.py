"""
Test infrastructure — SQLite in-memory DB + FastAPI TestClient.

- Base.metadata.create_all(...) must exist HERE ONLY (see CLAUDE.md).
- app.dependency_overrides[get_db] swaps Postgres for SQLite without
  touching any business logic — dependency inversion in action.
"""
from collections.abc import Callable, Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.enums import UserRole
from app.core.security import hash_password
from app.database import get_db
from app.domains.users.model import User
from app.main import app
from app.models.base import Base

# ── SQLite in-memory ───────────────────────────────────────────────────────
# StaticPool = single shared connection → TestClient (separate thread)
# sees the same DB as fixtures. Without it the DB appears empty.
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(engine)  # ONLY place this is allowed (see CLAUDE.md)


# ── Override FastAPI ───────────────────────────────────────────────────────
def override_get_db() -> Generator[Session, None, None]:
    db = TestingSessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db


# ── Fixtures ───────────────────────────────────────────────────────────────
@pytest.fixture()
def db() -> Generator[Session, None, None]:
    db = TestingSessionLocal()
    yield db
    db.rollback()
    db.close()


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def make_user(db: Session) -> Callable[..., User]:
    """
    Factory — create and persist a User in the database.

    Examples:
        make_user("alice@test.com", "Secret123!")
        make_user("bob@test.com",   "Secret123!", role=UserRole.ADMIN)
        make_user("eve@test.com",   "Secret123!", enabled=False)
        make_user("del@test.com",   "Secret123!", is_deleted=True)
    """
    def _make(
        email: str,
        password: str,
        role: UserRole = UserRole.DRH,
        enabled: bool = True,
        is_deleted: bool = False,
    ) -> User:
        user = User(
            email=email,
            hashed_password=hash_password(password),
            role=role,
            enabled=enabled,
            is_deleted=is_deleted,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    return _make