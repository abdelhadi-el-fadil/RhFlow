from collections.abc import Callable
from typing import Any, cast

from fastapi.testclient import TestClient

from app.core.codes import ErrorCode
from app.core.enums import UserRole
from app.domains.users.model import User


def _login(client: TestClient, email: str, password: str) -> str:
    response = client.post("/auth/login", data={"username": email,
                                                "password": password})
    return cast(str, response.json()["data"]["access_token"])


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _create_direction(
    client: TestClient,
    token: str,
    code: str,
    name: str,
    director_id: int | None = None,
) -> int:
    payload: dict[str, Any] = {"name": name, "code": code}
    if director_id is not None:
        payload["director_id"] = director_id

    response = client.post("/directions/", json=payload, headers=_auth(token))
    assert response.status_code == 201
    return cast(int, response.json()["data"]["id"])


def _create_fiche(
    client: TestClient,
    token: str,
    direction_id: int,
    title: str,
) -> dict[str, Any]:
    response = client.post(
        "/fiches-de-poste/",
        json={
            "title": title,
            "main_activities": f"{title} activites",
            "missions": f"{title} missions",
            "required_skills": f"{title} skills",
            "experience_level": "Senior",
            "direction_id": direction_id,
        },
        headers=_auth(token),
    )
    assert response.status_code == 201
    return cast(dict[str, Any], response.json()["data"])


