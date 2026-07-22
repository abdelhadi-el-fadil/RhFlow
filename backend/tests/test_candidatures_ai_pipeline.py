from collections.abc import Callable
from datetime import date, datetime, timezone

import pytest
from _pytest.monkeypatch import MonkeyPatch
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.ai.service.cv.analysis_agents_service import (
    CandidatInfo,
    EvaluationCv,
    ExperienceInfo,
    FormationInfo,
    RecommendationValue,
)
from app.core.enums import UserRole
from app.core.schemas import PaginationParams
from app.domains.candidatures import service as candidatures_service
from app.domains.candidatures.enums import CandidatureStatut, RecommandationIA
from app.domains.candidatures.error_messages import humanize_candidature_error
from app.domains.candidatures.model import Candidature
from app.domains.directions.model import Direction
from app.domains.fiches_de_poste.model import FicheDePoste
from app.domains.recruitment.enums import BesoinPriority, BesoinStatus, ProjetStatus
from app.domains.recruitment.model import BesoinRecrutement, ProjetRecrutement
from app.domains.users.model import User


class FakeStorage:
    def __init__(self, download_payload: bytes = b"pdf-bytes") -> None:
        self.download_payload = download_payload
        self.uploaded: list[tuple[str, bytes, str]] = []
        self.deleted: list[str] = []

    def upload_bytes(self, object_key: str, payload: bytes, content_type: str) -> None:
        self.uploaded.append((object_key, payload, content_type))

    def delete_object(self, object_key: str) -> None:
        self.deleted.append(object_key)

    def download_bytes(self, object_key: str) -> bytes:
        return self.download_payload


def _create_project_chain(db: Session, user: User) -> ProjetRecrutement:
    direction = Direction(
        name="Direction IA",
        code=f"DIR-AI-{user.id}",
        director_id=user.id,
        created_by_id=user.id,
        updated_by_id=user.id,
    )
    db.add(direction)
    db.flush()

    fiche = FicheDePoste(
        title="Ingenieur IA",
        main_activities="Construire des pipelines IA",
        missions="Extraire et evaluer des CV",
        experience_level="Senior",
        formation_domain="Informatique",
        education_level="Bac+5",
        technical_skills="Python, LLM, FastAPI",
        managerial_skills="Communication",
        direction_id=direction.id,
        created_by_id=user.id,
        updated_by_id=user.id,
    )
    db.add(fiche)
    db.flush()

    besoin = BesoinRecrutement(
        lieu_affectation="Marrakech",
        positions_count=1,
        desired_date=date(2026, 7, 17),
        justification="Renforcer l'equipe IA",
        priority=BesoinPriority.NORMALE,
        status=BesoinStatus.APPROVED,
        fiche_de_poste_id=fiche.id,
        submitted_by_id=user.id,
        created_by_id=user.id,
        updated_by_id=user.id,
    )
    db.add(besoin)
    db.flush()

    projet = ProjetRecrutement(
        status=ProjetStatus.ACTIVE,
        manager_id=user.id,
        besoin_recrutement_id=besoin.id,
        email_subject="Candidature Ingenieur IA",
        offre="Offre IA",
        created_by_id=user.id,
        updated_by_id=user.id,
    )
    db.add(projet)
    db.commit()
    db.refresh(projet)
    return projet


def _session_factory_for_test(db: Session) -> sessionmaker[Session]:
    return sessionmaker(autocommit=False, autoflush=False, bind=db.get_bind())


def test_create_uploaded_candidature_stores_markdown_on_upload(
    db: Session,
    make_user: Callable[..., User],
    monkeypatch: MonkeyPatch,
) -> None:
    user = make_user("ai-upload@test.com", "Secret123!", role=UserRole.ADMIN)
    project = _create_project_chain(db, user)
    storage = FakeStorage()

    candidature = candidatures_service.create_uploaded_candidature(
        db=db,
        projet_recrutement_id=project.id,
        current_user=user,
        storage=storage,
        filename="alice.pdf",
        content_type="application/pdf",
        payload=b"fake-pdf",
    )

    assert candidature.contenu_markdown is None
    assert candidature.statut == CandidatureStatut.EN_COURS
    assert len(storage.uploaded) == 1
    assert storage.deleted == []


