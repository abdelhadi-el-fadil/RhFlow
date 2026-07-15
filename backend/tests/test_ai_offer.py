from collections.abc import Callable
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.enums import UserRole
from app.domains.recruitment.model import ProjetRecrutement
from app.domains.users.model import User


def _login(client: TestClient, email: str, password: str) -> str:
    response = client.post(
        "/auth/login",
        data={"username": email, "password": password},
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
    title: str = "Fiche projet",
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


def _create_besoin(
    client: TestClient,
    token: str,
    fiche_id: int,
    title: str = "Besoin projet",
) -> dict[str, Any]:
    response = client.post(
        "/besoins/",
        json={
            "lieu_affectation": "desc",
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


def test_generate_offer_persists_and_reuses_existing_offer(
    client: TestClient,
    db: Session,
    make_user: Callable[..., User],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    admin = make_user("admin@ai.test", "Secret123!", role=UserRole.ADMIN)
    drh = make_user("drh@ai.test", "Secret123!", role=UserRole.DRH)
    directeur = make_user("dir@ai.test", "Secret123!", role=UserRole.DIRECTEUR)

    admin_token = _login(client, admin.email, "Secret123!")
    drh_token = _login(client, drh.email, "Secret123!")
    directeur_token = _login(client, directeur.email, "Secret123!")

    direction_id = _create_direction(
        client,
        admin_token,
        "DIR-AI-1",
        "Direction AI",
        director_id=directeur.id,
    )
    fiche_id = _create_fiche(client, directeur_token, direction_id, title="Fiche IA")
    besoin = _create_besoin(client, directeur_token, fiche_id, title="Besoin IA")
    approved = client.post(
        f"/besoins/{besoin['id']}/approuver",
        headers=_auth(drh_token),
    )
    assert approved.status_code == 200

    project = (
        db.query(ProjetRecrutement)
        .filter(ProjetRecrutement.besoin_recrutement_id == besoin["id"])
        .one()
    )
    assert project.offre is None

    calls = {"count": 0}

    def fake_generate(prompt: str) -> str:
        calls["count"] += 1
        assert "## Fiche de poste" in prompt
        return "# Offre générée\n\nContenu de test."

    monkeypatch.setattr("app.ai.router.offer_router.generate_sync", fake_generate)

    first = client.get(f"/ai/generate-offer/{project.id}", headers=_auth(admin_token))
    assert first.status_code == 200
    assert first.json()["data"]["offer"] == "# Offre générée\n\nContenu de test."

    db.refresh(project)
    assert project.offre == "# Offre générée\n\nContenu de test."

    second = client.get(f"/ai/generate-offer/{project.id}", headers=_auth(admin_token))
    assert second.status_code == 200
    assert second.json()["data"]["offer"] == "# Offre générée\n\nContenu de test."
    assert calls["count"] == 1
