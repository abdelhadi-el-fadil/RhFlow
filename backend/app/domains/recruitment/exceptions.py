"""Business exceptions — recruitment domain."""
from app.core.exceptions import AppException, ConflictException


class ProjetRecrutementNotFoundException(AppException):
    def __init__(self) -> None:
        super().__init__(404, "Recruitment project not found",
                         "RECRUTEMENT_PROJET_NOT_FOUND")


class BesoinRecrutementNotFoundException(AppException):
    def __init__(self) -> None:
        super().__init__(404, "Recruitment need not found",
                          "RECRUTEMENT_BESOIN_NOT_FOUND")


class BesoinRecrutementNotApprovedException(ConflictException):
    def __init__(self) -> None:
        super().__init__("Recruitment need is not approved")
        self.code = "RECRUTEMENT_BESOIN_NOT_APPROVED"


class BesoinRecrutementAlreadyAttachedException(ConflictException):
    def __init__(self) -> None:
        super().__init__("Recruitment need is already attached")
        self.code = "RECRUTEMENT_BESOIN_ALREADY_ATTACHED"


class BesoinRecrutementInvalidTransitionException(ConflictException):
    def __init__(self) -> None:
        super().__init__("Invalid recruitment need transition")
        self.code = "RECRUTEMENT_INVALID_TRANSITION"


class ProjetRecrutementInvalidTransitionException(ConflictException):
    def __init__(self) -> None:
        super().__init__("Invalid recruitment project transition")
        self.code = "RECRUTEMENT_PROJET_INVALID_TRANSITION"


class ProjetRecrutementLinkMismatchException(ConflictException):
    def __init__(self) -> None:
        super().__init__("Recruitment project links are inconsistent")
        self.code = "RECRUTEMENT_PROJET_LINK_MISMATCH"
