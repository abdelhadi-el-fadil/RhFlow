"""Service - candidatures domain."""

from __future__ import annotations

import os
import tempfile
from datetime import datetime, timezone
from typing import Protocol
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.ai.providers.llm.configuration import configure_llm
from app.ai.service.cv.analysis_agents_service import (
    EvaluationCv,
    evaluate_cv,
    extract_candidat_info,
    sanitize_candidate_identity,
)
from app.ai.service.cv.extraction_service import extract_cv_to_markdown
from app.core.exceptions import ForbiddenException
from app.core.logging import logger
from app.core.minio_service import MinioStorageServiceError
from app.core.schemas import PaginationParams
from app.database import SessionLocal
from app.domains.candidatures.enums import CandidatureStatut, RecommandationIA
from app.domains.candidatures.error_messages import humanize_candidature_error
from app.domains.candidatures.exceptions import (
    CandidatureAnalysisInProgressException,
    CandidatureFileTooLargeException,
    CandidatureFileTypeNotAllowedException,
    CandidatureNotFoundException,
    CandidatureStorageException,
)
from app.domains.candidatures.model import Candidature
from app.domains.recruitment.model import BesoinRecrutement, ProjetRecrutement
from app.domains.recruitment.service import get_project
from app.domains.users.model import User

ALLOWED_CANDIDATURE_CONTENT_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
}
ALLOWED_CANDIDATURE_EXTENSIONS = {"pdf", "png", "jpg", "jpeg"}
MAX_CANDIDATURE_FILE_SIZE_BYTES = 10 * 1024 * 1024
CANDIDATURE_IN_PROGRESS_TIMEOUT_SECONDS = 8 * 60


class CandidatureStorage(Protocol):
    def upload_bytes(
        self, object_key: str, payload: bytes, content_type: str
    ) -> None: ...

    def delete_object(self, object_key: str) -> None: ...

    def download_bytes(self, object_key: str) -> bytes: ...


def _normalize_filename(filename: str) -> str:
    keep = [ch if ch.isalnum() or ch in {".", "_", "-"} else "-" for ch in filename]
    normalized = "".join(keep).strip("-.")
    return (normalized or "cv")[:160]


def _slugify_segment(value: str) -> str:
    lowered = value.lower()
    keep = [ch if ch.isalnum() or ch in {"-", "_"} else "-" for ch in lowered]
    compact = "".join(keep)
    while "--" in compact:
        compact = compact.replace("--", "-")
    return compact.strip("-") or "unknown"


def _build_candidature_object_key(project: ProjetRecrutement, filename: str) -> str:
    besoin = project.besoin_recrutement
    fiche = besoin.fiche_de_poste if besoin else None
    direction = fiche.direction if fiche else None

    direction_base = "direction-unknown"
    if direction:
        human = direction.code or direction.name or "direction"
        direction_base = f"direction-{direction.id}-{human}"

    fiche_base = "fiche-de-poste-unknown"
    if fiche:
        human = fiche.title or "fiche"
        fiche_base = f"fiche-de-poste-{fiche.id}-{human}"

    direction_segment = _slugify_segment(direction_base)
    fiche_segment = _slugify_segment(fiche_base)
    safe_filename = _normalize_filename(filename)

    return f"{direction_segment}/{fiche_segment}/cvs/{uuid4()}-{safe_filename}"


def _extension(filename: str) -> str:
    return filename.rsplit(".", maxsplit=1)[-1].lower() if "." in filename else ""


def _is_allowed_file(filename: str, content_type: str) -> bool:
    ext_ok = _extension(filename) in ALLOWED_CANDIDATURE_EXTENSIONS
    content_ok = content_type in ALLOWED_CANDIDATURE_CONTENT_TYPES
    return ext_ok or content_ok


def _load_candidature_for_pipeline(db: Session, candidature_id: int) -> Candidature:
    candidature = db.scalars(
        select(Candidature)
        .options(
            selectinload(Candidature.projet_recrutement)
            .selectinload(ProjetRecrutement.besoin_recrutement)
            .selectinload(BesoinRecrutement.fiche_de_poste)
        )
        .where(Candidature.id == candidature_id, Candidature.is_deleted.is_(False))
    ).first()
    if candidature is None:
        raise CandidatureNotFoundException()
    return candidature


def _build_fiche_de_poste_context(candidature: Candidature) -> str:
    projet = candidature.projet_recrutement
    besoin = projet.besoin_recrutement if projet else None
    fiche = besoin.fiche_de_poste if besoin else None
    if fiche is None:
        return "Aucune fiche de poste detaillee disponible pour ce projet."

    parts = [
        f"Titre du poste: {fiche.title}",
        f"Activites principales: {fiche.main_activities}",
        f"Missions: {fiche.missions}",
        f"Niveau d'experience: {fiche.experience_level}",
        f"Domaine de formation: {fiche.formation_domain or '-'}",
        f"Niveau d'etudes: {fiche.education_level or '-'}",
        f"Competences techniques: {fiche.technical_skills or '-'}",
        f"Competences manageriales: {fiche.managerial_skills or '-'}",
    ]
    return "\n".join(parts)


