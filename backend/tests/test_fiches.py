from collections.abc import Callable
from typing import Any, cast

from fastapi.testclient import TestClient

from app.core.codes import ErrorCode
from app.core.enums import UserRole
from app.domains.users.model import User


def _login(client: TestClient, email: str, password: str) -> str:
    r = client.post("/auth/login", data={"username": email, "password": password})
    return cast(str, r.json()["data"]["access_token"])


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

    r = client.post(
        "/directions/",
        json=payload,
        headers=_auth(token),
    )
    assert r.status_code == 201
    return cast(int, r.json()["data"]["id"])


def _create_fiche(
    client: TestClient,
    token: str,
    direction_id: int,
    title: str,
) -> dict[str, Any]:
    r = client.post(
        "/fiches-de-poste/",
        json={
            "title": title,
            "description": f"{title} description",
            "missions": f"{title} missions",
            "required_skills": f"{title} skills",
            "experience_level": "Senior",
            "direction_id": direction_id,
        },
        headers=_auth(token),
    )
    assert r.status_code == 201
    return cast(dict[str, Any], r.json()["data"])


def test_nominal_workflow_directeur_create_drh_validate_admin_archive(
    client: TestClient,
    make_user: Callable[..., User],
) -> None:
    admin = make_user("admin@fiche.test", "Secret123!", role=UserRole.ADMIN)
    drh = make_user("drh@fiche.test", "Secret123!", role=UserRole.DRH)
    directeur = make_user("directeur@fiche.test", "Secret123!", role=UserRole.DIRECTEUR)

    admin_token = _login(client, admin.email, "Secret123!")
    drh_token = _login(client, drh.email, "Secret123!")
    directeur_token = _login(client, directeur.email, "Secret123!")
    direction_id = _create_direction(
        client,
        admin_token,
        "DIR-FICHE-1",
        "Direction 1",
        director_id=directeur.id,
    )

    fiche = _create_fiche(client, directeur_token, direction_id, "Fiche 1")
    assert fiche["status"] == "DRAFT"
    assert fiche["created_by_id"] == directeur.id
    assert fiche["validated_by_id"] is None

    validated = client.patch(
        f"/fiches-de-poste/{fiche['id']}/valider",
        headers=_auth(drh_token),
    )
    assert validated.status_code == 200
    validated_body = validated.json()["data"]
    assert validated_body["status"] == "VALIDATED"
    assert validated_body["validated_by_id"] == drh.id

    archived = client.patch(
        f"/fiches-de-poste/{fiche['id']}/archiver",
        headers=_auth(admin_token),
    )
    assert archived.status_code == 200
    assert archived.json()["data"]["status"] == "ARCHIVED"


