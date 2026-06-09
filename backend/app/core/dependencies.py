"""
FastAPI dependency: get_current_user
=====================================
Extracts the Bearer token from the Authorization header, validates it,
and returns the matching User row from the database.

All protected routes declare this dependency — they never touch JWT logic
directly. Single place to change auth behaviour for the whole app.

Usage
-----
    from app.core.dependencies import get_current_user

    @router.get("/something")
    def my_route(user: User = Depends(get_current_user)):
        ...
"""
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.database import get_db
from app.models.user import User

# ---------------------------------------------------------------------------
# OAuth2 scheme
# ---------------------------------------------------------------------------
# Points FastAPI to the login endpoint so Swagger UI shows an Authorize button.
# On each request FastAPI pulls the token out of:  Authorization: Bearer <token>
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# ---------------------------------------------------------------------------
# Dependency
# ---------------------------------------------------------------------------
def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Session = Depends(get_db),
) -> User:
    """
    Decode the JWT → read user id from ``sub`` claim → fetch User from DB.

    Raises HTTP 401 on any token problem (missing / expired / tampered).
    Raises HTTP 401 if the user id is absent from the payload.
    Raises HTTP 404 if the user no longer exists in the database.
    """
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_token(token)
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise credentials_exc
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise credentials_exc

    user = db.get(User, int(user_id))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user