def _download_to_tempfile(
    storage: CandidatureStorage, object_key: str, suffix: str
) -> str:
    payload = storage.download_bytes(object_key)
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(payload)
        return tmp.name


def _parse_uploaded_payload_to_markdown(filename: str, payload: bytes) -> str:
    suffix = f".{_extension(filename)}" if _extension(filename) else ".pdf"
    temp_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(payload)
            temp_path = tmp.name
        return extract_cv_to_markdown(temp_path)
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


def list_candidatures(
    db: Session,
    params: PaginationParams,
    projet_id: int,
    current_user: User,
) -> tuple[list[Candidature], int]:
    _ = get_project(db, projet_id, current_user)
    base_query = (
        select(Candidature)
        .where(
            Candidature.projet_recrutement_id == projet_id,
            Candidature.is_deleted.is_(False),
            Candidature.statut != CandidatureStatut.ERREUR,
        )
        .order_by(Candidature.id.desc())
    )
    items = list(
        db.scalars(base_query.offset(params.offset).limit(params.page_size)).all()
    )
    total_items = db.scalar(
        select(func.count())
        .select_from(Candidature)
        .where(
            Candidature.projet_recrutement_id == projet_id,
            Candidature.is_deleted.is_(False),
            Candidature.statut != CandidatureStatut.ERREUR,
        )
    )
    return items, int(total_items or 0)


def list_errored_candidatures(
    db: Session,
    params: PaginationParams,
    current_user: User,
) -> tuple[list[Candidature], int]:
    base_query = (
        select(Candidature)
        .options(selectinload(Candidature.projet_recrutement))
        .where(
            Candidature.is_deleted.is_(False),
            Candidature.statut == CandidatureStatut.ERREUR,
        )
        .order_by(Candidature.id.desc())
    )

    items = list(db.scalars(base_query).all())
    visible_items: list[Candidature] = []
    for item in items:
        try:
            get_project(db, item.projet_recrutement_id, current_user)
        except ForbiddenException:
            continue
        visible_items.append(item)
    total_items = len(visible_items)
    visible_items = visible_items[params.offset : params.offset + params.page_size]
    return visible_items, total_items


def get_candidature(
    db: Session,
    candidature_id: int,
    current_user: User,
) -> Candidature:
    candidature = db.scalars(
        select(Candidature)
        .options(selectinload(Candidature.projet_recrutement))
        .where(
            Candidature.id == candidature_id,
            Candidature.is_deleted.is_(False),
        )
    ).first()
    if candidature is None:
        raise CandidatureNotFoundException()

    _ = get_project(db, candidature.projet_recrutement_id, current_user)
    return candidature


def delete_candidature(
    db: Session,
    candidature_id: int,
    current_user: User,
    storage: CandidatureStorage,
) -> Candidature:
    candidature = get_candidature(db, candidature_id, current_user)

    candidature.is_deleted = True
    candidature.deleted_at = datetime.now(timezone.utc)
    candidature.updated_by_id = current_user.id
    db.add(candidature)
    db.flush()

    try:
        storage.delete_object(candidature.chemin_minio)
    except MinioStorageServiceError as exc:
        raise CandidatureStorageException(str(exc)) from exc

    return candidature


def requeue_candidature_analysis(
    db: Session,
    candidature_id: int,
    current_user: User,
) -> Candidature:
    candidature = get_candidature(db, candidature_id, current_user)

    candidature.nom_candidat = None
    candidature.email_candidat = None
    candidature.telephone_candidat = None
    candidature.formations = None
    candidature.experiences = None
    candidature.skills = None

    candidature.score_matching = None
    candidature.points_forts = None
    candidature.points_manquants = None
    candidature.recommandation = None
    candidature.justification_ia = None
    candidature.questions_entretien = None

    candidature.statut = CandidatureStatut.RECU
    candidature.evalue_le = None
    candidature.updated_by_id = current_user.id
    db.add(candidature)
    db.flush()
    db.refresh(candidature)
    return candidature