def test_create_uploaded_candidature_persists_row_for_background_worker(
    db: Session,
    make_user: Callable[..., User],
) -> None:
    user = make_user("ai-bg@test.com", "Secret123!", role=UserRole.ADMIN)
    project = _create_project_chain(db, user)
    storage = FakeStorage()

    candidature = candidatures_service.create_uploaded_candidature(
        db=db,
        projet_recrutement_id=project.id,
        current_user=user,
        storage=storage,
        filename="bg.pdf",
        content_type="application/pdf",
        payload=b"fake-pdf",
    )
    candidature_id = candidature.id

    db.commit()
    db.expire_all()

    persisted = db.scalar(select(Candidature).where(Candidature.id == candidature_id))
    assert persisted is not None
    assert persisted.statut == CandidatureStatut.EN_COURS


def test_process_candidature_extraction_uses_cached_markdown(
    db: Session,
    make_user: Callable[..., User],
    monkeypatch: MonkeyPatch,
) -> None:
    user = make_user("ai-extract@test.com", "Secret123!", role=UserRole.ADMIN)
    project = _create_project_chain(db, user)
    storage = FakeStorage()

    candidature = Candidature(
        projet_recrutement_id=project.id,
        nom_fichier="alice.pdf",
        chemin_minio="cvs/alice.pdf",
        type_fichier="application/pdf",
        taille_fichier=123,
        contenu_markdown="# CV\nAlice Dupont\nalice@example.com\n+212600000000",
        statut=CandidatureStatut.EN_COURS,
        created_by_id=user.id,
        updated_by_id=user.id,
    )
    db.add(candidature)
    db.commit()
    db.refresh(candidature)

    monkeypatch.setattr(
        candidatures_service, "SessionLocal", _session_factory_for_test(db)
    )
    monkeypatch.setattr(
        candidatures_service,
        "extract_cv_to_markdown",
        lambda path: (_ for _ in ()).throw(AssertionError("parser should not run")),
    )
    monkeypatch.setattr(
        candidatures_service,
        "extract_candidat_info",
        lambda markdown: CandidatInfo.model_construct(
            nom="Alice Dupont",
            email="alice@example.com",
            telephone="+212600000000",
            formations=[FormationInfo(titre="Master IA", date_obtention="2024")],
            experiences=[
                ExperienceInfo(
                    titre="ML Engineer",
                    entreprise="STAPORT",
                    periode="2024-2026",
                )
            ],
            skills=["Python", "FastAPI", "LLM"],
        ),
    )

    candidatures_service.process_candidature_extraction(candidature.id, storage)

    db.expire_all()
    refreshed = db.scalar(select(Candidature).where(Candidature.id == candidature.id))
    assert refreshed is not None
    assert refreshed.nom_candidat == "Alice Dupont"
    assert refreshed.email_candidat == "alice@example.com"
    assert refreshed.telephone_candidat == "+212600000000"
    assert refreshed.formations == [{"titre": "Master IA", "dateObtention": "2024"}]
    assert refreshed.experiences == [
        {
            "titre": "ML Engineer",
            "entreprise": "STAPORT",
            "periode": "2024-2026",
        }
    ]
    assert refreshed.skills == ["Python", "FastAPI", "LLM"]
    assert refreshed.statut == CandidatureStatut.RECU


