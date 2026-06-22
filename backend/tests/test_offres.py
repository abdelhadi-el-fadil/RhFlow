from collections.abc import Callable
from typing import Any, cast

from fastapi.testclient import TestClient

from app.core.codes import ErrorCode
from app.core.enums import UserRole
from app.domains.offres.model import Offre
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


def _create_fiche(client: TestClient, token: str, direction_id: int) -> int:
    r = client.post(
        "/fiches-de-poste/",
        json={
            "title": "Fiche Offre",
            "description": "Description",
            "missions": "Missions",
            "required_skills": "Skills",
            "experience_level": "Senior",
            "direction_id": direction_id,
        },
        headers=_auth(token),
    )
    assert r.status_code == 201
    return cast(int, r.json()["data"]["id"])


def _create_besoin(client: TestClient, token: str, fiche_id: int, title: str) -> int:
    r = client.post(
        "/besoins/",
        json={
            "title": title,
            "description": f"{title} description",
            "positions_count": 1,
            "desired_date": "2026-08-01",
            "justification": f"{title} justification",
            "fiche_de_poste_id": fiche_id,
        },
        headers=_auth(token),
    )
    assert r.status_code == 201
    return cast(int, r.json()["data"]["id"])


def _create_approved_besoin(
    client: TestClient,
    directeur_token: str,
    drh_token: str,
    fiche_id: int,
    title: str,
) -> int:
    besoin_id = _create_besoin(client, directeur_token, fiche_id, title)

    submitted = client.post(
        f"/besoins/{besoin_id}/soumettre",
        headers=_auth(directeur_token),
    )
    assert submitted.status_code == 200

    approved = client.post(
        f"/besoins/{besoin_id}/approuver",
        headers=_auth(drh_token),
    )
    assert approved.status_code == 200
    return besoin_id


def _create_offre(
    client: TestClient,
    drh_token: str,
    besoin_id: int,
    title: str,
) -> dict[str, Any]:
    r = client.post(
        "/offres/",
        json={
            "title": title,
            "description": f"{title} description",
            "requirements": f"{title} requirements",
            "deadline": "2026-12-31",
            "besoin_id": besoin_id,
        },
        headers=_auth(drh_token),
    )
    assert r.status_code == 201
    return cast(dict[str, Any], r.json()["data"])


def test_nominal_cycle_create_publish_close(
    client: TestClient,
    make_user: Callable[..., User],
) -> None:
    admin = make_user("admin@offres.test", "Secret123!", role=UserRole.ADMIN)
    drh = make_user("drh@offres.test", "Secret123!", role=UserRole.DRH)
    directeur = make_user("dir@offres.test", "Secret123!", role=UserRole.DIRECTEUR)

    admin_token = _login(client, admin.email, "Secret123!")
    drh_token = _login(client, drh.email, "Secret123!")
    directeur_token = _login(client, directeur.email, "Secret123!")

    direction_id = _create_direction(client, admin_token, "DIR-OFFRE-1", "Direction 1")
    fiche_id = _create_fiche(client, directeur_token, direction_id)
    approved_besoin_id = _create_approved_besoin(
        client,
        directeur_token,
        drh_token,
        fiche_id,
        "Besoin cycle",
    )

    created = _create_offre(client, drh_token, approved_besoin_id, "Offre Cycle")
    assert created["status"] == "DRAFT"
    assert created["published_at"] is None

    published = client.patch(
        f"/offres/{created['id']}/publier",
        headers=_auth(drh_token),
    )
    assert published.status_code == 200
    published_body = published.json()["data"]
    assert published_body["status"] == "PUBLISHED"
    assert published_body["published_at"] is not None
    assert published_body["published_by_id"] == drh.id

    closed = client.patch(
        f"/offres/{created['id']}/cloturer",
        headers=_auth(drh_token),
    )
    assert closed.status_code == 200
    assert closed.json()["data"]["status"] == "CLOSED"


