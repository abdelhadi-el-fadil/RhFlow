"""
Authentication router
=====================
POST /auth/login  — exchange credentials for a JWT access token
GET  /auth/me     — return the profile of the authenticated user

Mounted in main.py:
    from app.routers.auth import router as auth_router
    app.include_router(auth_router)
"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.core.security import create_access_token, verify_password
from app.database import get_db
from app.models.user import User,UserRole

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class TokenResponse(BaseModel):
    """Returned by POST /auth/login."""
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """Returned by GET /auth/me."""
    id: int
    email: str
    full_name: str | None
    role: str

    model_config = {"from_attributes": True}  # ORM → Pydantic


# ---------------------------------------------------------------------------
# POST /auth/login
# ---------------------------------------------------------------------------

@router.post("/login", response_model=TokenResponse)
def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db),
):
    """
    Authenticate and return a JWT.

    Accepts ``application/x-www-form-urlencoded`` with fields:
      - ``username`` — the user's email address
      - ``password`` — plain-text password

    Flow:
      1. Find user by email (``username`` field per OAuth2 spec).
      2. Verify bcrypt hash — same vague error whether email or password
         is wrong (prevents user-enumeration attacks).
      3. Issue a JWT with ``sub=user.id`` + ``role`` + ``email`` claims.

    The client stores the token and sends it on every subsequent request as:
        Authorization: Bearer <token>
    """
    user: User | None = (
        db.query(User).filter(User.email == form_data.username).first()
    )
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(
        subject=user.id,
        extra_claims={"role": user.role.value, "email": user.email},
    )
    return TokenResponse(access_token=token)


# ---------------------------------------------------------------------------
# GET /auth/me
# ---------------------------------------------------------------------------

@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    """
    Return the profile of the currently authenticated user.

    ``get_current_user`` already fetched the user from the DB, so this
    route does zero extra work — it just serialises and returns it.
    """
    return current_user