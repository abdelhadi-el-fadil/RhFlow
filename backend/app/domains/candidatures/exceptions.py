"""Business exceptions - candidatures domain."""

from app.core.exceptions import AppException, ConflictException


class CandidatureNotFoundException(AppException):
    def __init__(self) -> None:
        super().__init__(404, "Candidature not found", "CANDIDATURE_NOT_FOUND")


class CandidatureFileTypeNotAllowedException(AppException):
    def __init__(self) -> None:
        super().__init__(
            409, "Unsupported candidature file type", "CANDIDATURE_FILE_TYPE"
        )


class CandidatureStorageException(AppException):
    def __init__(self, detail: str = "Failed to store candidature file") -> None:
        super().__init__(500, detail, "CANDIDATURE_STORAGE_ERROR")


class CandidatureFileTooLargeException(AppException):
    def __init__(self, max_bytes: int) -> None:
        super().__init__(
            409,
            f"Candidature file exceeds max size ({max_bytes} bytes)",
            "CANDIDATURE_FILE_TOO_LARGE",
        )


class CandidatureDuplicateEmailException(ConflictException):
    def __init__(self) -> None:
        super().__init__("Candidate email already exists for this project")
        self.code = "CANDIDATURE_EMAIL_DUPLICATE"


class CandidatureAnalysisInProgressException(ConflictException):
    def __init__(self) -> None:
        super().__init__("Candidature analysis already in progress")
        self.code = "CANDIDATURE_ANALYSIS_IN_PROGRESS"
