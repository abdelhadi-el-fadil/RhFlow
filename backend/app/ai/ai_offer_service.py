"""Offer-generation service for recruitment projects."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.ai.job_announcement_generator import generate_job_announcement
from app.ai.job_description_context import JobDescriptionContext
from app.core.logging import logger
from app.database import SessionLocal
from app.domains.recruitment.service import get_project as get_recruitment_project
from app.domains.users.model import User


def build_validated_prompt(
    projet_id: int,
    db: Session | None = None,
    current_user: User | None = None,
) -> str:
    owns_db = db is None
    session = db or SessionLocal()
    try:
        projet = get_recruitment_project(session, projet_id, current_user)
        besoin = projet.besoin_recrutement
        fiche = besoin.fiche_de_poste if besoin else None
        logger.info(
            "ai.generate_offer projet_id=%s poste_title=%s objet_candidature=%s",
            projet.id,
            fiche.title if fiche else None,
            projet.email_subject,
        )
        return JobDescriptionContext.from_projet(projet).to_prompt_text()
    finally:
        if owns_db:
            session.close()


def generate_sync(prompt: str) -> str:
    return generate_job_announcement(prompt)