def create_uploaded_candidature(
    db: Session,
    projet_recrutement_id: int,
    current_user: User,
    storage: CandidatureStorage,
    filename: str,
    content_type: str,
    payload: bytes,
) -> Candidature:
    safe_filename = _normalize_filename(filename)

    if not _is_allowed_file(filename, content_type):
        raise CandidatureFileTypeNotAllowedException()
    if len(payload) > MAX_CANDIDATURE_FILE_SIZE_BYTES:
        raise CandidatureFileTooLargeException(MAX_CANDIDATURE_FILE_SIZE_BYTES)

    project = get_project(db, projet_recrutement_id, current_user)
    object_key = _build_candidature_object_key(project, filename)

    try:
        storage.upload_bytes(
            object_key=object_key,
            payload=payload,
            content_type=content_type,
        )
    except MinioStorageServiceError as exc:
        raise CandidatureStorageException(str(exc)) from exc
    except Exception:
        try:
            storage.delete_object(object_key)
        except MinioStorageServiceError:
            pass
        raise

    candidature = Candidature(
        projet_recrutement_id=project.id,
        nom_fichier=safe_filename,
        chemin_minio=object_key,
        type_fichier=content_type,
        taille_fichier=len(payload),
        contenu_markdown=None,
        statut=CandidatureStatut.EN_COURS,
        created_by_id=current_user.id,
        updated_by_id=current_user.id,
    )
    db.add(candidature)
    db.flush()
    db.refresh(candidature)
    return candidature


def _mark_candidature_error(
    db: Session, candidature: Candidature, message: str
) -> None:
    candidature.statut = CandidatureStatut.ERREUR
    readable_message = humanize_candidature_error(message)
    if readable_message and readable_message != message:
        candidature.justification_ia = (
            f"{readable_message}\n\nDetail technique: {message[:3400]}"
        )
    else:
        candidature.justification_ia = message[:4000]
    db.add(candidature)


def _coerce_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _is_stale_in_progress(candidature: Candidature) -> bool:
    if candidature.statut != CandidatureStatut.EN_COURS:
        return False
    updated_at = _coerce_utc(getattr(candidature, "updated_at", None))
    if updated_at is None:
        return False
    age_seconds = (datetime.now(timezone.utc) - updated_at).total_seconds()
    return age_seconds >= CANDIDATURE_IN_PROGRESS_TIMEOUT_SECONDS


def _recover_stale_in_progress(candidature: Candidature, current_user: User) -> None:
    candidature.statut = CandidatureStatut.ERREUR
    candidature.justification_ia = (
        "Analyse precedente interrompue (timeout). Nouvelle tentative relancee."
    )
    candidature.updated_by_id = current_user.id


def _apply_evaluation_result(
    db: Session,
    candidature: Candidature,
    evaluation: EvaluationCv,
) -> None:
    candidature.score_matching = evaluation.score_matching
    candidature.points_forts = evaluation.points_forts
    candidature.points_manquants = evaluation.points_manquants
    candidature.recommandation = RecommandationIA(evaluation.recommandation.value)
    candidature.justification_ia = evaluation.justification_ia
    candidature.questions_entretien = evaluation.questions_entretien

    candidature.statut = CandidatureStatut.EVALUE
    candidature.evalue_le = datetime.now(timezone.utc)
    db.add(candidature)


def _extract_and_apply_candidate_info(
    db: Session,
    candidature: Candidature,
    cv_markdown: str,
) -> None:
    candidat_info = extract_candidat_info(cv_markdown)

    if candidat_info.email:
        duplicate = db.scalars(
            select(Candidature).where(
                Candidature.projet_recrutement_id == candidature.projet_recrutement_id,
                Candidature.email_candidat == candidat_info.email,
                Candidature.id != candidature.id,
                Candidature.is_deleted.is_(False),
            )
        ).first()
        if duplicate is not None:
            raise ValueError("Duplicate candidate email for the same project")

    candidature.nom_candidat = candidat_info.nom
    candidature.email_candidat = candidat_info.email
    candidature.telephone_candidat = candidat_info.telephone
    candidature.formations = [
        {
            "titre": item.titre,
            "dateObtention": item.date_obtention or "",
        }
        for item in candidat_info.formations
    ]
    candidature.experiences = [
        {
            "titre": item.titre,
            "entreprise": item.entreprise or "",
            "periode": item.periode or "",
        }
        for item in candidat_info.experiences
    ]
    candidature.skills = candidat_info.skills
    db.add(candidature)


def _parse_cv_markdown(candidature: Candidature, storage: CandidatureStorage) -> str:
    if candidature.contenu_markdown and candidature.contenu_markdown.strip():
        return candidature.contenu_markdown.strip()

    temp_path: str | None = None
    try:
        suffix = (
            f".{_extension(candidature.nom_fichier)}"
            if _extension(candidature.nom_fichier)
            else ".pdf"
        )
        temp_path = _download_to_tempfile(storage, candidature.chemin_minio, suffix)
        return extract_cv_to_markdown(temp_path)
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


