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
    BesoinRecrutementNotApprovedException,
    BesoinRecrutementNotFoundException,
    ProjetRecrutementInvalidTransitionException,
    ProjetRecrutementLinkMismatchException,
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
        selectinload(ProjetRecrutement.besoins).selectinload(BesoinRecrutement.fiche_de_poste),
        selectinload(ProjetRecrutement.besoin_recrutement),
        selectinload(ProjetRecrutement.fiche_de_poste).selectinload(FicheDePoste.direction).selectinload(Direction.director),
        selectinload(ProjetRecrutement.manager),
    )


def _resolve_project_links(
    db: Session,
    besoin_id: int | None,
    fiche_id: int | None,
) -> tuple[BesoinRecrutement | None, int | None]:
    besoin: BesoinRecrutement | None = None
    resolved_fiche_id = fiche_id

    if besoin_id is not None:
        besoin = get_besoin(db, besoin_id)
        if besoin.status != BesoinStatus.APPROVED:
            raise BesoinRecrutementNotApprovedException()

        if fiche_id is not None and fiche_id != besoin.fiche_de_poste_id:
            raise ProjetRecrutementLinkMismatchException()

        resolved_fiche_id = besoin.fiche_de_poste_id

    if resolved_fiche_id is not None:
        get_fiche_de_poste(db, resolved_fiche_id)

    return besoin, resolved_fiche_id


