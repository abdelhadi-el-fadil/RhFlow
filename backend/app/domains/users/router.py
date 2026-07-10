from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from app.core.dependencies import (
    get_current_user,
    get_minio_storage_service,
    require_role,
)
from app.core.enums import UserRole
from app.core.minio_service import MinioStorageService, MinioStorageServiceError
from app.core.schemas import (
    ApiResponse,
    PaginatedResponse,
    PaginationMeta,
    PaginationParams,
)
from app.database import get_db
from app.domains.users import service as user_service
from app.domains.users.exceptions import (
    InvalidSignatureContentTypeException,
    SignatureNotFoundException,
    SignatureStorageException,
)
from app.domains.users.model import User
from app.domains.users.schemas import (
    UserCreate,
    UserResponse,
    UserSignatureResponse,
    UserUpdate,
)

router = APIRouter(prefix="/users", tags=["Users"])

ALLOWED_SIGNATURE_CONTENT_TYPES = {"image/png", "image/jpeg"}
CONTENT_TYPE_TO_EXTENSION = {
    "image/png": "png",
    "image/jpeg": "jpg",
}


def _upload_signature_for_user(
    db: Session,
    storage: MinioStorageService,
    target_user: User,
    payload: bytes,
    content_type: str,
) -> User:
    if content_type not in ALLOWED_SIGNATURE_CONTENT_TYPES:
        raise InvalidSignatureContentTypeException()

    extension = CONTENT_TYPE_TO_EXTENSION[content_type]
    object_key = f"signatures/user-{target_user.id}.{extension}"
    old_key = target_user.signature_key
    try:
        storage.upload_bytes(
            object_key=object_key,
            payload=payload,
            content_type=content_type,
        )
        if old_key and old_key != object_key:
            storage.delete_object(old_key)
    except MinioStorageServiceError as exc:
        raise SignatureStorageException(str(exc)) from exc

    return user_service.set_signature(
        db,
        user_id=target_user.id,
        signature_key=object_key,
        signature_content_type=content_type,
    )


def _delete_signature_for_user(
    db: Session,
    storage: MinioStorageService,
    target_user: User,
) -> User:
    if not target_user.signature_key or not target_user.signature_content_type:
        raise SignatureNotFoundException()

    try:
        storage.delete_object(target_user.signature_key)
    except MinioStorageServiceError as exc:
        raise SignatureStorageException(str(exc)) from exc

    return user_service.clear_signature(db, user_id=target_user.id)


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
    _: User = Depends(require_role(UserRole.ADMIN, UserRole.DRH)),
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
    _: User = Depends(require_role(UserRole.ADMIN, UserRole.DRH)),
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
    _: User = Depends(require_role(UserRole.ADMIN, UserRole.DRH)),
    db: Session = Depends(get_db),
) -> ApiResponse[None]:
    user_service.soft_delete_user(db, user_id)
    return ApiResponse(data=None)


@router.post("/me/signature", response_model=ApiResponse[UserResponse])
async def upload_my_signature(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    storage: MinioStorageService = Depends(get_minio_storage_service),
) -> ApiResponse[UserResponse]:
    content_type = file.content_type or ""
    payload = await file.read()
    await file.close()

    user = _upload_signature_for_user(
        db=db,
        storage=storage,
        target_user=current_user,
        payload=payload,
        content_type=content_type,
    )
    return ApiResponse(data=UserResponse.model_validate(user))


@router.post("/{user_id}/signature", response_model=ApiResponse[UserResponse])
async def upload_user_signature(
    user_id: int,
    file: UploadFile = File(...),
    _: User = Depends(require_role(UserRole.ADMIN, UserRole.DRH)),
    db: Session = Depends(get_db),
    storage: MinioStorageService = Depends(get_minio_storage_service),
) -> ApiResponse[UserResponse]:
    target_user = user_service.get_user(db, user_id)
    content_type = file.content_type or ""
    payload = await file.read()
    await file.close()
    updated_user = _upload_signature_for_user(
        db=db,
        storage=storage,
        target_user=target_user,
        payload=payload,
        content_type=content_type,
    )
    return ApiResponse(data=UserResponse.model_validate(updated_user))


@router.delete("/{user_id}/signature", response_model=ApiResponse[UserResponse])
def delete_user_signature(
    user_id: int,
    _: User = Depends(require_role(UserRole.ADMIN, UserRole.DRH)),
    db: Session = Depends(get_db),
    storage: MinioStorageService = Depends(get_minio_storage_service),
) -> ApiResponse[UserResponse]:
    target_user = user_service.get_user(db, user_id)
    updated_user = _delete_signature_for_user(
        db=db,
        storage=storage,
        target_user=target_user,
    )
    return ApiResponse(data=UserResponse.model_validate(updated_user))


@router.get("/me/signature", response_model=ApiResponse[UserSignatureResponse])
def get_my_signature(
    current_user: User = Depends(get_current_user),
    storage: MinioStorageService = Depends(get_minio_storage_service),
) -> ApiResponse[UserSignatureResponse]:
    if not current_user.signature_key or not current_user.signature_content_type:
        raise SignatureNotFoundException()

    try:
        url = storage.get_presigned_get_url(current_user.signature_key)
    except MinioStorageServiceError as exc:
        raise SignatureStorageException(str(exc)) from exc

    return ApiResponse(
        data=UserSignatureResponse(
            signature_key=current_user.signature_key,
            signature_content_type=current_user.signature_content_type,
            url=url,
        )
    )


@router.get("/{user_id}/signature", response_model=ApiResponse[UserSignatureResponse])
def get_user_signature(
    user_id: int,
    _: User = Depends(require_role(UserRole.ADMIN, UserRole.DRH)),
    db: Session = Depends(get_db),
    storage: MinioStorageService = Depends(get_minio_storage_service),
) -> ApiResponse[UserSignatureResponse]:
    target_user = user_service.get_user(db, user_id)
    if not target_user.signature_key or not target_user.signature_content_type:
        raise SignatureNotFoundException()

    try:
        url = storage.get_presigned_get_url(target_user.signature_key)
    except MinioStorageServiceError as exc:
        raise SignatureStorageException(str(exc)) from exc

    return ApiResponse(
        data=UserSignatureResponse(
            signature_key=target_user.signature_key,
            signature_content_type=target_user.signature_content_type,
            url=url,
        )
    )
