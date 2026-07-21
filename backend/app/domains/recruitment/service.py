"""Service — recruitment domain."""

from datetime import datetime, timezone

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, selectinload

from app.core.enums import UserRole
from app.core.exceptions import ForbiddenException
from app.core.schemas import PaginationParams
from app.domains.directions.model import Direction
from app.domains.fiches_de_poste.model import FicheDePoste
from app.domains.fiches_de_poste.service import get_fiche as get_fiche_de_poste
from app.domains.recruitment.enums import BesoinPriority, BesoinStatus, ProjetStatus
from app.domains.recruitment.exceptions import (
    BesoinRecrutementAlreadyAttachedException,
    BesoinRecrutementInvalidTransitionException,
    BesoinRecrutementNotFoundException,
    ProjetRecrutementInvalidTransitionException,
    ProjetRecrutementNotFoundException,
)
from app.domains.recruitment.model import BesoinRecrutement, ProjetRecrutement
from app.domains.recruitment.schemas import (
    BesoinRecrutementCreate,
    BesoinRecrutementUpdate,
    ProjetRecrutementCreate,
    ProjetRecrutementUpdate,
    RejectBesoinRequest,
)
from app.domains.users.model import User


def _project_query() -> Select[tuple[ProjetRecrutement]]:
    return select(ProjetRecrutement).options(
        selectinload(ProjetRecrutement.besoin_recrutement)
        .selectinload(BesoinRecrutement.fiche_de_poste)
        .selectinload(FicheDePoste.direction)
        .selectinload(Direction.director),
        selectinload(ProjetRecrutement.manager),
    )


def _ensure_besoin_attachable(
    db: Session,
    besoin: BesoinRecrutement,
    current_project_id: int | None = None,
) -> None:
    if besoin.status != BesoinStatus.APPROVED:
        raise BesoinRecrutementInvalidTransitionException()

    existing_project = db.scalars(
        select(ProjetRecrutement).where(
            ProjetRecrutement.besoin_recrutement_id == besoin.id,
            ProjetRecrutement.is_deleted.is_(False),
        )
    ).first()
    if existing_project is not None and existing_project.id != current_project_id:
        raise BesoinRecrutementAlreadyAttachedException()


def _is_project_visible_to_user(project: ProjetRecrutement, current_user: User) -> bool:
    if current_user.role != UserRole.DIRECTEUR:
        return True
    besoin = project.besoin_recrutement
    fiche = besoin.fiche_de_poste if besoin else None
    direction = fiche.direction if fiche else None
    return direction is not None and direction.director_id == current_user.id


def create_besoin(
    db: Session,
    payload: BesoinRecrutementCreate,
    current_user: User,
) -> BesoinRecrutement:
    fiche = get_fiche_de_poste(db, payload.fiche_de_poste_id)
    direction = fiche.direction

    if (
        current_user.role == UserRole.DIRECTEUR
        and direction
        and direction.director_id != current_user.id
    ):
        raise ForbiddenException()

    besoin = BesoinRecrutement(
        lieu_affectation=payload.lieu_affectation,
        positions_count=payload.positions_count,
        desired_date=payload.desired_date,
        justification=payload.recruitment_reason,
        priority=payload.priority,
        fiche_de_poste_id=payload.fiche_de_poste_id,
        status=BesoinStatus.SUBMITTED,
        submitted_by_id=current_user.id,
        created_by_id=current_user.id,
        updated_by_id=current_user.id,
    )
    db.add(besoin)
    db.flush()
    db.refresh(besoin)
    return besoin


def create_project(
    db: Session,
    payload: ProjetRecrutementCreate,
    current_user: User,
) -> ProjetRecrutement:
    besoin = get_besoin(db, payload.besoin_recrutement_id)
    _ensure_besoin_attachable(db, besoin)

    project = ProjetRecrutement(
        status=ProjetStatus.ACTIVE,
        manager_id=payload.manager_id or current_user.id,
        besoin_recrutement_id=payload.besoin_recrutement_id,
        email_subject=payload.email_subject,
        offre=payload.offre,
        created_by_id=current_user.id,
        updated_by_id=current_user.id,
    )
    db.add(project)
    db.flush()

    db.refresh(project)
    return get_project(db, project.id)


