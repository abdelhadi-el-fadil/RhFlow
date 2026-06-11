"""
Router — "auth" domain.

POST /auth/login — exchange credentials for a JWT
GET  /auth/me    — profile of the authenticated user
"""
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.core.schemas import ApiResponse
from app.database import get_db
from app.domains.auth import service as auth_service
from app.domains.auth.schemas import TokenResponse
from app.domains.users.model import User
from app.domains.users.schemas import UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=ApiResponse[TokenResponse])
def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db),
) -> ApiResponse[TokenResponse]:
    token = auth_service.login(db, form_data.username, form_data.password)
    return ApiResponse(data=token)


@router.get("/me", response_model=ApiResponse[UserResponse])
def me(current_user: User = Depends(get_current_user)) -> ApiResponse[UserResponse]:
    return ApiResponse(data=UserResponse.model_validate(current_user))