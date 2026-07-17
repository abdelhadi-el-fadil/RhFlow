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
from app.domains.directions import service as directions_service
from app.domains.directions.schemas import (
    DirectionCreate,
    DirectionResponse,
    DirectionUpdate,
)
from app.domains.users.model import User

router = APIRouter(prefix="/directions", tags=["Directions"])


@router.get("/", response_model=PaginatedResponse[DirectionResponse])
def list_directions(
    params: Annotated[PaginationParams, Depends()],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PaginatedResponse[DirectionResponse]:
    items, total = directions_service.list_directions(db, params, current_user)
    return PaginatedResponse(
        data=[DirectionResponse.model_validate(i) for i in items],
        meta=PaginationMeta(
            page=params.page,
            page_size=params.page_size,
            total_items=total,
            total_pages=(total + params.page_size - 1) // params.page_size,
        ),
    )


@router.get("/{direction_id}", response_model=ApiResponse[DirectionResponse])
def get_direction(
    direction_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[DirectionResponse]:
    direction = directions_service.get_direction(db, direction_id, current_user)
    return ApiResponse(data=DirectionResponse.model_validate(direction))


@router.post(
    "/",
    response_model=ApiResponse[DirectionResponse],
    status_code=status.HTTP_201_CREATED,
)
def create_direction(
    payload: DirectionCreate,
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.DRH)),
    db: Session = Depends(get_db),
) -> ApiResponse[DirectionResponse]:
    direction = directions_service.create_direction(db, payload, current_user)
    return ApiResponse(data=DirectionResponse.model_validate(direction))


@router.put("/{direction_id}", response_model=ApiResponse[DirectionResponse])
def update_direction(
    direction_id: int,
    payload: DirectionUpdate,
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.DRH)),
    db: Session = Depends(get_db),
) -> ApiResponse[DirectionResponse]:
    direction = directions_service.update_direction(
        db,
        direction_id,
        payload,
        current_user,
    )
    return ApiResponse(data=DirectionResponse.model_validate(direction))


@router.delete("/{direction_id}", response_model=ApiResponse[None])
def delete_direction(
    direction_id: int,
    _: User = Depends(require_role(UserRole.ADMIN, UserRole.DRH)),
    db: Session = Depends(get_db),
) -> ApiResponse[None]:
    directions_service.soft_delete_direction(db, direction_id)
    return ApiResponse(data=None)
