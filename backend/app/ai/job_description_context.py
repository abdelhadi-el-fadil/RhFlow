"""Structured context used to generate a LinkedIn job offer."""

from __future__ import annotations

import re
from datetime import date

from pydantic import BaseModel, ConfigDict

from app.domains.recruitment.model import ProjetRecrutement


class JobDescriptionContext(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    intitule_poste: str
    direction_nom: str
    mission_principale: str
    activites_principales: str
    competences_techniques: str
    competences_manageriales: str
    niveau_etudes: str
    domaine_formation: str
    annees_experience: int
    nombre_postes: int
    priorite: str
    date_souhaitee: date
    objet_candidature: str

    @classmethod
    def from_projet(cls, projet: ProjetRecrutement) -> JobDescriptionContext:
        besoin = projet.besoin_recrutement
        fiche = besoin.fiche_de_poste if besoin else None
        direction = fiche.direction if fiche else None

        return cls(
            intitule_poste=fiche.title if fiche else "",
            direction_nom=direction.name if direction else "",
            mission_principale=fiche.missions if fiche else "",
            activites_principales=fiche.main_activities if fiche else "",
            competences_techniques=(fiche.technical_skills or "") if fiche else "",
            competences_manageriales=(fiche.managerial_skills or "") if fiche else "",
            niveau_etudes=(fiche.education_level or "") if fiche else "",
            domaine_formation=(fiche.formation_domain or "") if fiche else "",
            annees_experience=_extract_years(fiche.experience_level if fiche else ""),
            nombre_postes=(besoin.positions_count or 0) if besoin else 0,
            priorite=(besoin.priority.value if besoin else ""),
            date_souhaitee=(
                besoin.desired_date if besoin and besoin.desired_date else date.today()
            ),
            objet_candidature=projet.email_subject or "",
        )

    def to_prompt_text(self) -> str:
        return f"""## Fiche de poste
- **Intitulé**                : {self.intitule_poste}
- **Direction**               : {self.direction_nom}
- **Mission principale**      : {self.mission_principale}
- **Activités**               : {self.activites_principales}
- **Compétences techniques**  : {self.competences_techniques}
- **Compétences managériales**: {self.competences_manageriales}
- **Niveau d'études**         : {self.niveau_etudes}
- **Domaine de formation**    : {self.domaine_formation}
- **Expérience requise**      : {self.annees_experience} an(s)

## Recrutement
- **Nombre de postes** : {self.nombre_postes}
- **Priorité**         : {self.priorite}
- **Prise de poste**   : {self.date_souhaitee.strftime("%d/%m/%Y")}
- **Objet candidature**: {self.objet_candidature}
"""


def _extract_years(experience_level: str) -> int:
    match = re.search(r"\d+", experience_level or "")
    if match is None:
        return 0
    return int(match.group())
