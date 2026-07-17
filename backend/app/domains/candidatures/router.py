"""Router - candidatures domain."""

from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, UploadFile, status
from sqlalchemy.orm import Session

from app.core.dependencies import (
    get_current_user,
    get_minio_candidatures_storage_service,
)
from app.core.minio_service import MinioStorageService
from app.core.schemas import (
    ApiResponse,
    PaginatedResponse,
    PaginationMeta,
    PaginationParams,
)
from app.database import get_db
from app.domains.candidatures import service as candidatures_service
from app.domains.candidatures.schemas import CandidatureResponse
from app.domains.users.model import User

router = APIRouter(
    prefix="/candidatures",
    tags=["Candidatures"],
)

project_router = APIRouter(
    prefix="/projets/{projet_id}/candidatures",
    tags=["Candidatures"],
)


@project_router.get("/", response_model=PaginatedResponse[CandidatureResponse])
def list_candidatures(
    projet_id: int,
    params: Annotated[PaginationParams, Depends()],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PaginatedResponse[CandidatureResponse]:
    items, total = candidatures_service.list_candidatures(
        db,
        params,
        projet_id,
        current_user,
    )
    return PaginatedResponse(
        data=[CandidatureResponse.model_validate(item) for item in items],
        meta=PaginationMeta(
            page=params.page,
            page_size=params.page_size,
            total_items=total,
            total_pages=(total + params.page_size - 1) // params.page_size,
        ),
    )


@router.post(
    "/",
    response_model=ApiResponse[CandidatureResponse],
    status_code=status.HTTP_201_CREATED,
)
async def upload_candidature(
    background_tasks: BackgroundTasks,
    projet_recrutement_id: int = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    storage: MinioStorageService = Depends(get_minio_candidatures_storage_service),
) -> ApiResponse[CandidatureResponse]:
    payload = await file.read()
    content_type = file.content_type or "application/octet-stream"
    filename = file.filename or "cv"
    await file.close()

    candidature = candidatures_service.create_uploaded_candidature(
        db=db,
        projet_recrutement_id=projet_recrutement_id,
        current_user=current_user,
        storage=storage,
        filename=filename,
        content_type=content_type,
        payload=payload,
    )

    return ApiResponse(data=CandidatureResponse.model_validate(candidature))


@router.post(
    "/{candidature_id}/extract",
    response_model=ApiResponse[CandidatureResponse],
)
def extract_candidature(
    candidature_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    storage: MinioStorageService = Depends(get_minio_candidatures_storage_service),
) -> ApiResponse[CandidatureResponse]:
    candidature = candidatures_service.start_candidature_extraction(
        db,
        candidature_id,
        current_user,
    )
    db.commit()

    candidatures_service.process_candidature_extraction(
        candidature.id,
        storage,
    )
    db.expire_all()
    candidature = candidatures_service.get_candidature(db, candidature_id, current_user)

    return ApiResponse(
        data=CandidatureResponse.model_validate(candidature),
        message="Extraction completed",
    )


@router.post(
    "/{candidature_id}/evaluate",
    response_model=ApiResponse[CandidatureResponse],
)
def evaluate_candidature(
    candidature_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    storage: MinioStorageService = Depends(get_minio_candidatures_storage_service),
) -> ApiResponse[CandidatureResponse]:
    candidature = candidatures_service.start_candidature_evaluation(
        db,
        candidature_id,
        current_user,
    )
    db.commit()

    candidatures_service.process_candidature_evaluation(
        candidature.id,
        storage,
    )
    db.expire_all()
    candidature = candidatures_service.get_candidature(db, candidature_id, current_user)

    return ApiResponse(
        data=CandidatureResponse.model_validate(candidature),
        message="Evaluation completed",
    )
