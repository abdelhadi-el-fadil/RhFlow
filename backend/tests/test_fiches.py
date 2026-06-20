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


def _create_direction(client: TestClient, token: str, code: str, name: str) -> int:
    r = client.post(
        "/directions/",
        json={"name": name, "code": code},
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
    )
    fiche = _create_fiche(client, directeur_token, direction_id, "Fiche 6")

    client.patch(f"/fiches-de-poste/{fiche['id']}/valider", headers=_auth(drh_token))

    update_after_validation = client.put(
        f"/fiches-de-poste/{fiche['id']}",
        json={"title": "New title"},
        headers=_auth(directeur_token),
    )
    assert update_after_validation.status_code == 409
    assert update_after_validation.json()["code"] == "FICHES_INVALID_TRANSITION"


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
    )
    direction_two_id = _create_direction(
        client,
        admin_token,
        "DIR-FICHE-6",
        "Direction 6",
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
