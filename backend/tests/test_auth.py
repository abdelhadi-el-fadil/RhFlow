"""
Tests complets — domaine auth.

Chaque nom de test EST la spécification du comportement attendu.

Note sur require_role : on teste via une route protégée créée inline
dans le fichier de test avec app.include_router — pas besoin de modifier
le vrai router.py.
"""
from collections.abc import Callable
from datetime import timedelta

import jwt
from fastapi import APIRouter, Depends
from fastapi.testclient import TestClient

from app.config import settings
from app.core.codes import ErrorCode
from app.core.dependencies import require_role
from app.core.enums import UserRole
from app.core.security import create_access_token
from app.domains.users.model import User
from app.main import app

# ── Route temporaire pour tester require_role ──────────────────────────────
# On ajoute une route ADMIN-only directement ici, sans toucher à router.py.
# C'est une pratique standard : tester une dépendance via une route dédiée.
_test_router = APIRouter()

@_test_router.get("/test-admin-only")
def admin_only(_: User = Depends(require_role(UserRole.ADMIN))) -> dict[str, bool]:
    return {"ok": True}

app.include_router(_test_router)


# ── POST /auth/login ───────────────────────────────────────────────────────

def test_login_valid_credentials_returns_200_and_token(
    client: TestClient,
    make_user: Callable[..., User],
) -> None:
    make_user("alice@test.com", "Secret123!")
    r = client.post(
        "/auth/login",
        data={"username": "alice@test.com", "password": "Secret123!"},
    )
    assert r.status_code == 200
    assert "access_token" in r.json()["data"]


def test_login_wrong_password_returns_401_with_code(
    client: TestClient,
    make_user: Callable[..., User],
) -> None:
    make_user("bob@test.com", "Secret123!")
    r = client.post(
        "/auth/login",
        data={"username": "bob@test.com", "password": "MAUVAIS"},
    )
    assert r.status_code == 401
    assert r.json()["code"] == "AUTH_INVALID_CREDENTIALS"


def test_login_unknown_email_returns_401_same_code_as_wrong_password(
    client: TestClient,
) -> None:
    """Anti-énumération : email inconnu → même code qu'un mauvais mot de passe."""
    r = client.post(
        "/auth/login",
        data={"username": "ghost@test.com", "password": "Secret123!"},
    )
    assert r.status_code == 401
    assert r.json()["code"] == "AUTH_INVALID_CREDENTIALS"


def test_login_deleted_user_returns_401(
    client: TestClient,
    make_user: Callable[..., User],
) -> None:
    """Prouve TICKET-026 : soft-delete exclut l'utilisateur de l'auth."""
    make_user("deleted@test.com", "Secret123!", is_deleted=True)
    r = client.post(
        "/auth/login",
        data={"username": "deleted@test.com", "password": "Secret123!"},
    )
    assert r.status_code == 401
    assert r.json()["code"] == "AUTH_INVALID_CREDENTIALS"


def test_login_disabled_user_returns_401(
    client: TestClient,
    make_user: Callable[..., User],
) -> None:
    """Prouve TICKET-026 : compte désactivé → même erreur vague (anti-énumération)."""
    make_user("disabled@test.com", "Secret123!", enabled=False)
    r = client.post(
        "/auth/login",
        data={"username": "disabled@test.com", "password": "Secret123!"},
    )
    assert r.status_code == 401
    assert r.json()["code"] == "AUTH_INVALID_CREDENTIALS"


# ── GET /auth/me ───────────────────────────────────────────────────────────

def test_me_without_token_returns_401(client: TestClient) -> None:
    r = client.get("/auth/me")
    assert r.status_code == 401


def test_me_with_valid_token_returns_200_email_correct_and_no_hashed_password(
    client: TestClient,
    make_user: Callable[..., User],
) -> None:
    """hashed_password ne doit JAMAIS apparaître dans la réponse."""
    make_user("eve@test.com", "Secret123!")
    login = client.post(
        "/auth/login",
        data={"username": "eve@test.com", "password": "Secret123!"},
    )
    token = login.json()["data"]["access_token"]

    r = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    body = r.json()["data"]
    assert body["email"] == "eve@test.com"
    assert "hashed_password" not in body          # sécurité : ne jamais exposer le hash


def test_me_with_expired_token_returns_401_with_code(
    client: TestClient,
    make_user: Callable[..., User],
) -> None:
    """Token expiré depuis 1 seconde → AUTH_TOKEN_EXPIRED."""
    user = make_user("frank@test.com", "Secret123!")
    expired_token = create_access_token(
        subject=user.id,
        extra_claims={"role": user.role.value, "email": user.email},
        expires_delta=timedelta(seconds=-1),   # déjà expiré
    )
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert r.status_code == 401
    assert r.json()["code"] == "AUTH_TOKEN_EXPIRED"


def test_me_with_wrong_signature_returns_401_with_code(
    client: TestClient,
    make_user: Callable[..., User],
) -> None:
    """Token signé avec une autre clé → AUTH_INVALID_TOKEN."""
    user = make_user("grace@test.com", "Secret123!")
    bad_token = jwt.encode(
        {"sub": str(user.id), "role": user.role.value, "email": user.email},
        key="cle-secrete-differente",
        algorithm=settings.ALGORITHM,
    )
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {bad_token}"})
    assert r.status_code == 401
    assert r.json()["code"] == "AUTH_INVALID_TOKEN"


# ── require_role ───────────────────────────────────────────────────────────

def test_require_role_wrong_role_returns_403_with_code(
    client: TestClient,
    make_user: Callable[..., User],
) -> None:
    """User DRH tente d'accéder à une route ADMIN-only → 403 FORBIDDEN."""
    make_user("henry@test.com", "Secret123!", role=UserRole.DRH)
    login = client.post(
        "/auth/login",
        data={"username": "henry@test.com", "password": "Secret123!"},
    )
    token = login.json()["data"]["access_token"]

    r = client.get("/test-admin-only", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403
    assert r.json()["code"] == ErrorCode.FORBIDDEN