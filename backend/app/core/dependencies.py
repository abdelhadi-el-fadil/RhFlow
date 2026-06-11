"""
FastAPI dependencies: get_current_user, require_role
======================================================
``get_current_user`` extrait le Bearer token et retourne le User
correspondant (délègue au service auth).

``require_role(*roles)`` s'appuie sur get_current_user pour appliquer le RBAC.

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
# OAuth2 scheme — pointe vers /auth/login pour le bouton "Authorize" de Swagger
# ---------------------------------------------------------------------------
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# ---------------------------------------------------------------------------
# get_current_user
# ---------------------------------------------------------------------------
def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Session = Depends(get_db),
) -> User:
    """Résout l'utilisateur authentifié à partir du Bearer token."""
    return get_current_user_from_token(db, token)


# ---------------------------------------------------------------------------
# require_role
# ---------------------------------------------------------------------------
def require_role(*roles: UserRole) -> Callable[..., User]:
    """Retourne une dépendance qui vérifie que le rôle de l'utilisateur
    fait partie de *roles*. Lève ForbiddenException sinon."""
    allowed: set[UserRole] = set(roles)

    def _enforce(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed:
            raise ForbiddenException()
        return current_user

    return _enforce