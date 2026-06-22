"""Business exceptions — offres domain."""
from app.core.exceptions import AppException, ConflictException


class OffreNotFoundException(AppException):
    def __init__(self) -> None:
        super().__init__(404, "Offer not found", "OFFRES_NOT_FOUND")


class OffreInvalidTransitionException(ConflictException):
    def __init__(self) -> None:
        super().__init__("Invalid offer transition")
        self.code = "OFFRES_INVALID_TRANSITION"


class OffreBesoinNotPublishableException(ConflictException):
    def __init__(self) -> None:
        super().__init__("Recruitment need is not publishable")
        self.code = "OFFRES_BESOIN_NOT_PUBLISHABLE"
