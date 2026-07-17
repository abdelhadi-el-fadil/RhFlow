"""Database seeder with complete demo data.

Seeds:
- users
- directions
- fiches de poste
- projets recrutement
- besoins recrutement

Run AFTER migrations have been applied:
    python -m alembic upgrade head
    python -m app.seed

Idempotent: existing rows (matched on stable business keys) are not duplicated.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import cast

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.enums import UserRole
from app.core.security import hash_password
from app.database import SessionLocal
from app.domains.directions.model import Direction
from app.domains.fiches_de_poste.model import FicheDePoste
from app.domains.recruitment.enums import BesoinStatus
from app.domains.recruitment.model import BesoinRecrutement, ProjetRecrutement
from app.domains.users.model import User


@dataclass(frozen=True)
class SeedCounters:
    created: int = 0
    skipped: int = 0

    def add_created(self) -> SeedCounters:
        return SeedCounters(created=self.created + 1, skipped=self.skipped)

    def add_skipped(self) -> SeedCounters:
        return SeedCounters(created=self.created, skipped=self.skipped + 1)


SEED_USERS: list[dict[str, object]] = [
    {
        "email": "admin@example.com",
        "full_name": "System Admin",
        "password": "Admin123",
        "role": UserRole.ADMIN,
        "gsm": "+212600000001",
    },
    {
        "email": "drh@example.com",
        "full_name": "Responsable RH",
        "password": "Drh123",
        "role": UserRole.DRH,
        "gsm": "+212600000002",
    },
    {
        "email": "dg@example.com",
        "full_name": "Directeur General",
        "password": "Dg123",
        "role": UserRole.DG,
        "gsm": "+212600000003",
    },
    {
        "email": "directeur.ops@example.com",
        "full_name": "Directeur des Operations",
        "password": "DirecteurOps123",
        "role": UserRole.DIRECTEUR,
        "gsm": "+212600000004",
    },
    {
        "email": "directeur.it@example.com",
        "full_name": "Directeur Technologie",
        "password": "DirecteurIt123",
        "role": UserRole.DIRECTEUR,
        "gsm": "+212600000005",
    },
    {
        "email": "directeur.hr@example.com",
        "full_name": "Directeur Ressources Humaines",
        "password": "DirecteurHr123",
        "role": UserRole.DIRECTEUR,
        "gsm": "+212600000006",
    },
]

SEED_DIRECTIONS: list[dict[str, object]] = [
    {
        "code": "OPS",
        "name": "Operations",
        "description": "Pilotage des operations et de la production.",
        "director_email": "directeur.ops@example.com",
    },
    {
        "code": "IT",
        "name": "Technologie",
        "description": "Systemes d'information et innovation.",
        "director_email": "directeur.it@example.com",
    },
    {
        "code": "HR",
        "name": "Ressources Humaines",
        "description": "Gestion RH et developpement des talents.",
        "director_email": "directeur.hr@example.com",
    },
]

SEED_FICHES: list[dict[str, object]] = [
    {
        "title": "Chef de Projet RH",
        "main_activities": "Pilote les projets de transformation RH.",
        "missions": (
            "Coordonner les parties prenantes, suivre planning, assurer livraison."
        ),
        "experience_level": "5+ years",
        "formation_domain": "Ressources Humaines / Gestion",
        "education_level": "Bac+5",
        "technical_skills": "MS Project, Jira, reporting RH, SIRH.",
        "managerial_skills": "Leadership, animation d'equipe, conduite du changement.",
        "direction_code": "HR",
    },
    {
        "title": "Ingenieur DevOps",
        "main_activities": "Automatise le deploiement et la fiabilite des plateformes.",
        "missions": "Mettre en place CI/CD, observabilite, securite operationnelle.",
        "experience_level": "3+ years",
        "formation_domain": "Informatique / Systemes",
        "education_level": "Bac+5",
        "technical_skills": "Docker, Kubernetes, Terraform, GitOps, monitoring.",
        "managerial_skills": "Coordination technique, mentorat junior.",
        "direction_code": "IT",
    },
    {
        "title": "Charge de Recrutement",
        "main_activities": "Conduit les campagnes de recrutement.",
        "missions": "Sourcing, entretiens, coordination avec managers.",
        "experience_level": "2+ years",
        "formation_domain": "Ressources Humaines",
        "education_level": "Bac+3",
        "technical_skills": "ATS, LinkedIn Recruiter, sourcing boolean.",
        "managerial_skills": "Organisation, gestion des priorites.",
        "direction_code": "HR",
    },
    {
        "title": "Responsable Production",
        "main_activities": "Supervise les lignes de production et la qualite.",
        "missions": (
            "Planifier la production, garantir la qualite, piloter les equipes terrain."
        ),
        "experience_level": "4+ years",
        "formation_domain": "Genie Industriel",
        "education_level": "Bac+5",
        "technical_skills": "Lean Six Sigma, ERP production, QHSE.",
        "managerial_skills": "Gestion d'equipe terrain, resolution de conflits.",
        "direction_code": "OPS",
    },
]

SEED_PROJECTS: list[dict[str, object]] = []

SEED_BESOINS: list[dict[str, object]] = [
    {
        "key": "devops-senior",
        "lieu_affectation": "Casablanca - IT",
        "positions_count": 2,
        "desired_date": date(2026, 8, 1),
        "justification": "Montee en charge des plateformes critiques.",
        "status": BesoinStatus.APPROVED,
        "fiche_title": "Ingenieur DevOps",
        "submitted_by_email": "directeur.it@example.com",
        "processed_by_email": "drh@example.com",
        "owner_email": "directeur.it@example.com",
    },
    {
        "key": "charge-recrutement",
        "lieu_affectation": "Rabat - RH",
        "positions_count": 1,
        "desired_date": date(2026, 7, 1),
        "justification": "Volume de postes ouverts en forte hausse.",
        "status": BesoinStatus.SUBMITTED,
        "fiche_title": "Charge de Recrutement",
        "submitted_by_email": "directeur.hr@example.com",
        "processed_by_email": None,
        "owner_email": "directeur.hr@example.com",
    },
    {
        "key": "chef-projet-rh",
        "lieu_affectation": "Rabat - RH",
        "positions_count": 1,
        "desired_date": date(2026, 9, 1),
        "justification": "Besoin de coordination transverse.",
        "status": BesoinStatus.REJECTED,
        "fiche_title": "Chef de Projet RH",
        "submitted_by_email": "directeur.hr@example.com",
        "processed_by_email": "drh@example.com",
        "owner_email": "directeur.hr@example.com",
    },
    {
        "key": "responsable-production",
        "lieu_affectation": "Tanger - Operations",
        "positions_count": 1,
        "desired_date": date(2026, 8, 15),
        "justification": "Depart a la retraite du titulaire actuel.",
        "status": BesoinStatus.APPROVED,
        "fiche_title": "Responsable Production",
        "submitted_by_email": "directeur.ops@example.com",
        "processed_by_email": "drh@example.com",
        "owner_email": "directeur.ops@example.com",
    },
]


def _get_user_by_email(db: Session, email: str) -> User:
    user = db.scalars(select(User).where(User.email == email)).first()
    if user is None:
        raise ValueError(f"Missing user for email: {email}")
    return user


def _seed_users(db: Session) -> tuple[dict[str, User], SeedCounters]:
    counters = SeedCounters()
    users_by_email: dict[str, User] = {}

    print("\nSeeding users...")
    for data in SEED_USERS:
        email = str(data["email"])
        existing = db.scalars(select(User).where(User.email == email)).first()
        if existing:
            print(f"  [skip]    {email} already exists")
            users_by_email[email] = existing
            counters = counters.add_skipped()
            continue

        user = User(
            email=email,
            full_name=str(data["full_name"]),
            gsm=str(data["gsm"]),
            hashed_password=hash_password(str(data["password"])),
            role=data["role"],
        )
        db.add(user)
        db.flush()
        users_by_email[email] = user
        print(f"  [created] {email} ({user.role.value})")
        counters = counters.add_created()

    return users_by_email, counters


def _seed_directions(
    db: Session,
    users_by_email: dict[str, User],
) -> tuple[dict[str, Direction], SeedCounters]:
    counters = SeedCounters()
    directions_by_code: dict[str, Direction] = {}
    admin = users_by_email["admin@example.com"]

    print("\nSeeding directions...")
    for data in SEED_DIRECTIONS:
        code = str(data["code"])
        existing = db.scalars(select(Direction).where(Direction.code == code)).first()
        if existing:
            print(f"  [skip]    direction {code} already exists")
            directions_by_code[code] = existing
            counters = counters.add_skipped()
            continue

        director_email = str(data["director_email"])
        direction = Direction(
            name=str(data["name"]),
            code=code,
            description=str(data["description"]),
            director_id=users_by_email[director_email].id,
            created_by_id=admin.id,
            updated_by_id=admin.id,
        )
        db.add(direction)
        db.flush()
        directions_by_code[code] = direction
        print(f"  [created] direction {code} (directeur: {director_email})")
        counters = counters.add_created()

    return directions_by_code, counters


def _seed_fiches(
    db: Session,
    users_by_email: dict[str, User],
    directions_by_code: dict[str, Direction],
) -> tuple[dict[str, FicheDePoste], SeedCounters]:
    counters = SeedCounters()
    fiches_by_title: dict[str, FicheDePoste] = {}
    drh = users_by_email["drh@example.com"]

    print("\nSeeding fiches de poste...")
    for data in SEED_FICHES:
        title = str(data["title"])
        existing = db.scalars(
            select(FicheDePoste).where(FicheDePoste.title == title)
        ).first()
        if existing:
            print(f"  [skip]    fiche '{title}' already exists")
            fiches_by_title[title] = existing
            counters = counters.add_skipped()
            continue

        direction = directions_by_code[str(data["direction_code"])]
        direction_directeur_id = direction.director_id

        fiche = FicheDePoste(
            title=title,
            main_activities=str(data["main_activities"]),
            missions=str(data["missions"]),
            experience_level=str(data["experience_level"]),
            formation_domain=str(data["formation_domain"]),
            education_level=str(data["education_level"]),
            technical_skills=str(data["technical_skills"]),
            managerial_skills=str(data["managerial_skills"]),
            direction_id=direction.id,
            validated_by_id=drh.id,
            created_by_id=direction_directeur_id,
            updated_by_id=direction_directeur_id,
        )
        db.add(fiche)
        db.flush()
        fiches_by_title[title] = fiche
        print(f"  [created] fiche '{title}'")
        counters = counters.add_created()

    return fiches_by_title, counters


def _seed_projects(
    db: Session,
    users_by_email: dict[str, User],
    fiches_by_title: dict[str, FicheDePoste],
) -> tuple[dict[str, ProjetRecrutement], SeedCounters]:
    _ = db
    _ = users_by_email
    _ = fiches_by_title
    print("\nSeeding projets recrutement...")
    if not SEED_PROJECTS:
        print("  [skip]    no standalone project seeds configured")
    return {}, SeedCounters()


def _seed_besoins(
    db: Session,
    users_by_email: dict[str, User],
    fiches_by_title: dict[str, FicheDePoste],
    projects_by_title: dict[str, ProjetRecrutement],
) -> tuple[dict[str, BesoinRecrutement], SeedCounters]:
    counters = SeedCounters()
    besoins_by_key: dict[str, BesoinRecrutement] = {}
    _ = projects_by_title

    print("\nSeeding besoins recrutement...")
    for data in SEED_BESOINS:
        key = str(data["key"])
        fiche = fiches_by_title[str(data["fiche_title"])]
        justification = str(data["justification"])
        existing = db.scalars(
            select(BesoinRecrutement).where(
                BesoinRecrutement.fiche_de_poste_id == fiche.id,
                BesoinRecrutement.justification == justification,
            )
        ).first()
        if existing:
            print(f"  [skip]    besoin '{key}' already exists")
            besoins_by_key[key] = existing
            counters = counters.add_skipped()
            continue

        besoin = BesoinRecrutement(
            lieu_affectation=str(data["lieu_affectation"]),
            positions_count=cast(int, data["positions_count"]),
            desired_date=data["desired_date"],
            justification=justification,
            status=data["status"],
            fiche_de_poste_id=fiche.id,
            submitted_by_id=(
                users_by_email[str(data["submitted_by_email"])].id
                if data["submitted_by_email"] is not None
                else None
            ),
            processed_by_id=(
                users_by_email[str(data["processed_by_email"])].id
                if data["processed_by_email"] is not None
                else None
            ),
            created_by_id=users_by_email[str(data["owner_email"])].id,
            updated_by_id=users_by_email[str(data["owner_email"])].id,
        )
        db.add(besoin)
        db.flush()
        besoins_by_key[key] = besoin
        print(f"  [created] besoin '{key}'")
        counters = counters.add_created()

    return besoins_by_key, counters


def seed() -> None:
    db = SessionLocal()
    try:
        users_by_email, users_counts = _seed_users(db)

        for data in SEED_USERS:
            email = str(data["email"])
            if email not in users_by_email:
                users_by_email[email] = _get_user_by_email(db, email)

        directions_by_code, directions_counts = _seed_directions(db, users_by_email)
        fiches_by_title, fiches_counts = _seed_fiches(
            db,
            users_by_email,
            directions_by_code,
        )
        projects_by_title, projects_counts = _seed_projects(
            db,
            users_by_email,
            fiches_by_title,
        )
        besoins_by_title, besoins_counts = _seed_besoins(
            db,
            users_by_email,
            fiches_by_title,
            projects_by_title,
        )

        db.commit()

        total_created = (
            users_counts.created
            + directions_counts.created
            + fiches_counts.created
            + projects_counts.created
            + besoins_counts.created
        )
        total_skipped = (
            users_counts.skipped
            + directions_counts.skipped
            + fiches_counts.skipped
            + projects_counts.skipped
            + besoins_counts.skipped
        )
        print(f"\nDone. {total_created} created, {total_skipped} skipped.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
