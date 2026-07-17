from collections.abc import Callable
from typing import cast

from fastapi.testclient import TestClient

from app.core.codes import ErrorCode
from app.core.enums import UserRole
from app.domains.users.model import User


def _login(client: TestClient, email: str, password: str) -> str:
    r = client.post("/auth/login", data={"username": email, "password": password})
    return cast(str, r.json()["data"]["access_token"])


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_admin_can_crud_direction_and_audit_is_set(
    client: TestClient, make_user: Callable[..., User]
) -> None:
    admin = make_user("admin@dir.test", "Secret123!", role=UserRole.ADMIN)
    director = make_user("director@dir.test", "Secret123!", role=UserRole.DIRECTEUR)
    token = _login(client, admin.email, "Secret123!")

    payload = {
        "name": "IT",
        "description": "Information Tech",
        "director_id": director.id,
    }
    r = client.post("/directions/", json=payload, headers=_auth(token))
    assert r.status_code == 201
    body = r.json()["data"]
    assert body["id"] is not None
    assert body["code"] == "IT"
    assert body["created_by_id"] == admin.id
    assert body["director_name"] == director.email
    assert body["fiche_count"] == 0

    # get by id
    rget = client.get(f"/directions/{body['id']}", headers=_auth(token))
    assert rget.status_code == 200

    # update
    rupdate = client.put(
        f"/directions/{body['id']}",
        json={"name": "IT Updated"},
        headers=_auth(token),
    )
    assert rupdate.status_code == 200
    assert rupdate.json()["data"]["name"] == "IT Updated"

    # delete (soft)
    rdel = client.delete(f"/directions/{body['id']}", headers=_auth(token))
    assert rdel.status_code == 200

    # ensure gone from list
    rlist = client.get("/directions/", headers=_auth(token))
    assert all(d["id"] != body["id"] for d in rlist.json()["data"])


def test_duplicate_code_returns_409_on_create_and_update(
    client: TestClient, make_user: Callable[..., User]
) -> None:
    admin = make_user("admin2@dir.test", "Secret123!", role=UserRole.ADMIN)
    token = _login(client, admin.email, "Secret123!")

    payload = {"name": "Finance", "code": "DIR-FIN"}
    r1 = client.post("/directions/", json=payload, headers=_auth(token))
    assert r1.status_code == 201

    # create duplicate
    r2 = client.post("/directions/", json=payload, headers=_auth(token))
    assert r2.status_code == 409
    assert r2.json()["code"] == "DIRECTIONS_CODE_ALREADY_EXISTS"

    # create another and try to update to duplicate code
    r3 = client.post(
        "/directions/",
        json={"name": "Other", "code": "DIR-OTH"},
        headers=_auth(token),
    )
    assert r3.status_code == 201
    id_other = r3.json()["data"]["id"]

    rupdate = client.put(
        f"/directions/{id_other}",
        json={"code": "DIR-FIN"},
        headers=_auth(token),
    )
    assert rupdate.status_code == 409
    assert rupdate.json()["code"] == "DIRECTIONS_CODE_ALREADY_EXISTS"


def test_404_for_missing_or_deleted(
    client: TestClient, make_user: Callable[..., User]
) -> None:
    admin = make_user("admin3@dir.test", "Secret123!", role=UserRole.ADMIN)
    token = _login(client, admin.email, "Secret123!")

    # non existent
    r = client.get("/directions/9999", headers=_auth(token))
    assert r.status_code == 404
    assert r.json()["code"] == "DIRECTIONS_NOT_FOUND"

    # create and delete then GET
    rcreate = client.post(
        "/directions/",
        json={"name": "Tmp", "code": "DIR-TMP"},
        headers=_auth(token),
    )
    did = rcreate.json()["data"]["id"]
    client.delete(f"/directions/{did}", headers=_auth(token))
    rget = client.get(f"/directions/{did}", headers=_auth(token))
    assert rget.status_code == 404
    assert rget.json()["code"] == "DIRECTIONS_NOT_FOUND"


def test_forbidden_roles_cannot_modify(
    client: TestClient, make_user: Callable[..., User]
) -> None:
    drh = make_user("drh@dir.test", "Secret123!", role=UserRole.DRH)
    token = _login(client, drh.email, "Secret123!")

    r = client.post(
        "/directions/",
        json={"name": "X"},
        headers=_auth(token),
    )
    assert r.status_code == 201
    assert r.json()["data"]["code"] == "X"


def test_get_without_token_returns_401(client: TestClient) -> None:
    r = client.get("/directions/")
    assert r.status_code == 401
    assert r.json()["code"] == ErrorCode.UNAUTHORIZED
