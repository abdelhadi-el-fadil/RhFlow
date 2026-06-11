"""
FastAPI dependencies: get_current_user, require_role
======================================================
``get_current_user`` extracts the Bearer token and returns the matching
User (delegates to the auth service).

``require_role(*roles)`` builds on get_current_user to enforce RBAC.

Usage
-----
    from app.core.dependencies import get_current_user, require_role

    @router.get("/something")
    def my_route(user: User = Depends(get_current_user)):
        ...

    @router.delete("/users/{id}")
    def delete_user(user_id: int, _: User = Depends(require_role(UserRole.ADMIN))):
        ...
"""
from typing import Annotated, Callable

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.enums import UserRole
from app.core.exceptions import ForbiddenException
from app.database import get_db
from app.domains.auth.service import get_current_user_from_token
from app.domains.users.model import User

# ---------------------------------------------------------------------------
# OAuth2 scheme — points to /auth/login for Swagger's "Authorize" button
# ---------------------------------------------------------------------------
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# ---------------------------------------------------------------------------
# get_current_user
# ---------------------------------------------------------------------------
def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Session = Depends(get_db),
) -> User:
    """Resolve the authenticated user from the Bearer token."""
    return get_current_user_from_token(db, token)


# ---------------------------------------------------------------------------
# require_role
# ---------------------------------------------------------------------------
def require_role(*roles: UserRole) -> Callable[..., User]:
    """Return a dependency that checks the user's role is one of *roles*.
    Raises ForbiddenException otherwise."""
    allowed: set[UserRole] = set(roles)

    def _enforce(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed:
            raise ForbiddenException()
        return current_user

    return _enforce