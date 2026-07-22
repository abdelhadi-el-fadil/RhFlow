from collections.abc import Callable
from typing import Any, cast
from uuid import uuid4

from fastapi.testclient import TestClient

from app.config import settings
from app.core.enums import UserRole
from app.domains.candidatures import service as candidatures_service
from app.domains.users.model import User
from app.main import app


class _FakeStorage:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}

    def upload_bytes(self, object_key: str, payload: bytes, content_type: str) -> None:
        self.objects[object_key] = payload

    def delete_object(self, object_key: str) -> None:
        self.objects.pop(object_key, None)

    def download_bytes(self, object_key: str) -> bytes:
        return self.objects.get(object_key, b"")


def _login(client: TestClient, email: str, password: str) -> str:
    response = client.post(
        "/auth/login", data={"username": email, "password": password}
    )
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
    title: str = "Fiche service key",
) -> int:
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


def _create_besoin(client: TestClient, token: str, fiche_id: int) -> dict[str, Any]:
    response = client.post(
        "/besoins/",
        json={
            "lieu_affectation": "desc",
            "recruitment_reason": "justification detaillee",
            "priority": "NORMALE",
            "positions_count": 1,
            "desired_date": "2026-07-10",
            "fiche_de_poste_id": fiche_id,
        },
        headers=_auth(token),
    )
    assert response.status_code == 201
    return cast(dict[str, Any], response.json()["data"])


def _prepare_project_with_subject(
    client: TestClient,
    make_user: Callable[..., User],
    subject: str,
) -> tuple[int, str, str]:
    suffix = uuid4().hex[:8]
    admin = make_user(
        f"api-key-admin-{suffix}@test.com", "Secret123!", role=UserRole.ADMIN
    )
    drh = make_user(f"api-key-drh-{suffix}@test.com", "Secret123!", role=UserRole.DRH)
    directeur = make_user(
        f"api-key-directeur-{suffix}@test.com",
        "Secret123!",
        role=UserRole.DIRECTEUR,
    )

    admin_token = _login(client, admin.email, "Secret123!")
    drh_token = _login(client, drh.email, "Secret123!")
    directeur_token = _login(client, directeur.email, "Secret123!")

    direction_id = _create_direction(
        client,
        admin_token,
        f"DIR-API-{suffix}",
        "Direction API Key",
        director_id=directeur.id,
    )
    fiche_id = _create_fiche(client, directeur_token, direction_id)
    besoin = _create_besoin(client, directeur_token, fiche_id)
    approve = client.post(
        f"/besoins/{besoin['id']}/approuver",
        headers=_auth(drh_token),
    )
    assert approve.status_code == 200

    projects_response = client.get(
        f"/projets/?direction_id={direction_id}",
        headers=_auth(admin_token),
    )
    assert projects_response.status_code == 200
    project = next(
        (
            item
            for item in projects_response.json()["data"]
            if item["besoin_recrutement_id"] == besoin["id"]
        ),
        None,
    )
    assert project is not None

    update = client.put(
        f"/projets/{project['id']}",
        json={"email_subject": subject},
        headers=_auth(admin_token),
    )
    assert update.status_code == 200
    return cast(int, project["id"]), drh_token, admin_token


def test_lookup_project_by_email_subject_with_jwt_is_rejected(
    client: TestClient,
    make_user: Callable[..., User],
) -> None:
    subject = "Candidature - API KEY - JWT"
    _, drh_token, _ = _prepare_project_with_subject(client, make_user, subject)

    response = client.get(
        "/projets-recrutement/by-email-subject",
        params={"subject": subject},
        headers=_auth(drh_token),
    )

    assert response.status_code == 401


def test_lookup_project_by_email_subject_with_service_api_key(
    client: TestClient,
    make_user: Callable[..., User],
    monkeypatch: Any,
) -> None:
    monkeypatch.setattr(settings, "CANDIDATURE_API_KEY", "service-key-123")
    subject = "Candidature - API KEY - SERVICE"
    project_id, _, _ = _prepare_project_with_subject(client, make_user, subject)

    response = client.get(
        "/projets-recrutement/by-email-subject",
        params={"subject": subject},
        headers={"X-API-Key": "service-key-123"},
    )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["projet_recrutement_id"] == project_id
    assert payload["email_subject"] == subject


def test_lookup_project_by_email_subject_requires_auth(
    client: TestClient,
) -> None:
    response = client.get(
        "/projets-recrutement/by-email-subject",
        params={"subject": "missing"},
    )
    assert response.status_code == 401


def test_lookup_project_by_email_subject_ignores_closed_projects(
    client: TestClient,
    make_user: Callable[..., User],
    monkeypatch: Any,
) -> None:
    monkeypatch.setattr(settings, "CANDIDATURE_API_KEY", "service-key-closed")
    subject = "Candidature - API KEY - CLOSED"
    project_id, _, admin_token = _prepare_project_with_subject(
        client, make_user, subject
    )

    close_response = client.patch(
        f"/projets/{project_id}/cloturer",
        headers=_auth(admin_token),
    )
    assert close_response.status_code == 200

    missing_subject = "Candidature - API KEY - DOES-NOT-EXIST"
    missing_response = client.get(
        "/projets-recrutement/by-email-subject",
        params={"subject": missing_subject},
        headers={"X-API-Key": "service-key-closed"},
    )
    closed_response = client.get(
        "/projets-recrutement/by-email-subject",
        params={"subject": subject},
        headers={"X-API-Key": "service-key-closed"},
    )

    assert missing_response.status_code == 404
    assert closed_response.status_code == 404
    assert missing_response.json()["code"] == "RECRUTEMENT_PROJET_NOT_FOUND"
    assert closed_response.json()["code"] == "RECRUTEMENT_PROJET_NOT_FOUND"
    assert closed_response.json() == missing_response.json()


def test_upload_candidature_with_service_api_key(
    client: TestClient,
    make_user: Callable[..., User],
    monkeypatch: Any,
) -> None:
    monkeypatch.setattr(settings, "CANDIDATURE_API_KEY", "service-key-upload")
    project_id, _, _ = _prepare_project_with_subject(
        client,
        make_user,
        "Candidature - Upload API Key",
    )

    fake_storage = _FakeStorage()

    from app.core.dependencies import get_minio_candidatures_storage_service

    app.dependency_overrides[get_minio_candidatures_storage_service] = (
        lambda: fake_storage
    )
    monkeypatch.setattr(
        candidatures_service,
        "process_candidature_pipeline",
        lambda candidature_id, storage: None,
    )

    try:
        response = client.post(
            "/candidatures/",
            data={"projet_recrutement_id": str(project_id)},
            files={"file": ("resume.pdf", b"fake-pdf", "application/pdf")},
            headers={"X-API-Key": "service-key-upload"},
        )
    finally:
        app.dependency_overrides.pop(get_minio_candidatures_storage_service, None)

    assert response.status_code == 201
    body = cast(dict[str, Any], response.json())
    data = cast(dict[str, Any], body["data"])
    assert data["projet_recrutement_id"] == project_id
    assert data["statut"] == "EN_COURS"