def test_nominal_create_update_and_delete_by_admin(
    client: TestClient,
    make_user: Callable[..., User],
) -> None:
    admin = make_user("admin@fiche.test", "Secret123!", role=UserRole.ADMIN)
    directeur = make_user("directeur@fiche.test", "Secret123!", role=UserRole.DIRECTEUR)

    admin_token = _login(client, admin.email, "Secret123!")
    directeur_token = _login(client, directeur.email, "Secret123!")
    direction_id = _create_direction(
        client,
        admin_token,
        "DIR-FICHE-1",
        "Direction 1",
        director_id=directeur.id,
    )

    fiche = _create_fiche(client, directeur_token, direction_id, "Fiche 1")
    assert fiche["created_by_id"] == directeur.id
    assert fiche["main_activities"] == "Fiche 1 activites"

    updated = client.put(
        f"/fiches-de-poste/{fiche['id']}",
        json={"main_activities": "Nouvelles activites"},
        headers=_auth(admin_token),
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["main_activities"] == "Nouvelles activites"

    deleted = client.delete(f"/fiches-de-poste/{fiche['id']}",
                            headers=_auth(admin_token))
    assert deleted.status_code == 200


def test_directeur_can_create_and_update_only_in_his_direction(
    client: TestClient,
    make_user: Callable[..., User],
) -> None:
    admin = make_user("admin2@fiche.test", "Secret123!", role=UserRole.ADMIN)
    directeur = make_user("directeur2@fiche.test",
                          "Secret123!",
                          role=UserRole.DIRECTEUR)
    other_directeur = make_user("directeur3@fiche.test",
                                "Secret123!",
                                role=UserRole.DIRECTEUR)

    admin_token = _login(client, admin.email, "Secret123!")
    directeur_token = _login(client, directeur.email, "Secret123!")
    other_directeur_token = _login(client, other_directeur.email, "Secret123!")

    own_direction_id = _create_direction(
        client,
        admin_token,
        "DIR-FICHE-2",
        "Direction 2",
        director_id=directeur.id,
    )
    other_direction_id = _create_direction(
        client,
        admin_token,
        "DIR-FICHE-3",
        "Direction 3",
        director_id=other_directeur.id,
    )

    own_fiche = _create_fiche(client, directeur_token, own_direction_id, "Fiche own")

    forbidden_create = client.post(
        "/fiches-de-poste/",
        json={
            "title": "Forbidden",
            "main_activities": "x",
            "missions": "x",
            "required_skills": "x",
            "experience_level": "Senior",
            "direction_id": other_direction_id,
        },
        headers=_auth(directeur_token),
    )
    assert forbidden_create.status_code == 403
    assert forbidden_create.json()["code"] == ErrorCode.FORBIDDEN

    forbidden_update = client.put(
        f"/fiches-de-poste/{own_fiche['id']}",
        json={"direction_id": other_direction_id},
        headers=_auth(directeur_token),
    )
    assert forbidden_update.status_code == 403
    assert forbidden_update.json()["code"] == ErrorCode.FORBIDDEN

    other_cannot_update = client.put(
        f"/fiches-de-poste/{own_fiche['id']}",
        json={"title": "Attempted update"},
        headers=_auth(other_directeur_token),
    )
    assert other_cannot_update.status_code == 403
    assert other_cannot_update.json()["code"] == ErrorCode.FORBIDDEN


def test_only_admin_and_drh_can_delete_fiche(
    client: TestClient,
    make_user: Callable[..., User],
) -> None:
    admin = make_user("admin3@fiche.test", "Secret123!", role=UserRole.ADMIN)
    drh = make_user("drh@fiche.test", "Secret123!", role=UserRole.DRH)
    directeur = make_user("directeur4@fiche.test",
                          "Secret123!",
                          role=UserRole.DIRECTEUR)

    admin_token = _login(client, admin.email, "Secret123!")
    drh_token = _login(client, drh.email, "Secret123!")
    directeur_token = _login(client, directeur.email, "Secret123!")

    direction_id = _create_direction(
        client,
        admin_token,
        "DIR-FICHE-4",
        "Direction 4",
        director_id=directeur.id,
    )

    fiche = _create_fiche(client, directeur_token, direction_id, "Fiche delete")

    forbidden_delete = client.delete(
        f"/fiches-de-poste/{fiche['id']}",
        headers=_auth(directeur_token),
    )
    assert forbidden_delete.status_code == 403
    assert forbidden_delete.json()["code"] == ErrorCode.FORBIDDEN

    allowed_delete = client.delete(
        f"/fiches-de-poste/{fiche['id']}",
        headers=_auth(drh_token),
    )
    assert allowed_delete.status_code == 200


def test_direction_filter_and_missing_resources(
    client: TestClient,
    make_user: Callable[..., User],
) -> None:
    admin = make_user("admin4@fiche.test", "Secret123!", role=UserRole.ADMIN)
    directeur = make_user("directeur5@fiche.test",
                          "Secret123!",
                          role=UserRole.DIRECTEUR)

    admin_token = _login(client, admin.email, "Secret123!")
    directeur_token = _login(client, directeur.email, "Secret123!")

    direction_one_id = _create_direction(
        client,
        admin_token,
        "DIR-FICHE-5",
        "Direction 5",
        director_id=directeur.id,
    )
    direction_two_id = _create_direction(
        client,
        admin_token,
        "DIR-FICHE-6",
        "Direction 6",
        director_id=directeur.id,
    )

    _create_fiche(client, directeur_token, direction_one_id, "Fiche 7")
    _create_fiche(client, directeur_token, direction_two_id, "Fiche 8")

    direction_filtered = client.get(
        f"/fiches-de-poste/?direction_id={direction_one_id}",
        headers=_auth(admin_token),
    )
    assert direction_filtered.status_code == 200
    data = direction_filtered.json()["data"]

    assert {item["direction_id"] for item in data} == {direction_one_id}

    missing = client.get("/fiches-de-poste/9999", headers=_auth(admin_token))
    assert missing.status_code == 404
    assert missing.json()["code"] == "FICHES_NOT_FOUND"

    invalid_fk = client.post(
        "/fiches-de-poste/",
        json={
            "title": "Invalid FK",
            "main_activities": "desc",
            "missions": "missions",
            "required_skills": "skills",
            "experience_level": "Senior",
            "direction_id": 9999,
        },
        headers=_auth(directeur_token),
    )
    assert invalid_fk.status_code == 404
    assert invalid_fk.json()["code"] == "DIRECTIONS_NOT_FOUND"