def test_admin_can_update_and_validate_non_draft_fiche(
    client: TestClient,
    make_user: Callable[..., User],
) -> None:
    admin = make_user("admin-edit@fiche.test", "Secret123!", role=UserRole.ADMIN)
    drh = make_user("drh-edit@fiche.test", "Secret123!", role=UserRole.DRH)
    directeur = make_user("directeur-edit@fiche.test",
                          "Secret123!",
                          role=UserRole.DIRECTEUR)

    admin_token = _login(client, admin.email, "Secret123!")
    drh_token = _login(client, drh.email, "Secret123!")
    directeur_token = _login(client, directeur.email, "Secret123!")
    direction_id = _create_direction(client, admin_token,
                                     "DIR-FICHE-EDIT",
                                     "Direction Edit",
                                     director_id=directeur.id)

    fiche = _create_fiche(client, directeur_token, direction_id, "Fiche admin")

    validated = client.patch(
        f"/fiches-de-poste/{fiche['id']}/valider",
        headers=_auth(admin_token),
    )
    assert validated.status_code == 200

    updated = client.put(
        f"/fiches-de-poste/{fiche['id']}",
        json={"title": "Fiche admin modifiee"},
        headers=_auth(admin_token),
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["title"] == "Fiche admin modifiee"

    archived = client.patch(
        f"/fiches-de-poste/{fiche['id']}/archiver",
        headers=_auth(drh_token),
    )
    assert archived.status_code == 200


def test_invalid_transitions_return_409(
    client: TestClient,
    make_user: Callable[..., User],
) -> None:
    admin = make_user("admin2@fiche.test", "Secret123!", role=UserRole.ADMIN)
    drh = make_user("drh2@fiche.test", "Secret123!", role=UserRole.DRH)
    directeur = make_user(
        "directeur2@fiche.test",
        "Secret123!",
        role=UserRole.DIRECTEUR,
    )

    admin_token = _login(client, admin.email, "Secret123!")
    drh_token = _login(client, drh.email, "Secret123!")
    directeur_token = _login(client, directeur.email, "Secret123!")
    direction_id = _create_direction(
        client,
        admin_token,
        "DIR-FICHE-2",
        "Direction 2",
        director_id=directeur.id,
    )

    fiche_validated = _create_fiche(client, directeur_token, direction_id, "Fiche 2")
    client.patch(
        f"/fiches-de-poste/{fiche_validated['id']}/valider",
        headers=_auth(drh_token),
    )

    rerevalidate = client.patch(
        f"/fiches-de-poste/{fiche_validated['id']}/valider",
        headers=_auth(drh_token),
    )
    assert rerevalidate.status_code == 409
    assert rerevalidate.json()["code"] == "FICHES_INVALID_TRANSITION"

    fiche_archived = _create_fiche(client, directeur_token, direction_id, "Fiche 3")
    client.patch(
        f"/fiches-de-poste/{fiche_archived['id']}/valider",
        headers=_auth(drh_token),
    )
    client.patch(
        f"/fiches-de-poste/{fiche_archived['id']}/archiver",
        headers=_auth(admin_token),
    )

    validate_archived = client.patch(
        f"/fiches-de-poste/{fiche_archived['id']}/valider",
        headers=_auth(drh_token),
    )
    assert validate_archived.status_code == 409
    assert validate_archived.json()["code"] == "FICHES_INVALID_TRANSITION"

    fiche_draft = _create_fiche(client, directeur_token, direction_id, "Fiche 4")
    archive_draft = client.patch(
        f"/fiches-de-poste/{fiche_draft['id']}/archiver",
        headers=_auth(admin_token),
    )
    assert archive_draft.status_code == 409
    assert archive_draft.json()["code"] == "FICHES_INVALID_TRANSITION"


def test_transition_rbac_returns_403(
    client: TestClient,
    make_user: Callable[..., User],
) -> None:
    admin = make_user("admin3@fiche.test", "Secret123!", role=UserRole.ADMIN)
    directeur = make_user(
        "directeur3@fiche.test",
        "Secret123!",
        role=UserRole.DIRECTEUR,
    )
    other_directeur = make_user(
        "directeur4@fiche.test",
        "Secret123!",
        role=UserRole.DIRECTEUR,
    )

    admin_token = _login(client, admin.email, "Secret123!")
    directeur_token = _login(client, directeur.email, "Secret123!")
    other_directeur_token = _login(client, other_directeur.email, "Secret123!")
    direction_id = _create_direction(
        client,
        admin_token,
        "DIR-FICHE-3",
        "Direction 3",
        director_id=directeur.id,
    )
    fiche = _create_fiche(client, directeur_token, direction_id, "Fiche 5")

    validate_forbidden = client.patch(
        f"/fiches-de-poste/{fiche['id']}/valider",
        headers=_auth(directeur_token),
    )
    assert validate_forbidden.status_code == 403
    assert validate_forbidden.json()["code"] == ErrorCode.FORBIDDEN

    archive_forbidden = client.patch(
        f"/fiches-de-poste/{fiche['id']}/archiver",
        headers=_auth(directeur_token),
    )
    assert archive_forbidden.status_code == 403
    assert archive_forbidden.json()["code"] == ErrorCode.FORBIDDEN

    update_forbidden = client.put(
        f"/fiches-de-poste/{fiche['id']}",
        json={"title": "Attempted update"},
        headers=_auth(other_directeur_token),
    )
    assert update_forbidden.status_code == 403
    assert update_forbidden.json()["code"] == ErrorCode.FORBIDDEN


def test_update_on_validated_fiche_returns_409_for_creator(
    client: TestClient,
    make_user: Callable[..., User],
) -> None:
    admin = make_user("admin4@fiche.test", "Secret123!", role=UserRole.ADMIN)
    drh = make_user("drh4@fiche.test", "Secret123!", role=UserRole.DRH)
    directeur = make_user(
        "directeur5@fiche.test",
        "Secret123!",
        role=UserRole.DIRECTEUR,
    )

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
    fiche = _create_fiche(client, directeur_token, direction_id, "Fiche 6")

    client.patch(f"/fiches-de-poste/{fiche['id']}/valider", headers=_auth(drh_token))

    update_after_validation = client.put(
        f"/fiches-de-poste/{fiche['id']}",
        json={"title": "New title"},
        headers=_auth(directeur_token),
    )
    assert update_after_validation.status_code == 200
    assert update_after_validation.json()["data"]["title"] == "New title"


def test_create_fiche_persists_new_profile_fields(
    client: TestClient,
    make_user: Callable[..., User],
) -> None:
    admin = make_user("admin6@fiche.test", "Secret123!", role=UserRole.ADMIN)
    admin_token = _login(client, admin.email, "Secret123!")
    direction_id = _create_direction(
        client,
        admin_token,
        "DIR-FICHE-NEW",
        "Direction 6",
    )

    response = client.post(
        "/fiches-de-poste/",
        json={
            "title": "Fiche profil",
            "description": "desc",
            "missions": "missions",
            "required_skills": "skills",
            "experience_level": "Bac+3",
            "direction_id": direction_id,
            "formation_domain": "Informatique",
            "education_level": "Bac+3",
            "technical_skills": "Python, SQL",
            "managerial_skills": "Gestion d'équipe",
        },
        headers=_auth(admin_token),
    )

    assert response.status_code == 201
    body = response.json()["data"]
    assert body["formation_domain"] == "Informatique"
    assert body["education_level"] == "Bac+3"
    assert body["technical_skills"] == "Python, SQL"
    assert body["managerial_skills"] == "Gestion d'équipe"


def test_filters_and_404_and_invalid_fk(
    client: TestClient,
    make_user: Callable[..., User],
) -> None:
    admin = make_user("admin5@fiche.test", "Secret123!", role=UserRole.ADMIN)
    drh = make_user("drh5@fiche.test", "Secret123!", role=UserRole.DRH)
    directeur = make_user(
        "directeur6@fiche.test",
        "Secret123!",
        role=UserRole.DIRECTEUR,
    )

    admin_token = _login(client, admin.email, "Secret123!")
    drh_token = _login(client, drh.email, "Secret123!")
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

    fiche_one = _create_fiche(client, directeur_token, direction_one_id, "Fiche 7")
    _create_fiche(client, directeur_token, direction_one_id, "Fiche 8")
    fiche_three = _create_fiche(client, directeur_token, direction_two_id, "Fiche 9")

    client.patch(
        f"/fiches-de-poste/{fiche_one['id']}/valider",
        headers=_auth(drh_token),
    )
    client.patch(
        f"/fiches-de-poste/{fiche_three['id']}/valider",
        headers=_auth(drh_token),
    )

    status_filtered = client.get(
        "/fiches-de-poste/?status=VALIDATED",
        headers=_auth(admin_token),
    )
    assert status_filtered.status_code == 200
    assert all(
        item["status"] == "VALIDATED"
        for item in status_filtered.json()["data"]
    )

    direction_filtered = client.get(
        f"/fiches-de-poste/?direction_id={direction_one_id}",
        headers=_auth(admin_token),
    )
    assert direction_filtered.status_code == 200
    assert all(
        item["direction_id"] == direction_one_id
        for item in direction_filtered.json()["data"]
    )

    combined_filtered = client.get(
        f"/fiches-de-poste/?status=VALIDATED&direction_id={direction_one_id}",
        headers=_auth(admin_token),
    )
    assert combined_filtered.status_code == 200
    combined_items = combined_filtered.json()["data"]
    assert len(combined_items) == 1
    assert combined_items[0]["id"] == fiche_one["id"]

    missing = client.get("/fiches-de-poste/9999", headers=_auth(admin_token))
    assert missing.status_code == 404
    assert missing.json()["code"] == "FICHES_NOT_FOUND"

    invalid_fk = client.post(
        "/fiches-de-poste/",
        json={
            "title": "Invalid FK",
            "description": "desc",
            "missions": "missions",
            "required_skills": "skills",
            "experience_level": "Senior",
            "direction_id": 9999,
        },
        headers=_auth(directeur_token),
    )
    assert invalid_fk.status_code == 404
    assert invalid_fk.json()["code"] == "DIRECTIONS_NOT_FOUND"
