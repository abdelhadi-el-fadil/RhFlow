"""Router — fiches de poste domain."""
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_role
from app.core.enums import UserRole
from app.core.schemas import (
    ApiResponse,
    PaginatedResponse,
    PaginationMeta,
    PaginationParams,
)
from app.database import get_db
from app.domains.fiches_de_poste import service as fiche_service
from app.domains.fiches_de_poste.schemas import (
    FicheDePosteCreate,
    FicheDePosteResponse,
    FicheDePosteUpdate,
)
from app.domains.users.model import User

router = APIRouter(prefix="/fiches-de-poste", tags=["Fiches de poste"])


@router.get("/", response_model=PaginatedResponse[FicheDePosteResponse])
def list_fiches(
    params: Annotated[PaginationParams, Depends()],
    direction_id: int | None = None,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PaginatedResponse[FicheDePosteResponse]:
    items, total = fiche_service.list_fiches(db, params, direction_id)
    return PaginatedResponse(
        data=[FicheDePosteResponse.model_validate(item) for item in items],
        meta=PaginationMeta(
            page=params.page,
            page_size=params.page_size,
            total_items=total,
            total_pages=(total + params.page_size - 1) // params.page_size,
        ),
    )


@router.post(
    "/",
    response_model=ApiResponse[FicheDePosteResponse],
    status_code=status.HTTP_201_CREATED,
)
def create_fiche(
    payload: FicheDePosteCreate,
    current_user: User = Depends(
        require_role(UserRole.ADMIN, UserRole.DRH, UserRole.DIRECTEUR)
    ),
    db: Session = Depends(get_db),
) -> ApiResponse[FicheDePosteResponse]:
    fiche = fiche_service.create_fiche(db, payload, current_user)
    return ApiResponse(data=FicheDePosteResponse.model_validate(fiche))


@router.get("/{fiche_id}", response_model=ApiResponse[FicheDePosteResponse])
def get_fiche(
    fiche_id: int,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[FicheDePosteResponse]:
    fiche = fiche_service.get_fiche(db, fiche_id)
    return ApiResponse(data=FicheDePosteResponse.model_validate(fiche))


@router.put("/{fiche_id}", response_model=ApiResponse[FicheDePosteResponse])
def update_fiche(
    fiche_id: int,
    payload: FicheDePosteUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[FicheDePosteResponse]:
    fiche = fiche_service.update_fiche(db, fiche_id, payload, current_user)
    return ApiResponse(data=FicheDePosteResponse.model_validate(fiche))


@router.delete("/{fiche_id}", response_model=ApiResponse[None])
def delete_fiche(
    fiche_id: int,
    current_user: User = Depends(
        require_role(UserRole.ADMIN, UserRole.DRH)
        ),
    db: Session = Depends(get_db),
) -> ApiResponse[None]:
    fiche_service.delete_fiche(db, fiche_id, current_user)
    return ApiResponse(data=None)
