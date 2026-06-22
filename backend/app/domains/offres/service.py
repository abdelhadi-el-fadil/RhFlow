"""Service — offres domain."""
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.schemas import PaginationParams
from app.domains.offres.enums import OffreStatus
from app.domains.offres.exceptions import (
    OffreBesoinNotPublishableException,
    OffreInvalidTransitionException,
    OffreNotFoundException,
)
from app.domains.offres.model import Offre
from app.domains.offres.schemas import OffreCreate
from app.domains.recruitment.enums import BesoinStatus
from app.domains.recruitment.model import BesoinRecrutement
from app.domains.users.model import User


def _get_publishable_besoin(db: Session, besoin_id: int) -> BesoinRecrutement:
    besoin = db.scalars(
        select(BesoinRecrutement).where(
            BesoinRecrutement.id == besoin_id,
            BesoinRecrutement.is_deleted.is_(False),
        )
    ).first()
    if besoin is None or besoin.status != BesoinStatus.APPROVED:
        raise OffreBesoinNotPublishableException()
    return besoin


def create_offre(db: Session, payload: OffreCreate, current_user: User) -> Offre:
    _get_publishable_besoin(db, payload.besoin_id)

    offre = Offre(
        title=payload.title,
        description=payload.description,
        requirements=payload.requirements,
        deadline=payload.deadline,
        status=OffreStatus.DRAFT,
        besoin_id=payload.besoin_id,
        created_by_id=current_user.id,
        updated_by_id=current_user.id,
    )
    db.add(offre)
    db.flush()
    db.refresh(offre)
    return offre


def get_offre(db: Session, offre_id: int) -> Offre:
    offre = db.scalars(
        select(Offre).where(
            Offre.id == offre_id,
            Offre.is_deleted.is_(False),
        )
    ).first()
    if offre is None:
        raise OffreNotFoundException()
    return offre


def list_public_offres(
    db: Session,
    params: PaginationParams,
) -> tuple[list[Offre], int]:
    base_query = (
        select(Offre)
        .where(
            Offre.status == OffreStatus.PUBLISHED,
            Offre.is_deleted.is_(False),
        )
        .order_by(Offre.id)
    )
    items = list(
        db.scalars(base_query.offset(params.offset).limit(params.page_size)).all()
    )
    total_items = db.scalar(
        select(func.count())
        .select_from(Offre)
        .where(
            Offre.status == OffreStatus.PUBLISHED,
            Offre.is_deleted.is_(False),
        )
    )
    return items, int(total_items or 0)


def publish_offre(db: Session, offre_id: int, current_user: User) -> Offre:
    offre = get_offre(db, offre_id)
    if offre.status != OffreStatus.DRAFT:
        raise OffreInvalidTransitionException()

    offre.status = OffreStatus.PUBLISHED
    offre.published_at = datetime.now(timezone.utc)
    offre.published_by_id = current_user.id
    offre.updated_by_id = current_user.id
    db.add(offre)
    db.flush()
    db.refresh(offre)
    return offre


def close_offre(db: Session, offre_id: int, current_user: User) -> Offre:
    offre = get_offre(db, offre_id)
    if offre.status != OffreStatus.PUBLISHED:
        raise OffreInvalidTransitionException()

    offre.status = OffreStatus.CLOSED
    offre.updated_by_id = current_user.id
    db.add(offre)
    db.flush()
    db.refresh(offre)
    return offre
