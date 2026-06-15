"""
Business exceptions — "auth" domain.
"""
from app.core.exceptions import AppException


class InvalidCredentialsException(AppException):
    """Wrong email or password — message deliberately vague
    (does not reveal whether the email exists, anti-enumeration)."""

    def __init__(self) -> None:
        super().__init__(401, "Incorrect email or password", "AUTH_INVALID_CREDENTIALS")


class InvalidTokenException(AppException):
    """Missing, malformed, or invalid JWT."""

    def __init__(self) -> None:
        super().__init__(401, "Could not validate credentials", "AUTH_INVALID_TOKEN")


class TokenExpiredException(AppException):
    """Expired JWT."""

    def __init__(self) -> None:
        super().__init__(401, "Token has expired", "AUTH_TOKEN_EXPIRED")