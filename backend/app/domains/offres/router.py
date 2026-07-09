"""Router — offres domain."""
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.dependencies import require_role
from app.core.enums import UserRole
from app.core.schemas import (
    ApiResponse,
    PaginatedResponse,
    PaginationMeta,
    PaginationParams,
)
from app.database import get_db
from app.domains.offres import service as offres_service
from app.domains.offres.schemas import OffreCreate, OffrePublicResponse, OffreResponse
from app.domains.users.model import User

router = APIRouter(prefix="/offres", tags=["Offres"])


@router.get("/", response_model=PaginatedResponse[OffrePublicResponse])
def list_offres(
    params: Annotated[PaginationParams, Depends()],
    db: Session = Depends(get_db),
) -> PaginatedResponse[OffrePublicResponse]:
    items, total = offres_service.list_public_offres(db, params)
    return PaginatedResponse(
        data=[OffrePublicResponse.model_validate(item) for item in items],
        meta=PaginationMeta(
            page=params.page,
            page_size=params.page_size,
            total_items=total,
            total_pages=(total + params.page_size - 1) // params.page_size,
        ),
    )


@router.post(
    "/",
    response_model=ApiResponse[OffreResponse],
    status_code=status.HTTP_201_CREATED,
)
def create_offre(
    payload: OffreCreate,
    current_user: User = Depends(require_role(UserRole.DRH,
                                              UserRole.ADMIN,
                                              UserRole.DIRECTEUR,
                                              UserRole.DG)),
    db: Session = Depends(get_db),
) -> ApiResponse[OffreResponse]:
    offre = offres_service.create_offre(db, payload, current_user)
    return ApiResponse(data=OffreResponse.model_validate(offre))


@router.patch(
    "/{offre_id}/publier",
    response_model=ApiResponse[OffreResponse],
)
def publish_offre(
    offre_id: int,
    current_user: User = Depends(require_role(UserRole.DRH,
                                              UserRole.ADMIN,
                                              UserRole.DIRECTEUR,
                                              UserRole.DG)),
    db: Session = Depends(get_db),
) -> ApiResponse[OffreResponse]:
    offre = offres_service.publish_offre(db, offre_id, current_user)
    return ApiResponse(data=OffreResponse.model_validate(offre))


@router.patch(
    "/{offre_id}/cloturer",
    response_model=ApiResponse[OffreResponse],
)
def close_offre(
    offre_id: int,
    current_user: User = Depends(require_role(UserRole.DRH,
                                              UserRole.ADMIN,
                                              UserRole.DIRECTEUR,
                                              UserRole.DG)),
    db: Session = Depends(get_db),
) -> ApiResponse[OffreResponse]:
    offre = offres_service.close_offre(db, offre_id, current_user)
    return ApiResponse(data=OffreResponse.model_validate(offre))
