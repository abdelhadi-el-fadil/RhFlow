"""
Business exceptions — "directions" domain.
"""
from app.core.exceptions import AppException, ConflictException


class DirectionsNotFoundException(AppException):
    def __init__(self) -> None:
        super().__init__(404, "Direction not found", "DIRECTIONS_NOT_FOUND")


class DirectionCodeAlreadyExistsException(ConflictException):
    def __init__(self) -> None:
        super().__init__("Direction code already exists")
        self.code = "DIRECTIONS_CODE_ALREADY_EXISTS"