def list_projects(
    db: Session,
    params: PaginationParams,
    current_user: User,
    direction_id: int | None = None,
    archived: bool = False,
) -> tuple[list[ProjetRecrutement], int]:
    target_status = ProjetStatus.CLOSED if archived else ProjetStatus.ACTIVE
    base_query = _project_query().where(
        ProjetRecrutement.is_deleted.is_(False),
        ProjetRecrutement.status == target_status,
    )

    items = list(db.scalars(base_query.order_by(ProjetRecrutement.id.desc())).all())
    items = [item for item in items if _is_project_visible_to_user(item, current_user)]

    if direction_id is not None:
        items = [
            item
            for item in items
            if item.besoin_recrutement
            and item.besoin_recrutement.fiche_de_poste
            and item.besoin_recrutement.fiche_de_poste.direction_id == direction_id
        ]

    total_items = len(items)
    items = items[params.offset : params.offset + params.page_size]
    return items, total_items


def get_project(
    db: Session,
    projet_id: int,
    current_user: User | None = None,
) -> ProjetRecrutement:
    project = db.scalars(
        _project_query().where(
            ProjetRecrutement.id == projet_id,
            ProjetRecrutement.is_deleted.is_(False),
        )
    ).first()
    if project is None:
        raise ProjetRecrutementNotFoundException()
    if current_user is not None and not _is_project_visible_to_user(
        project, current_user
    ):
        raise ForbiddenException()
    return project


def get_project_by_email_subject(
    db: Session,
    subject: str,
) -> ProjetRecrutement:
    normalized = subject.strip().lower()
    project = db.scalars(
        _project_query().where(
            ProjetRecrutement.is_deleted.is_(False),
            func.lower(ProjetRecrutement.email_subject) == normalized,
        )
    ).first()
    if project is None:
        raise ProjetRecrutementNotFoundException()
    return project


def update_project(
    db: Session,
    projet_id: int,
    payload: ProjetRecrutementUpdate,
    current_user: User,
) -> ProjetRecrutement:
    project = get_project(db, projet_id, current_user)
    if project.status == ProjetStatus.CLOSED:
        raise ProjetRecrutementInvalidTransitionException()

    payload_data = payload.model_dump(exclude_unset=True)

    for field_name in ("status", "manager_id", "email_subject", "offre"):
        if field_name in payload_data:
            setattr(project, field_name, payload_data[field_name])

    if (
        payload_data.get("status") == ProjetStatus.CLOSED
        and project.archived_at is None
    ):
        project.archived_at = datetime.now(timezone.utc)

    project.updated_by_id = current_user.id
    db.add(project)
    db.flush()
    db.refresh(project)
    return get_project(db, project.id)


def delete_project(
    db: Session,
    projet_id: int,
    current_user: User,
) -> ProjetRecrutement:
    project = get_project(db, projet_id, current_user)
    project.is_deleted = True
    project.deleted_at = datetime.now(timezone.utc)
    project.updated_by_id = current_user.id
    db.add(project)
    db.flush()
    return project


def close_project(
    db: Session,
    projet_id: int,
    current_user: User,
) -> ProjetRecrutement:
    project = get_project(db, projet_id, current_user)
    if project.status == ProjetStatus.CLOSED:
        raise ProjetRecrutementInvalidTransitionException()

    project.status = ProjetStatus.CLOSED
    project.archived_at = datetime.now(timezone.utc)
    project.updated_by_id = current_user.id
    db.add(project)
    db.flush()
    db.refresh(project)
    return get_project(db, project.id)


def get_besoin(db: Session, besoin_id: int) -> BesoinRecrutement:
    besoin = db.scalars(
        select(BesoinRecrutement)
        .options(
            selectinload(BesoinRecrutement.fiche_de_poste)
            .selectinload(FicheDePoste.direction)
            .selectinload(Direction.director),
            selectinload(BesoinRecrutement.submitted_by),
        )
        .where(
            BesoinRecrutement.id == besoin_id,
            BesoinRecrutement.is_deleted.is_(False),
        )
    ).first()
    if besoin is None:
        raise BesoinRecrutementNotFoundException()
    return besoin