def start_candidature_extraction(
    db: Session,
    candidature_id: int,
    current_user: User,
) -> Candidature:
    candidature = get_candidature(db, candidature_id, current_user)
    if candidature.statut == CandidatureStatut.EN_COURS:
        if _is_stale_in_progress(candidature):
            _recover_stale_in_progress(candidature, current_user)
        else:
            raise CandidatureAnalysisInProgressException()

    candidature.statut = CandidatureStatut.EN_COURS
    candidature.updated_by_id = current_user.id

    candidature.nom_candidat = None
    candidature.email_candidat = None
    candidature.telephone_candidat = None
    candidature.formations = None
    candidature.experiences = None
    candidature.skills = None

    candidature.score_matching = None
    candidature.points_forts = None
    candidature.points_manquants = None
    candidature.recommandation = None
    candidature.justification_ia = None
    candidature.questions_entretien = None
    candidature.evalue_le = None
    candidature.justification_ia = None

    db.add(candidature)
    db.flush()
    db.refresh(candidature)
    return candidature


def start_candidature_evaluation(
    db: Session,
    candidature_id: int,
    current_user: User,
) -> Candidature:
    candidature = get_candidature(db, candidature_id, current_user)
    if candidature.statut == CandidatureStatut.EN_COURS:
        if _is_stale_in_progress(candidature):
            _recover_stale_in_progress(candidature, current_user)
        else:
            raise CandidatureAnalysisInProgressException()

    candidature.statut = CandidatureStatut.EN_COURS
    candidature.updated_by_id = current_user.id

    candidature.score_matching = None
    candidature.points_forts = None
    candidature.points_manquants = None
    candidature.recommandation = None
    candidature.justification_ia = None
    candidature.questions_entretien = None
    candidature.evalue_le = None

    db.add(candidature)
    db.flush()
    db.refresh(candidature)
    return candidature


def process_candidature_extraction(
    candidature_id: int, storage: CandidatureStorage
) -> None:
    db = SessionLocal()
    try:
        candidature = _load_candidature_for_pipeline(db, candidature_id)
        cv_markdown = _parse_cv_markdown(candidature, storage)
        if not cv_markdown.strip():
            raise ValueError("Parsed CV markdown is empty")

        candidature.contenu_markdown = cv_markdown
        _extract_and_apply_candidate_info(db, candidature, cv_markdown)
        candidature.statut = CandidatureStatut.RECU
        candidature.justification_ia = None
        db.add(candidature)
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.error(
            "Candidature extraction failed id=%s error=%s",
            candidature_id,
            exc,
            exc_info=True,
        )
        try:
            candidature = _load_candidature_for_pipeline(db, candidature_id)
            _mark_candidature_error(db, candidature, str(exc))
            db.commit()
        except Exception:
            db.rollback()
    finally:
        db.close()


def process_candidature_evaluation(
    candidature_id: int, storage: CandidatureStorage
) -> None:
    db = SessionLocal()
    try:
        candidature = _load_candidature_for_pipeline(db, candidature_id)
        cv_markdown = _parse_cv_markdown(candidature, storage)
        if not cv_markdown.strip():
            raise ValueError("Parsed CV markdown is empty")

        candidature.contenu_markdown = cv_markdown
        if (
            candidature.nom_candidat is None
            and candidature.email_candidat is None
            and candidature.telephone_candidat is None
            and not candidature.formations
            and not candidature.experiences
            and not candidature.skills
        ):
            _extract_and_apply_candidate_info(db, candidature, cv_markdown)

        safe_nom, safe_email, safe_phone = sanitize_candidate_identity(
            candidature.nom_candidat,
            candidature.email_candidat,
            candidature.telephone_candidat,
            cv_markdown,
        )
        candidature.nom_candidat = safe_nom
        candidature.email_candidat = safe_email
        candidature.telephone_candidat = safe_phone
        db.add(candidature)

        fiche_de_poste = _build_fiche_de_poste_context(candidature)
        evaluation = evaluate_cv(fiche_de_poste, cv_markdown)
        _apply_evaluation_result(db, candidature, evaluation)
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.error(
            "Candidature evaluation failed id=%s error=%s",
            candidature_id,
            exc,
            exc_info=True,
        )
        try:
            candidature = _load_candidature_for_pipeline(db, candidature_id)
            _mark_candidature_error(db, candidature, str(exc))
            db.commit()
        except Exception:
            db.rollback()
    finally:
        db.close()


def process_candidature_pipeline(
    candidature_id: int, storage: CandidatureStorage
) -> None:
    """Run parse + two independent LLM agents and persist final status."""
    configure_llm()
    process_candidature_extraction(candidature_id, storage)
    process_candidature_evaluation(candidature_id, storage)
