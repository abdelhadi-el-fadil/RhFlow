"""
Full test suite — auth domain.

Each test name IS the specification of the expected behaviour.

Note on require_role: tested via a throwaway protected route added inline
with app.include_router — no need to touch the real router.py.
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

# ── Throwaway route to test require_role ──────────────────────────────────
# We add an ADMIN-only route inline here, without touching router.py.
# Standard practice: test a dependency through a dedicated test route.
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
    """Anti-enumeration: unknown email → same code as wrong password."""
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
    """Proves TICKET-026: soft-deleted user is excluded from auth."""
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
    """Proves TICKET-026: disabled account → same vague error (anti-enumeration)."""
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
    """hashed_password must NEVER appear in the response."""
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
    assert "hashed_password" not in body  # security: never expose the hash


def test_me_with_expired_token_returns_401_with_code(
    client: TestClient,
    make_user: Callable[..., User],
) -> None:
    """Token expired 1 second ago → AUTH_TOKEN_EXPIRED."""
    user = make_user("frank@test.com", "Secret123!")
    expired_token = create_access_token(
        subject=user.id,
        extra_claims={"role": user.role.value, "email": user.email},
        expires_delta=timedelta(seconds=-1),  # already expired
    )
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert r.status_code == 401
    assert r.json()["code"] == "AUTH_TOKEN_EXPIRED"


def test_me_with_wrong_signature_returns_401_with_code(
    client: TestClient,
    make_user: Callable[..., User],
) -> None:
    """Token signed with a different key → AUTH_INVALID_TOKEN."""
    user = make_user("grace@test.com", "Secret123!")
    bad_token = jwt.encode(
        {"sub": str(user.id), "role": user.role.value, "email": user.email},
        key="different-secret-key",
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
    """DRH user attempts to access an ADMIN-only route → 403 FORBIDDEN."""
    make_user("henry@test.com", "Secret123!", role=UserRole.DRH)
    login = client.post(
        "/auth/login",
        data={"username": "henry@test.com", "password": "Secret123!"},
    )
    token = login.json()["data"]["access_token"]

    r = client.get("/test-admin-only", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403
    assert r.json()["code"] == ErrorCode.FORBIDDEN
