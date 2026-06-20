"""Business exceptions — fiches de poste domain."""
from app.core.exceptions import AppException, ConflictException


class FicheDePosteNotFoundException(AppException):
    def __init__(self) -> None:
        super().__init__(404, "Job description not found", "FICHES_NOT_FOUND")


class FicheDePosteInvalidTransitionException(ConflictException):
    def __init__(self) -> None:
        super().__init__("Invalid fiche de poste transition")
        self.code = "FICHES_INVALID_TRANSITION"
