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
from app.domains.users import service as user_service
from app.domains.users.model import User
from app.domains.users.schemas import UserCreate, UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/", response_model=PaginatedResponse[UserResponse])
def list_users(
    params: Annotated[PaginationParams, Depends()],
    _: User = Depends(require_role(UserRole.ADMIN, UserRole.DRH)),
    db: Session = Depends(get_db),
) -> PaginatedResponse[UserResponse]:
    users, total_items = user_service.list_users(db, params)
    return PaginatedResponse(
        data=[UserResponse.model_validate(user) for user in users],
        meta=PaginationMeta(
            page=params.page,
            page_size=params.page_size,
            total_items=total_items,
            total_pages=(total_items + params.page_size - 1) // params.page_size,
        ),
    )


@router.post(
    "/", response_model=ApiResponse[UserResponse], status_code=status.HTTP_201_CREATED
)
def create_user(
    payload: UserCreate,
    _: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> ApiResponse[UserResponse]:
    user = user_service.create_user(
        db,
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name,
        gsm=payload.gsm,
        role=payload.role,
    )
    return ApiResponse(data=UserResponse.model_validate(user))


@router.put("/{user_id}", response_model=ApiResponse[UserResponse])
def update_user(
    user_id: int,
    payload: UserUpdate,
    _: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> ApiResponse[UserResponse]:
    user = user_service.update_user(
        db,
        user_id=user_id,
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name,
        gsm=payload.gsm,
        role=payload.role,
        enabled=payload.enabled,
    )
    return ApiResponse(data=UserResponse.model_validate(user))


@router.delete("/{user_id}", response_model=ApiResponse[None])
def delete_user(
    user_id: int,
    _: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> ApiResponse[None]:
    user_service.soft_delete_user(db, user_id)
    return ApiResponse(data=None)
