from collections.abc import Callable

from fastapi.testclient import TestClient

from app.core.codes import ErrorCode
from app.core.enums import UserRole
from app.domains.users.model import User


def test_admin_can_create_user_and_returns_201_without_hashed_password(
    client: TestClient,
    make_user: Callable[..., User],
) -> None:
    admin = make_user("admin@test.com", "Secret123!", role=UserRole.ADMIN)
    login = client.post(
        "/auth/login",
        data={"username": admin.email, "password": "Secret123!"},
    )
    token = login.json()["data"]["access_token"]

    payload = {
        "email": "newuser@test.com",
        "password": "Secret123!",
        "full_name": "New User",
        "gsm": "0600000000",
        "role": "DRH",
    }
    r = client.post(
        "/users/",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert r.status_code == 201
    body = r.json()["data"]
    assert body["id"] is not None
    assert body["email"] == payload["email"]
    assert "hashed_password" not in body


def test_create_user_invalid_email_returns_422(
    client: TestClient,
    make_user: Callable[..., User],
) -> None:
    admin = make_user("admin2@test.com", "Secret123!", role=UserRole.ADMIN)
    login = client.post(
        "/auth/login",
        data={"username": admin.email, "password": "Secret123!"},
    )
    token = login.json()["data"]["access_token"]

    r = client.post(
        "/users/",
        json={"email": "not-an-email", "password": "Secret123!", "role": "DRH"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert r.status_code == 422
    assert r.json()["code"] == ErrorCode.VALIDATION_ERROR


def test_create_user_short_password_returns_422(
    client: TestClient,
    make_user: Callable[..., User],
) -> None:
    admin = make_user("admin3@test.com", "Secret123!", role=UserRole.ADMIN)
    login = client.post(
        "/auth/login",
        data={"username": admin.email, "password": "Secret123!"},
    )
    token = login.json()["data"]["access_token"]

    r = client.post(
        "/users/",
        json={"email": "new2@test.com", "password": "short", "role": "DRH"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert r.status_code == 422
    assert r.json()["code"] == ErrorCode.VALIDATION_ERROR


def test_get_users_paginated_returns_meta_and_users(
    client: TestClient,
    make_user: Callable[..., User],
) -> None:
    admin = make_user("admin4@test.com", "Secret123!", role=UserRole.ADMIN)
    login = client.post(
        "/auth/login",
        data={"username": admin.email, "password": "Secret123!"},
    )
    token = login.json()["data"]["access_token"]

    for i in range(3):
        client.post(
            "/users/",
            json={
                "email": f"user{i}@test.com",
                "password": "Secret123!",
                "role": "DRH",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

    r = client.get(
        "/users/?page=1&page_size=2", headers={"Authorization": f"Bearer {token}"}
    )
    assert r.status_code == 200
    body = r.json()
    assert body["meta"]["page"] == 1
    assert body["meta"]["page_size"] == 2
    assert body["meta"]["total_items"] >= 3
    assert len(body["data"]) == 2


def test_admin_can_update_user(
    client: TestClient,
    make_user: Callable[..., User],
) -> None:
    admin = make_user("admin5@test.com", "Secret123!", role=UserRole.ADMIN)
    target = make_user("target@test.com", "Secret123!", role=UserRole.DRH)
    login = client.post(
        "/auth/login",
        data={"username": admin.email, "password": "Secret123!"},
    )
    token = login.json()["data"]["access_token"]

    r = client.put(
        f"/users/{target.id}",
        json={"full_name": "Updated Name", "enabled": False},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert r.status_code == 200
    body = r.json()["data"]
    assert body["full_name"] == "Updated Name"
    assert body["enabled"] is False


def test_admin_can_soft_delete_user_and_user_disappears_from_list(
    client: TestClient,
    make_user: Callable[..., User],
) -> None:
    admin = make_user("admin6@test.com", "Secret123!", role=UserRole.ADMIN)
    target = make_user("todelete@test.com", "Secret123!", role=UserRole.DRH)
    login = client.post(
        "/auth/login",
        data={"username": admin.email, "password": "Secret123!"},
    )
    token = login.json()["data"]["access_token"]

    delete_resp = client.delete(
        f"/users/{target.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert delete_resp.status_code == 200
    assert delete_resp.json()["data"] is None

    list_resp = client.get("/users/", headers={"Authorization": f"Bearer {token}"})
    assert list_resp.status_code == 200
    assert all(user["id"] != target.id for user in list_resp.json()["data"])

    login_deleted = client.post(
        "/auth/login",
        data={"username": target.email, "password": "Secret123!"},
    )
    assert login_deleted.status_code == 401


def test_drh_can_create_user_returns_201(
    client: TestClient,
    make_user: Callable[..., User],
) -> None:
    drh = make_user("drh@test.com", "Secret123!", role=UserRole.DRH)
    login = client.post(
        "/auth/login",
        data={"username": drh.email, "password": "Secret123!"},
    )
    token = login.json()["data"]["access_token"]

    r = client.post(
        "/users/",
        json={"email": "forbidden@test.com", "password": "Secret123!", "role": "DRH"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 201
    assert r.json()["data"]["email"] == "forbidden@test.com"