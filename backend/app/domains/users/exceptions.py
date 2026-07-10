"""
Business exceptions — "users" domain.
"""
from app.core.exceptions import AppException, ConflictException, ForbiddenException


class UserNotFoundException(AppException):
    """Raised when a referenced user (e.g. by a JWT) no longer exists."""

    def __init__(self) -> None:
        super().__init__(404, "User not found", "USERS_NOT_FOUND")


class EmailAlreadyExistsException(ConflictException):
    """Raised when creating or updating a user with an existing email."""

    def __init__(self) -> None:
        super().__init__("Email already exists")
        self.code = "USERS_EMAIL_ALREADY_EXISTS"


class UserDisabledException(ForbiddenException):
    """Raised when a disabled user tries to access a protected resource."""

    def __init__(self) -> None:
        super().__init__()
        self.detail = "User account is disabled"
        self.code = "USERS_DISABLED"


class InvalidSignatureContentTypeException(AppException):
    def __init__(self) -> None:
        super().__init__(
            400,
            "Signature file must be image/png or image/jpeg",
            "USERS_INVALID_SIGNATURE_CONTENT_TYPE",
        )


class SignatureNotFoundException(AppException):
    def __init__(self) -> None:
        super().__init__(404, "Signature not found", "USERS_SIGNATURE_NOT_FOUND")


class SignatureStorageException(AppException):
    def __init__(self, detail: str = "Signature storage operation failed") -> None:
        super().__init__(500, detail, "USERS_SIGNATURE_STORAGE_ERROR")
