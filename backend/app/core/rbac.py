"""
Role-Based Access Control (RBAC) — dependency factory
======================================================
``require_role(*roles)`` returns a FastAPI dependency that:
  1. Runs ``get_current_user`` first (validates the JWT).
  2. Checks that the user's role is in the allowed set.
  3. Returns the User object so the route can still use it.

Usage
-----
    from app.core.rbac import require_role
    from app.models.user import Role

    # Single role
    @router.delete("/users/{id}")
    def delete_user(user_id: int, _: User = Depends(require_role(Role.ADMIN))):
        ...

    # Multiple roles — any one is sufficient
    @router.get("/dashboard")
    def dashboard(me: User = Depends(require_role(Role.DG, Role.DIRECTEUR))):
        ...

Why a factory instead of a plain dependency?
Each route can declare a *different* set of allowed roles, so we need a
closure to capture that set at decoration time.
"""
from typing import Callable

from fastapi import Depends, HTTPException, status

from app.core.dependencies import get_current_user
from app.models.user import Role, User


def require_role(*roles: Role) -> Callable[..., User]:
    """
    Return a dependency that enforces role membership.

    Args:
        *roles: One or more :class:`~app.models.user.Role` values permitted
                to access the route.

    Returns:
        A FastAPI-compatible callable that resolves to the authenticated User.

    Raises:
        HTTP 403 if the user's role is not in *roles*.
    """
    allowed: set[Role] = set(roles)

    def _enforce(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Access denied. "
                    f"Required: {', '.join(r.value for r in allowed)}. "
                    f"Your role: {current_user.role.value}."
                ),
            )
        return current_user

    return _enforce