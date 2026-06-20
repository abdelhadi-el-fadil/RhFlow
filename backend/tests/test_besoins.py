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


def _create_fiche(client: TestClient, token: str, direction_id: int) -> int:
    r = client.post(
        "/fiches-de-poste/",
        json={
            "title": "Fiche",
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


def _create_besoin(
    client: TestClient,
    token: str,
    fiche_id: int,
    title: str,
) -> dict[str, Any]:
    r = client.post(
        "/besoins/",
        json={
            "title": title,
            "description": f"{title} description",
            "positions_count": 2,
            "desired_date": "2026-07-01",
            "justification": f"{title} justification",
            "fiche_de_poste_id": fiche_id,
        },
        headers=_auth(token),
    )
    assert r.status_code == 201
    return cast(dict[str, Any], r.json()["data"])


def test_nominal_workflow_submit_approve_and_reject(
    client: TestClient,
    make_user: Callable[..., User],
) -> None:
    admin = make_user("admin@need.test", "Secret123!", role=UserRole.ADMIN)
    drh = make_user("drh@need.test", "Secret123!", role=UserRole.DRH)
    directeur = make_user("dir@need.test", "Secret123!", role=UserRole.DIRECTEUR)

    admin_token = _login(client, admin.email, "Secret123!")
    drh_token = _login(client, drh.email, "Secret123!")
    directeur_token = _login(client, directeur.email, "Secret123!")
    direction_id = _create_direction(client, admin_token, "DIR-NEED-1", "Need Dir")
    fiche_id = _create_fiche(client, directeur_token, direction_id)

    besoin = _create_besoin(client, directeur_token, fiche_id, "Need 1")
    assert besoin["status"] == "DRAFT"

    submitted = client.post(
        f"/besoins/{besoin['id']}/soumettre",
        headers=_auth(directeur_token),
    )
    assert submitted.status_code == 200
    submitted_body = submitted.json()["data"]
    assert submitted_body["status"] == "SUBMITTED"
    assert submitted_body["submitted_by_id"] == directeur.id

    approved = client.post(
        f"/besoins/{besoin['id']}/approuver",
        headers=_auth(drh_token),
    )
    assert approved.status_code == 200
    approved_body = approved.json()["data"]
    assert approved_body["status"] == "APPROVED"
    assert approved_body["processed_by_id"] == drh.id

    rejected_besoin = _create_besoin(client, directeur_token, fiche_id, "Need 2")
    client.post(
        f"/besoins/{rejected_besoin['id']}/soumettre",
        headers=_auth(directeur_token),
    )
    rejected = client.post(
        f"/besoins/{rejected_besoin['id']}/rejeter",
        json={"reason": "Reason is detailed enough"},
        headers=_auth(drh_token),
    )
    assert rejected.status_code == 200
    rejected_body = rejected.json()["data"]
    assert rejected_body["status"] == "REJECTED"
    assert rejected_body["rejection_reason"] == "Reason is detailed enough"


def test_invalid_transitions_return_409(
    client: TestClient,
    make_user: Callable[..., User],
) -> None:
    admin = make_user("admin2@need.test", "Secret123!", role=UserRole.ADMIN)
    drh = make_user("drh2@need.test", "Secret123!", role=UserRole.DRH)
    directeur = make_user("dir2@need.test", "Secret123!", role=UserRole.DIRECTEUR)

    admin_token = _login(client, admin.email, "Secret123!")
    drh_token = _login(client, drh.email, "Secret123!")
    directeur_token = _login(client, directeur.email, "Secret123!")
    direction_id = _create_direction(client, admin_token, "DIR-NEED-2", "Need Dir 2")
    fiche_id = _create_fiche(client, directeur_token, direction_id)

    draft_need = _create_besoin(client, directeur_token, fiche_id, "Need draft")
    submitted = client.post(
        f"/besoins/{draft_need['id']}/soumettre",
        headers=_auth(directeur_token),
    )
    assert submitted.status_code == 200

    approved = client.post(
        f"/besoins/{draft_need['id']}/approuver",
        headers=_auth(drh_token),
    )
    assert approved.status_code == 200

    approve_approved = client.post(
        f"/besoins/{draft_need['id']}/approuver",
        headers=_auth(drh_token),
    )
    assert approve_approved.status_code == 409
    assert approve_approved.json()["code"] == "RECRUTEMENT_INVALID_TRANSITION"

    second_need = _create_besoin(client, directeur_token, fiche_id, "Need second")
    reject_draft = client.post(
        f"/besoins/{second_need['id']}/rejeter",
        json={"reason": "This reason is long enough"},
        headers=_auth(drh_token),
    )
    assert reject_draft.status_code == 409
    assert reject_draft.json()["code"] == "RECRUTEMENT_INVALID_TRANSITION"

    third_need = _create_besoin(client, directeur_token, fiche_id, "Need third")
    submit_third = client.post(
        f"/besoins/{third_need['id']}/soumettre",
        headers=_auth(directeur_token),
    )
    assert submit_third.status_code == 200

    resubmit = client.post(
        f"/besoins/{third_need['id']}/soumettre",
        headers=_auth(directeur_token),
    )
    assert resubmit.status_code == 409
    assert resubmit.json()["code"] == "RECRUTEMENT_INVALID_TRANSITION"

    client.post(
        f"/besoins/{third_need['id']}/rejeter",
        json={"reason": "This reason is long enough"},
        headers=_auth(drh_token),
    )
    after_rejected_approve = client.post(
        f"/besoins/{third_need['id']}/approuver",
        headers=_auth(drh_token),
    )
    assert after_rejected_approve.status_code == 409
    assert after_rejected_approve.json()["code"] == "RECRUTEMENT_INVALID_TRANSITION"

    after_rejected_reject = client.post(
        f"/besoins/{third_need['id']}/rejeter",
        json={"reason": "This reason is long enough"},
        headers=_auth(drh_token),
    )
    assert after_rejected_reject.status_code == 409
    assert after_rejected_reject.json()["code"] == "RECRUTEMENT_INVALID_TRANSITION"

    after_rejected_submit = client.post(
        f"/besoins/{third_need['id']}/soumettre",
        headers=_auth(directeur_token),
    )
    assert after_rejected_submit.status_code == 409
    assert after_rejected_submit.json()["code"] == "RECRUTEMENT_INVALID_TRANSITION"


def test_409_vs_422_on_reject(
    client: TestClient,
    make_user: Callable[..., User],
) -> None:
    admin = make_user("admin3@need.test", "Secret123!", role=UserRole.ADMIN)
    drh = make_user("drh3@need.test", "Secret123!", role=UserRole.DRH)
    directeur = make_user("dir3@need.test", "Secret123!", role=UserRole.DIRECTEUR)

    admin_token = _login(client, admin.email, "Secret123!")
    drh_token = _login(client, drh.email, "Secret123!")
    directeur_token = _login(client, directeur.email, "Secret123!")
    direction_id = _create_direction(client, admin_token, "DIR-NEED-3", "Need Dir 3")
    fiche_id = _create_fiche(client, directeur_token, direction_id)
    besoin = _create_besoin(client, directeur_token, fiche_id, "Need 3")

    reject_without_reason = client.post(
        f"/besoins/{besoin['id']}/rejeter",
        json={},
        headers=_auth(drh_token),
    )
    assert reject_without_reason.status_code == 422
    assert reject_without_reason.json()["code"] == ErrorCode.VALIDATION_ERROR

    valid_reason_on_draft = client.post(
        f"/besoins/{besoin['id']}/rejeter",
        json={"reason": "This reason is long enough"},
        headers=_auth(drh_token),
    )
    assert valid_reason_on_draft.status_code == 409
    assert valid_reason_on_draft.json()["code"] == "RECRUTEMENT_INVALID_TRANSITION"


def test_rbac_returns_403(
    client: TestClient,
    make_user: Callable[..., User],
) -> None:
    admin = make_user("admin4@need.test", "Secret123!", role=UserRole.ADMIN)
    drh = make_user("drh4@need.test", "Secret123!", role=UserRole.DRH)
    directeur = make_user("dir4@need.test", "Secret123!", role=UserRole.DIRECTEUR)

    admin_token = _login(client, admin.email, "Secret123!")
    drh_token = _login(client, drh.email, "Secret123!")
    directeur_token = _login(client, directeur.email, "Secret123!")
    direction_id = _create_direction(client, admin_token, "DIR-NEED-4", "Need Dir 4")
    fiche_id = _create_fiche(client, directeur_token, direction_id)
    besoin = _create_besoin(client, directeur_token, fiche_id, "Need 4")

    submit_forbidden = client.post(
        f"/besoins/{besoin['id']}/soumettre",
        headers=_auth(drh_token),
    )
    assert submit_forbidden.status_code == 403
    assert submit_forbidden.json()["code"] == ErrorCode.FORBIDDEN

    approve_forbidden = client.post(
        f"/besoins/{besoin['id']}/approuver",
        headers=_auth(directeur_token),
    )
    assert approve_forbidden.status_code == 403
    assert approve_forbidden.json()["code"] == ErrorCode.FORBIDDEN

    reject_forbidden = client.post(
        f"/besoins/{besoin['id']}/rejeter",
        json={"reason": "This reason is long enough"},
        headers=_auth(directeur_token),
    )
    assert reject_forbidden.status_code == 403
    assert reject_forbidden.json()["code"] == ErrorCode.FORBIDDEN


def test_404_for_missing_besoin_and_invalid_fiche_fk(
    client: TestClient,
    make_user: Callable[..., User],
) -> None:
    admin = make_user("admin5@need.test", "Secret123!", role=UserRole.ADMIN)
    directeur = make_user("dir5@need.test", "Secret123!", role=UserRole.DIRECTEUR)

    admin_token = _login(client, admin.email, "Secret123!")
    directeur_token = _login(client, directeur.email, "Secret123!")
    direction_id = _create_direction(client, admin_token, "DIR-NEED-5", "Need Dir 5")
    _create_fiche(client, directeur_token, direction_id)

    missing = client.get("/besoins/9999", headers=_auth(admin_token))
    assert missing.status_code == 404
    assert missing.json()["code"] == "RECRUTEMENT_BESOIN_NOT_FOUND"

    invalid_fk = client.post(
        "/besoins/",
        json={
            "title": "Invalid",
            "description": "Description",
            "positions_count": 1,
            "fiche_de_poste_id": 9999,
        },
        headers=_auth(directeur_token),
    )
    assert invalid_fk.status_code == 404
    assert invalid_fk.json()["code"] == "FICHES_NOT_FOUND"
