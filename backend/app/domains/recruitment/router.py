"""Router — recruitment domain."""
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
from app.domains.recruitment import service as recruitment_service
from app.domains.recruitment.enums import BesoinPriority
from app.domains.recruitment.schemas import (
    BesoinRecrutementCreate,
    BesoinRecrutementResponse,
    BesoinRecrutementUpdate,
    ProjetRecrutementCardResponse,
    ProjetRecrutementCreate,
    ProjetRecrutementResponse,
    ProjetRecrutementUpdate,
    RejectBesoinRequest,
)
from app.domains.users.model import User

router = APIRouter(prefix="/projets", tags=["Recruitment projects"])
besoins_router = APIRouter(prefix="/besoins", tags=["Recruitment needs"])


@router.get("/", response_model=PaginatedResponse[ProjetRecrutementCardResponse])
def list_projects(
    params: Annotated[PaginationParams, Depends()],
    direction_id: int | None = None,
    archived: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PaginatedResponse[ProjetRecrutementCardResponse]:
    items, total = recruitment_service.list_projects(
        db,
        params,
        current_user,
        direction_id=direction_id,
        archived=archived,
    )
    return PaginatedResponse(
        data=[ProjetRecrutementCardResponse.model_validate(item) for item in items],
        meta=PaginationMeta(
            page=params.page,
            page_size=params.page_size,
            total_items=total,
            total_pages=(total + params.page_size - 1) // params.page_size,
        ),
    )


@router.post(
    "/",
    response_model=ApiResponse[ProjetRecrutementResponse],
    status_code=status.HTTP_201_CREATED,
)
def create_project(
    payload: ProjetRecrutementCreate,
    current_user: User = Depends(require_role(UserRole.DRH, UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> ApiResponse[ProjetRecrutementResponse]:
    project = recruitment_service.create_project(db, payload, current_user)
    return ApiResponse(data=ProjetRecrutementResponse.model_validate(project))


@router.put("/{projet_id}", response_model=ApiResponse[ProjetRecrutementResponse])
def update_project(
    projet_id: int,
    payload: ProjetRecrutementUpdate,
    current_user: User = Depends(require_role(UserRole.DRH, UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> ApiResponse[ProjetRecrutementResponse]:
    project = recruitment_service.update_project(db, projet_id, payload, current_user)
    return ApiResponse(data=ProjetRecrutementResponse.model_validate(project))


@router.delete("/{projet_id}", response_model=ApiResponse[None])
def delete_project(
    projet_id: int,
    current_user: User = Depends(require_role(UserRole.DRH, UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> ApiResponse[None]:
    recruitment_service.delete_project(db, projet_id, current_user)
    return ApiResponse(data=None)


@router.patch(
        "/{projet_id}/cloturer", response_model=ApiResponse[ProjetRecrutementResponse]
        )
def close_project(
    projet_id: int,
    current_user: User = Depends(require_role(UserRole.DRH, UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> ApiResponse[ProjetRecrutementResponse]:
    project = recruitment_service.close_project(db, projet_id, current_user)
    return ApiResponse(data=ProjetRecrutementResponse.model_validate(project))


@router.post(
    "/{projet_id}/besoins/{besoin_id}",
    response_model=ApiResponse[ProjetRecrutementResponse],
)
def attach_need(
    projet_id: int,
    besoin_id: int,
    current_user: User = Depends(require_role(UserRole.DRH, UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> ApiResponse[ProjetRecrutementResponse]:
    project = recruitment_service.attach_besoin(
        db, projet_id, besoin_id, current_user
    )
    return ApiResponse(data=ProjetRecrutementResponse.model_validate(project))


@router.get("/{projet_id}", response_model=ApiResponse[ProjetRecrutementResponse])
def get_project(
    projet_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[ProjetRecrutementResponse]:
    project = recruitment_service.get_project(db, projet_id, current_user)
    return ApiResponse(data=ProjetRecrutementResponse.model_validate(project))


@besoins_router.get(
    "/",
    response_model=PaginatedResponse[BesoinRecrutementResponse],
)
def list_besoins(
    params: Annotated[PaginationParams, Depends()],
    direction_id: int | None = None,
    priority: BesoinPriority | None = None,
    archived: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PaginatedResponse[BesoinRecrutementResponse]:
    items, total = recruitment_service.list_besoins(
        db,
        params,
        current_user,
        direction_id=direction_id,
        priority=priority,
        archived=archived,
    )
    return PaginatedResponse(
        data=[BesoinRecrutementResponse.model_validate(item) for item in items],
        meta=PaginationMeta(
            page=params.page,
            page_size=params.page_size,
            total_items=total,
            total_pages=(total + params.page_size - 1) // params.page_size,
        ),
    )


@besoins_router.post(
    "/",
    response_model=ApiResponse[BesoinRecrutementResponse],
    status_code=status.HTTP_201_CREATED,
)
def create_besoin(
    payload: BesoinRecrutementCreate,
    current_user: User = Depends(require_role(UserRole.DIRECTEUR,
                                              UserRole.DRH,
                                              UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> ApiResponse[BesoinRecrutementResponse]:
    besoin = recruitment_service.create_besoin(db, payload, current_user)
    return ApiResponse(data=BesoinRecrutementResponse.model_validate(besoin))


@besoins_router.get(
    "/{besoin_id}",
    response_model=ApiResponse[BesoinRecrutementResponse],
)
def get_besoin(
    besoin_id: int,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[BesoinRecrutementResponse]:
    besoin = recruitment_service.get_besoin(db, besoin_id)
    return ApiResponse(data=BesoinRecrutementResponse.model_validate(besoin))


@besoins_router.put(
    "/{besoin_id}",
    response_model=ApiResponse[BesoinRecrutementResponse],
)
def update_besoin(
    besoin_id: int,
    payload: BesoinRecrutementUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[BesoinRecrutementResponse]:
    besoin = recruitment_service.update_besoin(db, besoin_id, payload, current_user)
    return ApiResponse(data=BesoinRecrutementResponse.model_validate(besoin))


@besoins_router.delete("/{besoin_id}", response_model=ApiResponse[None])
def delete_besoin(
    besoin_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[None]:
    recruitment_service.delete_besoin(db, besoin_id, current_user)
    return ApiResponse(data=None)


@besoins_router.post(
    "/{besoin_id}/soumettre",
    response_model=ApiResponse[BesoinRecrutementResponse],
)
def submit_besoin(
    besoin_id: int,
    current_user: User = Depends(require_role(UserRole.DIRECTEUR,
                                              UserRole.DRH,
                                              UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> ApiResponse[BesoinRecrutementResponse]:
    besoin = recruitment_service.submit_besoin(db, besoin_id, current_user)
    return ApiResponse(data=BesoinRecrutementResponse.model_validate(besoin))


@besoins_router.post(
    "/{besoin_id}/approuver",
    response_model=ApiResponse[BesoinRecrutementResponse],
)
def approve_besoin(
    besoin_id: int,
    current_user: User = Depends(require_role(UserRole.DRH, UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> ApiResponse[BesoinRecrutementResponse]:
    besoin = recruitment_service.approve_besoin(db, besoin_id, current_user)
    return ApiResponse(data=BesoinRecrutementResponse.model_validate(besoin))


@besoins_router.post(
    "/{besoin_id}/rejeter",
    response_model=ApiResponse[BesoinRecrutementResponse],
)
def reject_besoin(
    besoin_id: int,
    payload: RejectBesoinRequest,
    current_user: User = Depends(require_role(UserRole.DRH, UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> ApiResponse[BesoinRecrutementResponse]:
    besoin = recruitment_service.reject_besoin(db, besoin_id, payload, current_user)
    return ApiResponse(data=BesoinRecrutementResponse.model_validate(besoin))
