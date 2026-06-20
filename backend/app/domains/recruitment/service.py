"""Service — recruitment domain."""
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import ForbiddenException
from app.core.schemas import PaginationParams
from app.domains.fiches_de_poste.service import get_fiche as get_fiche_de_poste
from app.domains.recruitment.enums import BesoinStatus
from app.domains.recruitment.exceptions import (
    BesoinRecrutementAlreadyAttachedException,
    BesoinRecrutementInvalidTransitionException,
    BesoinRecrutementNotApprovedException,
    BesoinRecrutementNotFoundException,
    ProjetRecrutementNotFoundException,
)
from app.domains.recruitment.model import BesoinRecrutement, ProjetRecrutement
from app.domains.recruitment.schemas import (
    BesoinRecrutementCreate,
    BesoinRecrutementUpdate,
    ProjetRecrutementCreate,
    RejectBesoinRequest,
)
from app.domains.users.model import User


def create_besoin(
    db: Session,
    payload: BesoinRecrutementCreate,
    current_user: User,
) -> BesoinRecrutement:
    get_fiche_de_poste(db, payload.fiche_de_poste_id)

    besoin = BesoinRecrutement(
        title=payload.title,
        description=payload.description,
        positions_count=payload.positions_count,
        desired_date=payload.desired_date,
        justification=payload.justification,
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
    project = ProjetRecrutement(
        title=payload.title,
        description=payload.description,
        start_date=payload.start_date,
        expected_end_date=payload.expected_end_date,
        status=payload.status,
        manager_id=payload.manager_id,
        created_by_id=current_user.id,
        updated_by_id=current_user.id,
    )
    db.add(project)
    db.flush()
    db.refresh(project)
    return project


def get_project(db: Session, projet_id: int) -> ProjetRecrutement:
    project = db.scalars(
        select(ProjetRecrutement)
        .where(
            ProjetRecrutement.id == projet_id,
            ProjetRecrutement.is_deleted.is_(False),
        )
        .options(selectinload(ProjetRecrutement.besoins))
    ).first()
    if project is None:
        raise ProjetRecrutementNotFoundException()
    return project


def get_besoin(db: Session, besoin_id: int) -> BesoinRecrutement:
    besoin = db.scalars(
        select(BesoinRecrutement).where(
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
) -> tuple[list[BesoinRecrutement], int]:
    base_query = (
        select(BesoinRecrutement)
        .where(BesoinRecrutement.is_deleted.is_(False))
        .order_by(BesoinRecrutement.id)
    )
    items = list(
        db.scalars(base_query.offset(params.offset).limit(params.page_size)).all()
    )
    total_items = db.scalar(
        select(func.count())
        .select_from(BesoinRecrutement)
        .where(BesoinRecrutement.is_deleted.is_(False))
    )
    return items, int(total_items or 0)


def update_besoin(
    db: Session,
    besoin_id: int,
    payload: BesoinRecrutementUpdate,
    current_user: User,
) -> BesoinRecrutement:
    besoin = get_besoin(db, besoin_id)

    if besoin.created_by_id != current_user.id:
        raise ForbiddenException()
    if besoin.status != BesoinStatus.DRAFT:
        raise BesoinRecrutementInvalidTransitionException()

    payload_data = payload.model_dump(exclude_unset=True)
    if (
        "fiche_de_poste_id" in payload_data
        and payload_data["fiche_de_poste_id"] is not None
    ):
        get_fiche_de_poste(db, payload_data["fiche_de_poste_id"])

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

    if besoin.created_by_id != current_user.id:
        raise ForbiddenException()
    if besoin.status != BesoinStatus.DRAFT:
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
    db.add(besoin)
    db.flush()
    return get_project(db, project.id)