def test_public_list_is_accessible_and_r4_strict(
    client: TestClient,
    db: Any,
    make_user: Callable[..., User],
) -> None:
    admin = make_user("admin2@offres.test", "Secret123!", role=UserRole.ADMIN)
    drh = make_user("drh2@offres.test", "Secret123!", role=UserRole.DRH)
    directeur = make_user("dir2@offres.test", "Secret123!", role=UserRole.DIRECTEUR)

    admin_token = _login(client, admin.email, "Secret123!")
    drh_token = _login(client, drh.email, "Secret123!")
    directeur_token = _login(client, directeur.email, "Secret123!")

    direction_id = _create_direction(client, admin_token, "DIR-OFFRE-2", "Direction 2")
    fiche_id = _create_fiche(client, directeur_token, direction_id)

    besoin_published = _create_approved_besoin(
        client,
        directeur_token,
        drh_token,
        fiche_id,
        "Besoin published",
    )
    besoin_draft = _create_approved_besoin(
        client,
        directeur_token,
        drh_token,
        fiche_id,
        "Besoin draft",
    )
    besoin_closed = _create_approved_besoin(
        client,
        directeur_token,
        drh_token,
        fiche_id,
        "Besoin closed",
    )
    besoin_soft_deleted = _create_approved_besoin(
        client,
        directeur_token,
        drh_token,
        fiche_id,
        "Besoin soft",
    )

    published_offre = _create_offre(client, drh_token, besoin_published, "Visible")
    draft_offre = _create_offre(client, drh_token, besoin_draft, "Draft")
    closed_offre = _create_offre(client, drh_token, besoin_closed, "Closed")
    soft_deleted_offre = _create_offre(client, drh_token, besoin_soft_deleted,
     "Deleted")

    client.patch(f"/offres/{published_offre['id']}/publier", headers=_auth(drh_token))
    client.patch(f"/offres/{closed_offre['id']}/publier", headers=_auth(drh_token))
    client.patch(f"/offres/{closed_offre['id']}/cloturer", headers=_auth(drh_token))
    client.patch(f"/offres/{soft_deleted_offre['id']}/publier",
                  headers=_auth(drh_token))

    soft_deleted_entity = db.get(Offre, soft_deleted_offre["id"])
    assert soft_deleted_entity is not None
    soft_deleted_entity.is_deleted = True
    db.add(soft_deleted_entity)
    db.commit()

    response = client.get("/offres/")
    assert response.status_code == 200

    body = response.json()
    assert body["meta"]["total_items"] == 1
    assert len(body["data"]) == 1
    returned = body["data"][0]
    assert returned["title"] == "Visible"

    assert draft_offre["id"] != published_offre["id"]
    assert closed_offre["id"] != published_offre["id"]

    assert set(returned.keys()) == {
        "title",
        "description",
        "requirements",
        "published_at",
        "deadline",
    }


def test_invalid_transitions_return_409(
    client: TestClient,
    make_user: Callable[..., User],
) -> None:
    admin = make_user("admin3@offres.test", "Secret123!", role=UserRole.ADMIN)
    drh = make_user("drh3@offres.test", "Secret123!", role=UserRole.DRH)
    directeur = make_user("dir3@offres.test", "Secret123!", role=UserRole.DIRECTEUR)

    admin_token = _login(client, admin.email, "Secret123!")
    drh_token = _login(client, drh.email, "Secret123!")
    directeur_token = _login(client, directeur.email, "Secret123!")

    direction_id = _create_direction(client, admin_token, "DIR-OFFRE-3", "Direction 3")
    fiche_id = _create_fiche(client, directeur_token, direction_id)

    besoin_a = _create_approved_besoin(client,
                                        directeur_token,
                                        drh_token,
                                        fiche_id,
                                        "A")
    besoin_b = _create_approved_besoin(client,
                                        directeur_token,
                                        drh_token,
                                        fiche_id,
                                        "B")
    besoin_c = _create_approved_besoin(client,
                                        directeur_token,
                                        drh_token,
                                        fiche_id,
                                        "C")

    offre_a = _create_offre(client, drh_token, besoin_a, "Offre A")
    offre_b = _create_offre(client, drh_token, besoin_b, "Offre B")
    offre_c = _create_offre(client, drh_token, besoin_c, "Offre C")

    client.patch(f"/offres/{offre_a['id']}/publier", headers=_auth(drh_token))

    publish_published = client.patch(
        f"/offres/{offre_a['id']}/publier",
        headers=_auth(drh_token),
    )
    assert publish_published.status_code == 409
    assert publish_published.json()["code"] == "OFFRES_INVALID_TRANSITION"

    close_draft = client.patch(
        f"/offres/{offre_b['id']}/cloturer",
        headers=_auth(drh_token),
    )
    assert close_draft.status_code == 409
    assert close_draft.json()["code"] == "OFFRES_INVALID_TRANSITION"

    client.patch(f"/offres/{offre_c['id']}/publier", headers=_auth(drh_token))
    client.patch(f"/offres/{offre_c['id']}/cloturer", headers=_auth(drh_token))

    publish_closed = client.patch(
        f"/offres/{offre_c['id']}/publier",
        headers=_auth(drh_token),
    )
    assert publish_closed.status_code == 409
    assert publish_closed.json()["code"] == "OFFRES_INVALID_TRANSITION"