def list_besoins(
    db: Session,
    params: PaginationParams,
    current_user: User,
    direction_id: int | None = None,
    priority: BesoinPriority | None = None,
    archived: bool = False,
) -> tuple[list[BesoinRecrutement], int]:
    base_query = (
        select(BesoinRecrutement)
        .options(
            selectinload(BesoinRecrutement.fiche_de_poste)
            .selectinload(FicheDePoste.direction)
            .selectinload(Direction.director),
            selectinload(BesoinRecrutement.submitted_by),
        )
        .where(BesoinRecrutement.is_deleted.is_(False))
        .order_by(BesoinRecrutement.id.desc())
    )

    if current_user.role == UserRole.DIRECTEUR:
        scoped_items = list(db.scalars(base_query).all())
        scoped_items = [
            item
            for item in scoped_items
            if (
                item.fiche_de_poste
                and item.fiche_de_poste.direction
                and item.fiche_de_poste.direction.director_id == current_user.id
            )
        ]
        if direction_id is not None:
            scoped_items = [
                item
                for item in scoped_items
                if item.fiche_de_poste
                and item.fiche_de_poste.direction_id == direction_id
            ]
        if priority is not None:
            scoped_items = [item for item in scoped_items if item.priority == priority]
        if archived:
            scoped_items = [
                item
                for item in scoped_items
                if item.status in {BesoinStatus.APPROVED, BesoinStatus.REJECTED}
            ]
        else:
            scoped_items = [
                item for item in scoped_items if item.status == BesoinStatus.SUBMITTED
            ]
        total_items = len(scoped_items)
        paged_items = scoped_items[params.offset : params.offset + params.page_size]
        return paged_items, total_items

    if current_user.role in {UserRole.DRH, UserRole.ADMIN}:
        if archived:
            base_query = base_query.where(
                BesoinRecrutement.status.in_(
                    [BesoinStatus.APPROVED, BesoinStatus.REJECTED]
                )
            )
        else:
            base_query = base_query.where(
                BesoinRecrutement.status == BesoinStatus.SUBMITTED
            )
    else:
        if archived:
            base_query = base_query.where(
                BesoinRecrutement.status.in_(
                    [BesoinStatus.APPROVED, BesoinStatus.REJECTED]
                )
            )

    if priority is not None:
        base_query = base_query.where(BesoinRecrutement.priority == priority)

    all_items = list(db.scalars(base_query).all())
    if direction_id is not None:
        all_items = [
            item
            for item in all_items
            if item.fiche_de_poste and item.fiche_de_poste.direction_id == direction_id
        ]

    total_items = len(all_items)
    items = all_items[params.offset : params.offset + params.page_size]
    return items, total_items


def update_besoin(
    db: Session,
    besoin_id: int,
    payload: BesoinRecrutementUpdate,
    current_user: User,
) -> BesoinRecrutement:
    besoin = get_besoin(db, besoin_id)

    fiche = besoin.fiche_de_poste
    direction = fiche.direction if fiche else None
    elevated_editor = current_user.role in {UserRole.ADMIN, UserRole.DRH}
    directeur_owner = (
        current_user.role == UserRole.DIRECTEUR
        and direction is not None
        and direction.director_id == current_user.id
    )

    if (
        not elevated_editor
        and not directeur_owner
        and besoin.created_by_id != current_user.id
    ):
        raise ForbiddenException()

    if besoin.status != BesoinStatus.SUBMITTED:
        raise BesoinRecrutementInvalidTransitionException()

    payload_data = payload.model_dump(exclude_unset=True)
    if (
        "fiche_de_poste_id" in payload_data
        and payload_data["fiche_de_poste_id"] is not None
    ):
        next_fiche = get_fiche_de_poste(db, payload_data["fiche_de_poste_id"])
        if (
            current_user.role == UserRole.DIRECTEUR
            and next_fiche.direction.director_id != current_user.id
        ):
            raise ForbiddenException()

    if "lieu_affectation" in payload_data and payload_data["lieu_affectation"] is None:
        payload_data.pop("lieu_affectation")
    if "recruitment_reason" in payload_data:
        payload_data["justification"] = payload_data.pop("recruitment_reason")

    for field_name, field_value in payload_data.items():
        setattr(besoin, field_name, field_value)

    besoin.updated_by_id = current_user.id
    db.add(besoin)
    db.flush()
    db.refresh(besoin)
    return besoin