def test_process_candidature_evaluation_uses_fiche_chain_and_extracted_profile(
    db: Session,
    make_user: Callable[..., User],
    monkeypatch: MonkeyPatch,
) -> None:
    user = make_user("ai-eval@test.com", "Secret123!", role=UserRole.ADMIN)
    project = _create_project_chain(db, user)
    storage = FakeStorage()

    candidature = Candidature(
        projet_recrutement_id=project.id,
        nom_fichier="alice.pdf",
        chemin_minio="cvs/alice.pdf",
        type_fichier="application/pdf",
        taille_fichier=123,
        contenu_markdown="# CV\nAlice Dupont\nML Engineer\nPython\nFastAPI",
        nom_candidat="Alice Dupont",
        email_candidat="alice@example.com",
        telephone_candidat="+212600000000",
        formations=[{"titre": "Master IA", "dateObtention": "2024"}],
        experiences=[
            {
                "titre": "ML Engineer",
                "entreprise": "STAPORT",
                "periode": "2024-2026",
            }
        ],
        statut=CandidatureStatut.EN_COURS,
        created_by_id=user.id,
        updated_by_id=user.id,
    )
    db.add(candidature)
    db.commit()
    db.refresh(candidature)

    captured: dict[str, str] = {}

    monkeypatch.setattr(
        candidatures_service, "SessionLocal", _session_factory_for_test(db)
    )
    monkeypatch.setattr(
        candidatures_service,
        "extract_cv_to_markdown",
        lambda path: (_ for _ in ()).throw(AssertionError("parser should not run")),
    )
    monkeypatch.setattr(
        candidatures_service,
        "extract_candidat_info",
        lambda markdown: (_ for _ in ()).throw(
            AssertionError("re-extraction should not run")
        ),
    )

    def _fake_evaluate_cv(fiche_de_poste: str, cv_markdown: str) -> EvaluationCv:
        captured["fiche_de_poste"] = fiche_de_poste
        captured["cv_markdown"] = cv_markdown
        return EvaluationCv(
            score_matching=87,
            points_forts=["Python", "LLM", "FastAPI"],
            points_manquants=[
                "Docker avance",
                "MLOps production",
                "Management d'equipe",
            ],
            recommandation=RecommendationValue.A_CONVOQUER,
            justification_ia="Profil solide et coherent avec la fiche de poste.",
            questions_entretien=[
                "Comment structurez-vous un pipeline d'extraction CV ?",
                "Comment validez-vous la qualite d'une evaluation LLM ?",
                "Quel a ete votre principal projet FastAPI ?",
                "Comment priorisez-vous les controles de qualite sur des sorties IA ?",
                "Quelle experience avez-vous de la mise en production d'API Python ?",
                (
                    "Comment detectez-vous les erreurs de parsing sur des "
                    "documents reels ?"
                ),
                (
                    "Comment rapprochez-vous les exigences d'une fiche avec un "
                    "CV incomplet ?"
                ),
            ],
        )

    monkeypatch.setattr(candidatures_service, "evaluate_cv", _fake_evaluate_cv)

    candidatures_service.process_candidature_evaluation(candidature.id, storage)

    db.expire_all()
    refreshed = db.scalar(
        select(Candidature).where(Candidature.id == candidature.id)
        )
    assert refreshed is not None
    assert refreshed.score_matching == 87
    assert refreshed.recommandation == RecommandationIA.A_CONVOQUER
    assert refreshed.points_forts == ["Python", "LLM", "FastAPI"]
    assert refreshed.statut == CandidatureStatut.EVALUE
    assert "Ingenieur IA" in captured["fiche_de_poste"]
    assert "Python, LLM, FastAPI" in captured["fiche_de_poste"]
    assert captured["cv_markdown"] == candidature.contenu_markdown


def test_list_candidatures_excludes_errored_items_from_project_page(
    db: Session,
    make_user: Callable[..., User],
) -> None:
    user = make_user("ai-list@test.com", "Secret123!", role=UserRole.ADMIN)
    project = _create_project_chain(db, user)

    ok_candidature = Candidature(
        projet_recrutement_id=project.id,
        nom_fichier="ok.pdf",
        chemin_minio="cvs/ok.pdf",
        type_fichier="application/pdf",
        taille_fichier=100,
        statut=CandidatureStatut.EVALUE,
        created_by_id=user.id,
        updated_by_id=user.id,
    )
    error_candidature = Candidature(
        projet_recrutement_id=project.id,
        nom_fichier="error.pdf",
        chemin_minio="cvs/error.pdf",
        type_fichier="application/pdf",
        taille_fichier=100,
        statut=CandidatureStatut.ERREUR,
        justification_ia="Parsed CV markdown is empty",
        created_by_id=user.id,
        updated_by_id=user.id,
    )
    db.add_all([ok_candidature, error_candidature])
    db.commit()

    items, total = candidatures_service.list_candidatures(
        db,
        PaginationParams(page=1, page_size=100),
        project.id,
        user,
    )

    assert total == 1
    assert [item.id for item in items] == [ok_candidature.id]

    fetched_error = candidatures_service.get_candidature(db,
                                                         error_candidature.id,
                                                         user)
    assert fetched_error.id == error_candidature.id


