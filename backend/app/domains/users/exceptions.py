"""
Exceptions métier — domaine "users".
"""
from app.core.exceptions import AppException


class UserNotFoundException(AppException):
    """Levée quand un utilisateur référencé (ex: par un token JWT) n'existe plus."""

    def __init__(self):
        super().__init__(404, "User not found", "USERS_NOT_FOUND")