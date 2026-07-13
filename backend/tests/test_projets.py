from collections.abc import Callable
from typing import Any, cast

from fastapi.testclient import TestClient

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


def _create_fiche(client: TestClient,
                  token: str,
                  direction_id: int,
                  title: str = "Fiche projet") -> int:
    response = client.post(
        "/fiches-de-poste/",
        json={
            "title": title,
            "main_activities": "desc",
            "missions": "missions",
            "experience_level": "Senior",
            "direction_id": direction_id,
        },
        headers=_auth(token),
    )
    assert response.status_code == 201
    return cast(int, response.json()["data"]["id"])


def _create_besoin(client: TestClient,
                   token: str,
                   fiche_id: int,
                   title: str = "Besoin projet") -> dict[str, Any]:
    response = client.post(
        "/besoins/",
        json={
            "title": title,
            "location": "desc",
            "recruitment_reason": "justification detaillee",
            "priority": "NORMALE",
            "positions_count": 3,
            "desired_date": "2026-07-10",
            "fiche_de_poste_id": fiche_id,
        },
        headers=_auth(token),
    )
    assert response.status_code == 201
    return cast(dict[str, Any], response.json()["data"])


def test_admin_can_create_list_update_close_and_delete_project(
    client: TestClient,
    make_user: Callable[..., User],
) -> None:
    admin = make_user("admin@project.test", "Secret123!", role=UserRole.ADMIN)
    drh = make_user("drh@project.test", "Secret123!", role=UserRole.DRH)
    directeur = make_user("dir@project.test", "Secret123!", role=UserRole.DIRECTEUR)

    admin_token = _login(client, admin.email, "Secret123!")
    drh_token = _login(client, drh.email, "Secret123!")
    directeur_token = _login(client, directeur.email, "Secret123!")

    direction_id = _create_direction(client,
                                     admin_token,
                                     "DIR-PROJ-1",
                                     "Direction projet",
                                     director_id=directeur.id)
    fiche_id = _create_fiche(client, directeur_token, direction_id)
    besoin = _create_besoin(client, directeur_token, fiche_id)
    client.post(f"/besoins/{besoin['id']}/soumettre", headers=_auth(directeur_token))
    client.post(f"/besoins/{besoin['id']}/approuver", headers=_auth(drh_token))

    besoin_lookup = client.get(f"/besoins/{besoin['id']}", headers=_auth(admin_token))
    assert besoin_lookup.status_code == 200
    auto_project_id = besoin_lookup.json()["data"]["projet_id"]
    assert auto_project_id is not None

    created = client.get(f"/projets/{auto_project_id}", headers=_auth(admin_token))
    assert created.status_code == 200
    body = created.json()["data"]
    assert body["besoin_recrutement_id"] == besoin["id"]
    assert body["fiche_de_poste_id"] == fiche_id
    assert body["nombre_postes"] == 3

    listed = client.get(f"/projets/?direction_id={direction_id}",
                        headers=_auth(admin_token))
    assert listed.status_code == 200
    assert listed.json()["data"][0]["direction_name"] == "Direction projet"

    updated = client.put(
        f"/projets/{body['id']}",
        json={"nombre_postes": 6, "description": "mise a jour"},
        headers=_auth(admin_token),
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["nombre_postes"] == 6

    closed = client.patch(f"/projets/{body['id']}/cloturer", headers=_auth(admin_token))
    assert closed.status_code == 200
    assert closed.json()["data"]["status"] == "CLOSED"

    deleted = client.delete(f"/projets/{body['id']}", headers=_auth(admin_token))
    assert deleted.status_code == 200


def test_attach_need_populates_new_project_fields(
    client: TestClient,
    make_user: Callable[..., User],
) -> None:
    drh = make_user("drh2@project.test", "Secret123!", role=UserRole.DRH)
    directeur = make_user("dir2@project.test", "Secret123!", role=UserRole.DIRECTEUR)

    drh_token = _login(client, drh.email, "Secret123!")
    directeur_token = _login(client, directeur.email, "Secret123!")

    direction_id = _create_direction(client, drh_token,
                                     "DIR-PROJ-2",
                                     "Direction projet 2",
                                     director_id=directeur.id)
    fiche_id = _create_fiche(client,
                             directeur_token,
                             direction_id,
                             title="Fiche projet 2")
    besoin = _create_besoin(client, directeur_token, fiche_id, title="Besoin projet 2")
    client.post(f"/besoins/{besoin['id']}/soumettre", headers=_auth(directeur_token))
    client.post(f"/besoins/{besoin['id']}/approuver", headers=_auth(drh_token))

    project = client.post(
        "/projets/",
        json={
            "title": "Projet B",
            "description": "description",
            "start_date": "2026-07-01",
            "expected_end_date": "2026-08-01",
            "status": "DRAFT",
            "manager_id": drh.id,
        },
        headers=_auth(drh_token),
    )
    project_id = project.json()["data"]["id"]

    besoin_lookup = client.get(f"/besoins/{besoin['id']}", headers=_auth(drh_token))
    assert besoin_lookup.status_code == 200
    auto_project_id = besoin_lookup.json()["data"]["projet_id"]
    assert auto_project_id is not None

    auto_project = client.get(f"/projets/{auto_project_id}", headers=_auth(drh_token))
    assert auto_project.status_code == 200
    auto_project_body = auto_project.json()["data"]
    assert auto_project_body["besoin_recrutement_id"] == besoin["id"]
    assert auto_project_body["fiche_de_poste_id"] == fiche_id
    assert auto_project_body["nombre_postes"] == 3

    attached = client.post(f"/projets/{project_id}/besoins/{besoin['id']}",
                           headers=_auth(drh_token))
    assert attached.status_code == 409
    assert attached.json()["code"] == "RECRUTEMENT_BESOIN_ALREADY_ATTACHED"