def test_list_errored_candidatures_skips_orphaned_deleted_projects(
    db: Session,
    make_user: Callable[..., User],
) -> None:
    _, baseline_total = candidatures_service.list_errored_candidatures(
        db,
        PaginationParams(page=1, page_size=100),
        make_user("ai-errors-baseline@test.com", "Secret123!", role=UserRole.ADMIN),
    )

    user = make_user("ai-errors@test.com", "Secret123!", role=UserRole.ADMIN)
    other_user = make_user(
        "ai-errors-2@test.com", "Secret123!", role=UserRole.ADMIN
    )
    visible_project = _create_project_chain(db, user)
    deleted_project = _create_project_chain(db, other_user)

    deleted_project.is_deleted = True
    deleted_project.deleted_at = datetime.now(timezone.utc)
    deleted_project.updated_by_id = user.id

    visible_error = Candidature(
        projet_recrutement_id=visible_project.id,
        nom_fichier="visible-error.pdf",
        chemin_minio="cvs/visible-error.pdf",
        type_fichier="application/pdf",
        taille_fichier=100,
        statut=CandidatureStatut.ERREUR,
        justification_ia="LLM evaluation failed",
        created_by_id=user.id,
        updated_by_id=user.id,
    )
    orphaned_error = Candidature(
        projet_recrutement_id=deleted_project.id,
        nom_fichier="orphaned-error.pdf",
        chemin_minio="cvs/orphaned-error.pdf",
        type_fichier="application/pdf",
        taille_fichier=100,
        statut=CandidatureStatut.ERREUR,
        justification_ia="LLM extraction failed",
        created_by_id=user.id,
        updated_by_id=user.id,
    )
    db.add_all([visible_error, orphaned_error, deleted_project])
    db.commit()

    items, total = candidatures_service.list_errored_candidatures(
        db,
        PaginationParams(page=1, page_size=100),
        user,
    )

    item_ids = [item.id for item in items]
    assert total == baseline_total + 1
    assert visible_error.id in item_ids
    assert orphaned_error.id not in item_ids


def test_extract_candidate_info_normalizes_email_and_detects_duplicate_case_insensitive(
    db: Session,
    make_user: Callable[..., User],
    monkeypatch: MonkeyPatch,
) -> None:
    user = make_user("ai-dup@test.com", "Secret123!", role=UserRole.ADMIN)
    project = _create_project_chain(db, user)

    existing = Candidature(
        projet_recrutement_id=project.id,
        nom_fichier="existing.pdf",
        chemin_minio="cvs/existing.pdf",
        type_fichier="application/pdf",
        taille_fichier=100,
        statut=CandidatureStatut.EVALUE,
        email_candidat="Abdellhadi.elfadil@gmail.com",
        created_by_id=user.id,
        updated_by_id=user.id,
    )
    incoming = Candidature(
        projet_recrutement_id=project.id,
        nom_fichier="incoming.pdf",
        chemin_minio="cvs/incoming.pdf",
        type_fichier="application/pdf",
        taille_fichier=100,
        statut=CandidatureStatut.EN_COURS,
        created_by_id=user.id,
        updated_by_id=user.id,
    )
    db.add_all([existing, incoming])
    db.commit()
    db.refresh(incoming)

    monkeypatch.setattr(
        candidatures_service,
        "extract_candidat_info",
        lambda markdown: CandidatInfo.model_construct(
            nom="EL FADIL Abdelhadi",
            email="abdellhadi.elfadil@gmail.com",
            telephone="+212654099755",
            formations=[],
            experiences=[],
            skills=[],
        ),
    )

    with pytest.raises(ValueError, match="Duplicate candidate email"):
        candidatures_service._extract_and_apply_candidate_info(db, incoming, "# CV")


def test_humanize_error_does_not_map_css3_to_storage() -> None:
    detail = "Skill list includes CSS3 and PostgreSQL"
    message = humanize_candidature_error(detail)
    assert message is not None
    assert "stockage" not in message.lower()


def test_humanize_error_maps_retry_budget_to_clear_message() -> None:
    detail = (
        "LLM cv_extraction exhausted retry budget after 1 attempt(s); "
        "25.00s remaining is below the per-call timeout of 30s"
    )
    message = humanize_candidature_error(detail)
    assert message is not None
    assert "temps imparti" in message.lower()


def test_humanize_error_maps_llm_structured_output_failures_to_clear_message() -> None:
    detail = "LLM evaluation missing score_matching"
    message = humanize_candidature_error(detail)
    assert message is not None
    assert "format attendu" in message.lower()