def test_rbac_returns_403_for_directeur(
    client: TestClient,
    make_user: Callable[..., User],
) -> None:
    admin = make_user("admin4@offres.test", "Secret123!", role=UserRole.ADMIN)
    drh = make_user("drh4@offres.test", "Secret123!", role=UserRole.DRH)
    directeur = make_user("dir4@offres.test", "Secret123!", role=UserRole.DIRECTEUR)

    admin_token = _login(client, admin.email, "Secret123!")
    drh_token = _login(client, drh.email, "Secret123!")
    directeur_token = _login(client, directeur.email, "Secret123!")

    direction_id = _create_direction(client, admin_token, "DIR-OFFRE-4", "Direction 4")
    fiche_id = _create_fiche(client, directeur_token, direction_id)
    approved_besoin_id = _create_approved_besoin(
        client,
        directeur_token,
        drh_token,
        fiche_id,
        "Besoin RBAC",
    )

    create_forbidden = client.post(
        "/offres/",
        json={
            "title": "Forbidden create",
            "description": "desc",
            "requirements": "req",
            "deadline": "2026-11-30",
            "besoin_id": approved_besoin_id,
        },
        headers=_auth(directeur_token),
    )
    assert create_forbidden.status_code == 403
    assert create_forbidden.json()["code"] == ErrorCode.FORBIDDEN

    offre = _create_offre(client, drh_token, approved_besoin_id, "Allowed")

    publish_forbidden = client.patch(
        f"/offres/{offre['id']}/publier",
        headers=_auth(directeur_token),
    )
    assert publish_forbidden.status_code == 403
    assert publish_forbidden.json()["code"] == ErrorCode.FORBIDDEN

    client.patch(f"/offres/{offre['id']}/publier", headers=_auth(drh_token))

    close_forbidden = client.patch(
        f"/offres/{offre['id']}/cloturer",
        headers=_auth(directeur_token),
    )
    assert close_forbidden.status_code == 403
    assert close_forbidden.json()["code"] == ErrorCode.FORBIDDEN


def test_404_and_409_on_create_constraints(
    client: TestClient,
    make_user: Callable[..., User],
) -> None:
    admin = make_user("admin5@offres.test", "Secret123!", role=UserRole.ADMIN)
    drh = make_user("drh5@offres.test", "Secret123!", role=UserRole.DRH)
    directeur = make_user("dir5@offres.test", "Secret123!", role=UserRole.DIRECTEUR)

    admin_token = _login(client, admin.email, "Secret123!")
    drh_token = _login(client, drh.email, "Secret123!")
    directeur_token = _login(client, directeur.email, "Secret123!")

    missing_offre = client.patch("/offres/9999/publier", headers=_auth(drh_token))
    assert missing_offre.status_code == 404
    assert missing_offre.json()["code"] == "OFFRES_NOT_FOUND"

    direction_id = _create_direction(client, admin_token, "DIR-OFFRE-5", "Direction 5")
    fiche_id = _create_fiche(client, directeur_token, direction_id)

    non_approved_besoin_id = _create_besoin(
        client,
        directeur_token,
        fiche_id,
        "Besoin non approved",
    )

    with_missing_besoin = client.post(
        "/offres/",
        json={
            "title": "Missing besoin",
            "description": "desc",
            "requirements": "req",
            "deadline": "2026-10-01",
            "besoin_id": 9999,
        },
        headers=_auth(drh_token),
    )
    assert with_missing_besoin.status_code == 409
    assert with_missing_besoin.json()["code"] == "OFFRES_BESOIN_NOT_PUBLISHABLE"

    with_non_approved_besoin = client.post(
        "/offres/",
        json={
            "title": "Non approved besoin",
            "description": "desc",
            "requirements": "req",
            "deadline": "2026-10-01",
            "besoin_id": non_approved_besoin_id,
        },
        headers=_auth(drh_token),
    )
    assert with_non_approved_besoin.status_code == 409
    assert with_non_approved_besoin.json()["code"] == "OFFRES_BESOIN_NOT_PUBLISHABLE"
