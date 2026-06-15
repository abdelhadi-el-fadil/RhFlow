"""
Business exceptions — "users" domain.
"""
from app.core.exceptions import AppException


class UserNotFoundException(AppException):
    """Raised when a referenced user (e.g. by a JWT) no longer exists."""

    def __init__(self) -> None:
        super().__init__(404, "User not found", "USERS_NOT_FOUND")