def delete_besoin(
    db: Session,
    besoin_id: int,
    current_user: User,
) -> BesoinRecrutement:
    besoin = get_besoin(db, besoin_id)

    fiche = besoin.fiche_de_poste
    direction = fiche.direction if fiche else None
    elevated_editor = current_user.role in {UserRole.ADMIN, UserRole.DRH}
    directeur_owner = (
        current_user.role == UserRole.DIRECTEUR
        and direction is not None
        and direction.director_id == current_user.id
    )

    if (
        not elevated_editor
        and not directeur_owner
        and besoin.created_by_id != current_user.id
    ):
        raise ForbiddenException()
    if besoin.status != BesoinStatus.SUBMITTED:
        raise BesoinRecrutementInvalidTransitionException()

    besoin.is_deleted = True
    besoin.deleted_at = datetime.now(timezone.utc)
    besoin.updated_by_id = current_user.id
    db.add(besoin)
    db.flush()
    return besoin


def submit_besoin(db: Session, besoin_id: int, current_user: User) -> BesoinRecrutement:
    _ = current_user
    _ = get_besoin(db, besoin_id)
    raise BesoinRecrutementInvalidTransitionException()


def approve_besoin(
    db: Session,
    besoin_id: int,
    current_user: User,
) -> BesoinRecrutement:
    besoin = get_besoin(db, besoin_id)
    if besoin.status != BesoinStatus.SUBMITTED:
        raise BesoinRecrutementInvalidTransitionException()

    besoin.status = BesoinStatus.APPROVED
    besoin.processed_by_id = current_user.id
    besoin.updated_by_id = current_user.id

    existing_project = db.scalars(
        select(ProjetRecrutement).where(
            ProjetRecrutement.besoin_recrutement_id == besoin.id,
            ProjetRecrutement.is_deleted.is_(False),
        )
    ).first()

    if existing_project is None:
        fiche = besoin.fiche_de_poste
        fiche_title = fiche.title if fiche else "Poste"
        subject = f"Candidature - {fiche_title} - Ref. {besoin.id:04d}"
        project = ProjetRecrutement(
            status=ProjetStatus.ACTIVE,
            manager_id=current_user.id,
            besoin_recrutement_id=besoin.id,
            email_subject=subject,
            offre=None,
            created_by_id=current_user.id,
            updated_by_id=current_user.id,
        )
        db.add(project)
        db.flush()

    db.add(besoin)
    db.flush()
    db.refresh(besoin)
    return besoin


def reject_besoin(
    db: Session,
    besoin_id: int,
    payload: RejectBesoinRequest,
    current_user: User,
) -> BesoinRecrutement:
    besoin = get_besoin(db, besoin_id)
    if besoin.status != BesoinStatus.SUBMITTED:
        raise BesoinRecrutementInvalidTransitionException()

    besoin.status = BesoinStatus.REJECTED
    besoin.processed_by_id = current_user.id
    besoin.updated_by_id = current_user.id
    db.add(besoin)
    db.flush()
    db.refresh(besoin)
    return besoin


def attach_besoin(
    db: Session,
    projet_id: int,
    besoin_id: int,
    current_user: User,
) -> ProjetRecrutement:
    project = get_project(db, projet_id, current_user)
    if project.status == ProjetStatus.CLOSED:
        raise ProjetRecrutementInvalidTransitionException()

    besoin = get_besoin(db, besoin_id)
    _ensure_besoin_attachable(db, besoin, current_project_id=project.id)

    project.besoin_recrutement_id = besoin.id
    project.archived_at = None
    project.updated_by_id = current_user.id
    db.add(project)
    db.flush()
    return get_project(db, project.id)
