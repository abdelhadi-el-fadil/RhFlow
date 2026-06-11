"""
Exceptions métier — domaine "auth".
"""
from app.core.exceptions import AppException


class InvalidCredentialsException(AppException):
    """Email ou mot de passe incorrect — message volontairement vague
    (ne révèle pas si l'email existe, anti-énumération)."""

    def __init__(self):
        super().__init__(401, "Incorrect email or password", "AUTH_INVALID_CREDENTIALS")


class InvalidTokenException(AppException):
    """Token JWT absent, malformé ou invalide."""

    def __init__(self):
        super().__init__(401, "Could not validate credentials", "AUTH_INVALID_TOKEN")


class TokenExpiredException(AppException):
    """Token JWT expiré."""

    def __init__(self):
        super().__init__(401, "Token has expired", "AUTH_TOKEN_EXPIRED")