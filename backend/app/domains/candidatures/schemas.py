"""Pydantic schemas - candidatures domain."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.domains.candidatures.enums import CandidatureStatut, RecommandationIA


class FormationExtraite(BaseModel):
    titre: str
    dateObtention: str | None = None


class ExperienceExtraite(BaseModel):
    titre: str
    entreprise: str | None = None
    periode: str | None = None


class CandidatureResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    projet_recrutement_id: int
    nom_fichier: str
    chemin_minio: str
    type_fichier: str
    taille_fichier: int | None
    contenu_markdown: str | None
    nom_candidat: str | None
    email_candidat: str | None
    telephone_candidat: str | None
    formations: list[FormationExtraite] | None
    experiences: list[ExperienceExtraite] | None
    skills: list[str] | None
    score_matching: int | None
    points_forts: list[str] | None
    points_manquants: list[str] | None
    recommandation: RecommandationIA | None
    justification_ia: str | None
    questions_entretien: list[str] | None
    statut: CandidatureStatut
    depose_le: datetime
    evalue_le: datetime | None
    version: int
    created_by_id: int | None
    updated_by_id: int | None
