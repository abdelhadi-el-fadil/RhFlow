"""
Test infrastructure — SQLite in-memory DB + FastAPI TestClient.

- Base.metadata.create_all(...) ne doit exister QUE ici (voir CLAUDE.md).
- app.dependency_overrides[get_db] échange Postgres par SQLite sans
  toucher au code métier — c'est la dependency inversion en action.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.enums import UserRole
from app.core.security import hash_password
from app.database import get_db
from app.domains.users.model import User
from app.main import app
from app.models.base import Base

# ── SQLite in-memory ───────────────────────────────────────────────────────
# StaticPool = une seule connexion partagée → TestClient (thread séparé)
# voit la même DB que les fixtures. Sans ça, la DB paraît vide.
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(engine)  # UNIQUE endroit autorisé (voir CLAUDE.md)


# ── Override FastAPI ───────────────────────────────────────────────────────
def override_get_db():
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
def db():
    db = TestingSessionLocal()
    yield db
    db.rollback()
    db.close()


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def make_user(db):
    """
    Factory — crée et persiste un User en base.

    Exemples :
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