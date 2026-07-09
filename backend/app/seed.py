"""Database seeder with complete demo data.

Seeds:
- users
- directions
- fiches de poste
- projets recrutement
- besoins recrutement
- offres

Run AFTER migrations have been applied:
    python -m alembic upgrade head
    python -m app.seed

Idempotent: existing rows (matched on stable business keys) are not duplicated.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import cast

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.enums import UserRole
from app.core.security import hash_password
from app.database import SessionLocal
from app.domains.directions.model import Direction
from app.domains.fiches_de_poste.enums import FicheStatus
from app.domains.fiches_de_poste.model import FicheDePoste
from app.domains.offres.enums import OffreStatus
from app.domains.offres.model import Offre
from app.domains.recruitment.enums import BesoinStatus, ProjetStatus
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
    # One dedicated DIRECTEUR per direction below.
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
        "description": "Pilote les projets de transformation RH.",
        "missions": "Coordonner les parties prenantes, suivre planning,"
        " assurer livraison.",
        "required_skills": "Gestion de projet, communication, leadership.",
        "experience_level": "5+ years",
        "formation_domain": "Ressources Humaines / Gestion",
        "education_level": "Bac+5",
        "technical_skills": "MS Project, Jira, reporting RH, SIRH.",
        "managerial_skills": "Leadership, animation d'equipe, conduite du changement.",
        "status": FicheStatus.VALIDATED,
        "direction_code": "HR",
    },
    {
        "title": "Ingenieur DevOps",
        "description": "Automatise le deploiement et la fiabilite des plateformes.",
        "missions": "Mettre en place CI/CD, observabilite, securite operationnelle.",
        "required_skills": "Docker, Kubernetes, CI/CD, Linux, scripting.",
        "experience_level": "3+ years",
        "formation_domain": "Informatique / Systemes",
        "education_level": "Bac+5",
        "technical_skills": "Docker, Kubernetes, Terraform, GitOps, monitoring.",
        "managerial_skills": "Coordination technique, mentorat junior.",
        "status": FicheStatus.VALIDATED,
        "direction_code": "IT",
    },
    {
        "title": "Charge de Recrutement",
        "description": "Conduit les campagnes de recrutement.",
        "missions": "Sourcing, entretiens, coordination avec managers.",
        "required_skills": "Entretien, evaluation, communication.",
        "experience_level": "2+ years",
        "formation_domain": "Ressources Humaines",
        "education_level": "Bac+3",
        "technical_skills": "ATS, LinkedIn Recruiter, sourcing boolean.",
        "managerial_skills": "Organisation, gestion des priorites.",
        "status": FicheStatus.DRAFT,
        "direction_code": "HR",
    },
    {
        "title": "Responsable Production",
        "description": "Supervise les lignes de production et la qualite.",
        "missions": "Planifier la production, garantir la qualite,"
        " piloter les equipes terrain.",
        "required_skills": "Lean management, gestion de production, QHSE.",
        "experience_level": "4+ years",
        "formation_domain": "Genie Industriel",
        "education_level": "Bac+5",
        "technical_skills": "Lean Six Sigma, ERP production, QHSE.",
        "managerial_skills": "Gestion d'equipe terrain, resolution de conflits.",
        "status": FicheStatus.VALIDATED,
        "direction_code": "OPS",
    },
]

SEED_PROJECTS: list[dict[str, object]] = [
    {
        "title": "Programme Recrutement 2026",
        "description": "Plan global de renforcement des equipes.",
        "start_date": date(2026, 1, 10),
        "expected_end_date": date(2026, 12, 20),
        "status": ProjetStatus.ACTIVE,
        "manager_email": "drh@example.com",
        "fiche_title": "Ingenieur DevOps",
        "nombre_postes": 5,
    },
    {
        "title": "Expansion Equipe IT",
        "description": "Renforcement des capacites engineering.",
        "start_date": date(2026, 3, 1),
        "expected_end_date": date(2026, 10, 1),
        "status": ProjetStatus.DRAFT,
        "manager_email": "drh@example.com",
        "fiche_title": "Ingenieur DevOps",
        "nombre_postes": 3,
    },
    {
        "title": "Renforcement RH 2026",
        "description": "Structuration de l'equipe recrutement interne.",
        "start_date": date(2026, 2, 1),
        "expected_end_date": date(2026, 11, 30),
        "status": ProjetStatus.ACTIVE,
        "manager_email": "drh@example.com",
        "fiche_title": "Charge de Recrutement",
        "nombre_postes": 2,
    },
]

SEED_BESOINS: list[dict[str, object]] = [
    {
        "title": "Recruter 2 DevOps Seniors",
        "description": "Soutenir la migration cloud.",
        "positions_count": 2,
        "desired_date": date(2026, 8, 1),
        "justification": "Montee en charge des plateformes critiques.",
        "status": BesoinStatus.APPROVED,
        "rejection_reason": None,
        "fiche_title": "Ingenieur DevOps",
        "submitted_by_email": "directeur.it@example.com",
        "processed_by_email": "drh@example.com",
        "project_title": "Programme Recrutement 2026",
        "owner_email": "directeur.it@example.com",
    },
    {
        "title": "Recruter 1 Charge de Recrutement",
        "description": "Accompagner la croissance des recrutements.",
        "positions_count": 1,
        "desired_date": date(2026, 7, 1),
        "justification": "Volume de postes ouverts en forte hausse.",
        "status": BesoinStatus.SUBMITTED,
        "rejection_reason": None,
        "fiche_title": "Charge de Recrutement",
        "submitted_by_email": "directeur.hr@example.com",
        "processed_by_email": None,
        "project_title": None,
        "owner_email": "directeur.hr@example.com",
    },
    {
        "title": "Recruter 1 Chef de Projet RH",
        "description": "Pilotage de plusieurs chantiers structurants.",
        "positions_count": 1,
        "desired_date": date(2026, 9, 1),
        "justification": "Besoin de coordination transverse.",
        "status": BesoinStatus.REJECTED,
        "rejection_reason": "Budget non valide pour ce trimestre.",
        "fiche_title": "Chef de Projet RH",
        "submitted_by_email": "directeur.hr@example.com",
        "processed_by_email": "drh@example.com",
        "project_title": None,
        "owner_email": "directeur.hr@example.com",
    },
    {
        "title": "Recruter 1 Responsable Production",
        "description": "Renforcer l'encadrement de la ligne de production B.",
        "positions_count": 1,
        "desired_date": date(2026, 8, 15),
        "justification": "Depart a la retraite du titulaire actuel.",
        "status": BesoinStatus.APPROVED,
        "rejection_reason": None,
        "fiche_title": "Responsable Production",
        "submitted_by_email": "directeur.ops@example.com",
        "processed_by_email": "drh@example.com",
        "project_title": None,
        "owner_email": "directeur.ops@example.com",
    },
]

SEED_OFFRES: list[dict[str, object]] = [
    {
        "title": "Offre Ingenieur DevOps Senior",
        "description": "Rejoignez l'equipe plateforme pour accelerer notre cloud.",
        "requirements": "Kubernetes, Terraform, GitOps, monitoring.",
        "deadline": date(2026, 9, 15),
        "status": OffreStatus.PUBLISHED,
        "published_at": datetime(2026, 6, 15, 10, 0, tzinfo=timezone.utc),
        "besoin_title": "Recruter 2 DevOps Seniors",
        "published_by_email": "drh@example.com",
        "owner_email": "drh@example.com",
    },
    {
        "title": "Offre Charge de Recrutement",
        "description": "Rejoignez l'equipe RH pour accelerer le staffing.",
        "requirements": "Sourcing, conduite d'entretien, ATS.",
        "deadline": date(2026, 10, 1),
        "status": OffreStatus.DRAFT,
        "published_at": None,
        "besoin_title": "Recruter 1 Charge de Recrutement",
        "published_by_email": None,
        "owner_email": "drh@example.com",
    },
    {
        "title": "Offre Responsable Production",
        "description": "Encadrez une ligne de production a fort enjeu qualite.",
        "requirements": "Lean Six Sigma, gestion d'equipe, QHSE.",
        "deadline": date(2026, 9, 30),
        "status": OffreStatus.PUBLISHED,
        "published_at": datetime(2026, 7, 1, 9, 0, tzinfo=timezone.utc),
        "besoin_title": "Recruter 1 Responsable Production",
        "published_by_email": "drh@example.com",
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

        status = data["status"]
        direction = directions_by_code[str(data["direction_code"])]
        # Each fiche is authored by the directeur of its own direction.
        direction_directeur_id = direction.director_id

        fiche = FicheDePoste(
            title=title,
            description=str(data["description"]),
            missions=str(data["missions"]),
            required_skills=str(data["required_skills"]),
            experience_level=str(data["experience_level"]),
            formation_domain=str(data["formation_domain"]),
            education_level=str(data["education_level"]),
            technical_skills=str(data["technical_skills"]),
            managerial_skills=str(data["managerial_skills"]),
            status=status,
            direction_id=direction.id,
            validated_by_id=drh.id if status == FicheStatus.VALIDATED else None,
            created_by_id=direction_directeur_id,
            updated_by_id=(
                drh.id 
                if status == FicheStatus.VALIDATED 
                else direction_directeur_id
                ),
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
    counters = SeedCounters()
    projects_by_title: dict[str, ProjetRecrutement] = {}
    drh = users_by_email["drh@example.com"]

    print("\nSeeding projets recrutement...")
    for data in SEED_PROJECTS:
        title = str(data["title"])
        existing = db.scalars(
            select(ProjetRecrutement).where(ProjetRecrutement.title == title)
        ).first()
        if existing:
            print(f"  [skip]    projet '{title}' already exists")
            projects_by_title[title] = existing
            counters = counters.add_skipped()
            continue

        project = ProjetRecrutement(
            title=title,
            description=str(data["description"]),
            start_date=data["start_date"],
            expected_end_date=data["expected_end_date"],
            status=data["status"],
            manager_id=users_by_email[str(data["manager_email"])].id,
            fiche_de_poste_id=fiches_by_title[str(data["fiche_title"])].id,
            nombre_postes=cast(int, data["nombre_postes"]),
            created_by_id=drh.id,
            updated_by_id=drh.id,
        )
        db.add(project)
        db.flush()
        projects_by_title[title] = project
        print(f"  [created] projet '{title}'")
        counters = counters.add_created()

    return projects_by_title, counters


def _seed_besoins(
    db: Session,
    users_by_email: dict[str, User],
    fiches_by_title: dict[str, FicheDePoste],
    projects_by_title: dict[str, ProjetRecrutement],
) -> tuple[dict[str, BesoinRecrutement], SeedCounters]:
    counters = SeedCounters()
    besoins_by_title: dict[str, BesoinRecrutement] = {}

    print("\nSeeding besoins recrutement...")
    for data in SEED_BESOINS:
        title = str(data["title"])
        existing = db.scalars(
            select(BesoinRecrutement).where(BesoinRecrutement.title == title)
        ).first()
        if existing:
            print(f"  [skip]    besoin '{title}' already exists")
            besoins_by_title[title] = existing
            counters = counters.add_skipped()
            continue

        project_title = data["project_title"]
        project_id = (
            projects_by_title[str(project_title)].id
            if project_title is not None
            else None
        )

        besoin = BesoinRecrutement(
            title=title,
            description=str(data["description"]),
            positions_count=cast(int, data["positions_count"]),
            desired_date=data["desired_date"],
            justification=str(data["justification"]),
            status=data["status"],
            rejection_reason=data["rejection_reason"],
            fiche_de_poste_id=fiches_by_title[str(data["fiche_title"])].id,
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
            projet_id=project_id,
            created_by_id=users_by_email[str(data["owner_email"])].id,
            updated_by_id=users_by_email[str(data["owner_email"])].id,
        )
        db.add(besoin)
        db.flush()
        besoins_by_title[title] = besoin
        print(f"  [created] besoin '{title}'")
        counters = counters.add_created()

    return besoins_by_title, counters


def _seed_offres(
    db: Session,
    users_by_email: dict[str, User],
    besoins_by_title: dict[str, BesoinRecrutement],
) -> SeedCounters:
    counters = SeedCounters()

    print("\nSeeding offres...")
    for data in SEED_OFFRES:
        title = str(data["title"])
        existing = db.scalars(select(Offre).where(Offre.title == title)).first()
        if existing:
            print(f"  [skip]    offre '{title}' already exists")
            counters = counters.add_skipped()
            continue

        offer = Offre(
            title=title,
            description=str(data["description"]),
            requirements=str(data["requirements"]),
            deadline=data["deadline"],
            status=data["status"],
            published_at=data["published_at"],
            besoin_id=besoins_by_title[str(data["besoin_title"])].id,
            published_by_id=(
                users_by_email[str(data["published_by_email"])].id
                if data["published_by_email"] is not None
                else None
            ),
            created_by_id=users_by_email[str(data["owner_email"])].id,
            updated_by_id=users_by_email[str(data["owner_email"])].id,
        )
        db.add(offer)
        db.flush()
        print(f"  [created] offre '{title}'")
        counters = counters.add_created()

    return counters


def seed() -> None:
    db = SessionLocal()
    try:
        users_by_email, users_counts = _seed_users(db)

        # Ensure maps include any pre-existing users required by later entities.
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
        offres_counts = _seed_offres(db, users_by_email, besoins_by_title)

        db.commit()

        total_created = (
            users_counts.created
            + directions_counts.created
            + fiches_counts.created
            + projects_counts.created
            + besoins_counts.created
            + offres_counts.created
        )
        total_skipped = (
            users_counts.skipped
            + directions_counts.skipped
            + fiches_counts.skipped
            + projects_counts.skipped
            + besoins_counts.skipped
            + offres_counts.skipped
        )
        print(f"\nDone. {total_created} created, {total_skipped} skipped.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()