def create_besoin(
    db: Session,
    payload: BesoinRecrutementCreate,
    current_user: User,
) -> BesoinRecrutement:
    fiche = get_fiche_de_poste(db, payload.fiche_de_poste_id)
    direction = fiche.direction

    if (
        current_user.role == UserRole.DIRECTEUR 
        and direction and direction.director_id != current_user.id
        ):
        raise ForbiddenException()

    besoin = BesoinRecrutement(
        title=payload.title or f"Besoin - {fiche.title}",
        description=payload.location,
        positions_count=payload.positions_count,
        desired_date=payload.desired_date,
        justification=payload.recruitment_reason,
        priority=payload.priority,
        fiche_de_poste_id=payload.fiche_de_poste_id,
        projet_id=payload.projet_id,
        status=BesoinStatus.DRAFT,
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
    besoin, resolved_fiche_id = _resolve_project_links(
        db,
        payload.besoin_recrutement_id,
        payload.fiche_de_poste_id,
    )

    project = ProjetRecrutement(
        title=payload.title,
        description=payload.description,
        start_date=payload.start_date,
        expected_end_date=payload.expected_end_date,
        status=payload.status,
        manager_id=payload.manager_id,
        besoin_recrutement_id=payload.besoin_recrutement_id,
        fiche_de_poste_id=resolved_fiche_id,
        nombre_postes=payload.nombre_postes,
        created_by_id=current_user.id,
        updated_by_id=current_user.id,
    )
    db.add(project)
    db.flush()

    if besoin is not None:
        besoin.projet_id = project.id
        besoin.updated_by_id = current_user.id
        if project.nombre_postes is None:
            project.nombre_postes = besoin.positions_count
        db.add(besoin)
        db.add(project)
        db.flush()

    db.refresh(project)
    return get_project(db, project.id)


def list_projects(
    db: Session,
    params: PaginationParams,
    direction_id: int | None = None,
) -> tuple[list[ProjetRecrutement], int]:
    base_query = _project_query().where(
        ProjetRecrutement.is_deleted.is_(False),
        ProjetRecrutement.status == ProjetStatus.ACTIVE,
    )
    count_query = select(func.count()).select_from(ProjetRecrutement).where(
        ProjetRecrutement.is_deleted.is_(False),
        ProjetRecrutement.status == ProjetStatus.ACTIVE,
    )

    if direction_id is not None:
        base_query = base_query.where(ProjetRecrutement.fiche_de_poste_id.is_not(None))
        items = [
            project for project in db.scalars(
                base_query.order_by(ProjetRecrutement.id)
                ).all()
            if (project.fiche_de_poste 
                and project.fiche_de_poste.direction_id == direction_id)
        ]
        total_items = len(items)
        paged_items = items[params.offset : params.offset + params.page_size]
        return paged_items, total_items

    items = list(
        db.scalars(base_query.order_by(ProjetRecrutement.id).offset(params.offset).limit(params.page_size)).all()
    )
    total_items = int(db.scalar(count_query) or 0)
    return items, total_items


def get_project(db: Session, projet_id: int) -> ProjetRecrutement:
    project = db.scalars(
        _project_query()
        .where(
            ProjetRecrutement.id == projet_id,
            ProjetRecrutement.is_deleted.is_(False),
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
    project = get_project(db, projet_id)
    payload_data = payload.model_dump(exclude_unset=True)

    besoin_id = payload_data.get("besoin_recrutement_id", project.besoin_recrutement_id)
    fiche_id = payload_data.get("fiche_de_poste_id", project.fiche_de_poste_id)
    besoin, resolved_fiche_id = _resolve_project_links(db, besoin_id, fiche_id)

    for field_name in ("title",
                       "description",
                       "start_date",
                       "expected_end_date",
                       "status", "manager_id",
                       "nombre_postes",
                       "email_subject"):
        if field_name in payload_data:
            setattr(project, field_name, payload_data[field_name])

    project.besoin_recrutement_id = besoin_id
    project.fiche_de_poste_id = resolved_fiche_id
    if ("nombre_postes" not in payload_data 
        and besoin is not None and project.nombre_postes is None):
        project.nombre_postes = besoin.positions_count

    if besoin is not None:
        if besoin.projet_id is not None and besoin.projet_id != project.id:
            raise BesoinRecrutementAlreadyAttachedException()
        besoin.projet_id = project.id
        besoin.updated_by_id = current_user.id
        db.add(besoin)

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
    project = get_project(db, projet_id)
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
    project = get_project(db, projet_id)
    if project.status == ProjetStatus.CLOSED:
        raise ProjetRecrutementInvalidTransitionException()

    project.status = ProjetStatus.CLOSED
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
                item for item in scoped_items if item.status in {BesoinStatus.APPROVED,
                                                                 BesoinStatus.REJECTED}
            ]
        else:
            scoped_items = [
                item for item in scoped_items if item.status in {BesoinStatus.DRAFT,
                                                                 BesoinStatus.SUBMITTED}
            ]
        total_items = len(scoped_items)
        paged_items = scoped_items[params.offset : params.offset + params.page_size]
        return paged_items, total_items

    if current_user.role in {UserRole.DRH, UserRole.ADMIN}:
        if archived:
            base_query = base_query.where(
                BesoinRecrutement.status.in_([BesoinStatus.APPROVED,
                                              BesoinStatus.REJECTED]))
        else:
            base_query = base_query.where(
                BesoinRecrutement.status.in_([BesoinStatus.DRAFT,
                                              BesoinStatus.SUBMITTED]))
    else:
        if archived:
            base_query = base_query.where(
                BesoinRecrutement.status.in_([BesoinStatus.APPROVED,
                                              BesoinStatus.REJECTED]))

    if priority is not None:
        base_query = base_query.where(BesoinRecrutement.priority == priority)

    all_items = list(db.scalars(base_query).all())
    if direction_id is not None:
        all_items = [
            item for item in all_items if item.fiche_de_poste 
            and item.fiche_de_poste.direction_id == direction_id
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

    if (not elevated_editor 
        and not directeur_owner 
        and besoin.created_by_id != current_user.id):
        raise ForbiddenException()

    if besoin.status not in {BesoinStatus.DRAFT, BesoinStatus.SUBMITTED}:
        raise BesoinRecrutementInvalidTransitionException()

    payload_data = payload.model_dump(exclude_unset=True)
    if (
        "fiche_de_poste_id" in payload_data
        and payload_data["fiche_de_poste_id"] is not None
    ):
        next_fiche = get_fiche_de_poste(db, payload_data["fiche_de_poste_id"])
        if (current_user.role == UserRole.DIRECTEUR 
            and next_fiche.direction.director_id != current_user.id):
            raise ForbiddenException()

    if "location" in payload_data:
        payload_data["description"] = payload_data.pop("location")
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

    if (not elevated_editor 
        and not directeur_owner 
        and besoin.created_by_id != current_user.id):
        raise ForbiddenException()
    if besoin.status not in {BesoinStatus.DRAFT, BesoinStatus.SUBMITTED}:
        raise BesoinRecrutementInvalidTransitionException()

    besoin.is_deleted = True
    besoin.deleted_at = datetime.now(timezone.utc)
    besoin.updated_by_id = current_user.id
    db.add(besoin)
    db.flush()
    return besoin


def submit_besoin(db: Session, besoin_id: int, current_user: User) -> BesoinRecrutement:
    besoin = get_besoin(db, besoin_id)
    if besoin.status != BesoinStatus.DRAFT:
        raise BesoinRecrutementInvalidTransitionException()

    fiche = besoin.fiche_de_poste
    direction = fiche.direction if fiche else None
    if (current_user.role == UserRole.DIRECTEUR 
        and (direction is None or direction.director_id != current_user.id)):
        raise ForbiddenException()

    besoin.status = BesoinStatus.SUBMITTED
    besoin.submitted_by_id = current_user.id
    besoin.updated_by_id = current_user.id
    db.add(besoin)
    db.flush()
    db.refresh(besoin)
    return besoin


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

    if besoin.projet_id is None:
        fiche = besoin.fiche_de_poste
        today = datetime.now(timezone.utc).date()
        expected_end = besoin.desired_date or today
        subject = f"Ref. {besoin.id:04d} - {fiche.title if fiche else besoin.title}"
        project = ProjetRecrutement(
            title=f"Recrutement - {fiche.title if fiche else besoin.title}",
            description=besoin.justification,
            start_date=today,
            expected_end_date=expected_end,
            status=ProjetStatus.ACTIVE,
            manager_id=current_user.id,
            besoin_recrutement_id=besoin.id,
            fiche_de_poste_id=besoin.fiche_de_poste_id,
            nombre_postes=besoin.positions_count,
            email_subject=subject,
            created_by_id=current_user.id,
            updated_by_id=current_user.id,
        )
        db.add(project)
        db.flush()
        besoin.projet_id = project.id

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
    besoin.rejection_reason = payload.reason
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
    project = get_project(db, projet_id)
    besoin = get_besoin(db, besoin_id)

    if besoin.status != BesoinStatus.APPROVED:
        raise BesoinRecrutementNotApprovedException()
    if besoin.projet_id is not None and besoin.projet_id != projet_id:
        raise BesoinRecrutementAlreadyAttachedException()

    besoin.projet_id = project.id
    besoin.updated_by_id = current_user.id
    project.besoin_recrutement_id = besoin.id
    project.fiche_de_poste_id = besoin.fiche_de_poste_id
    if project.nombre_postes is None:
        project.nombre_postes = besoin.positions_count
    project.updated_by_id = current_user.id
    db.add(besoin)
    db.add(project)
    db.flush()
    return get_project(db, project.id)