from app.core.codes import ErrorCode


class AppException(Exception):
    def __init__(self, status_code: int, detail: str, code: str):
        self.status_code = status_code
        self.detail = detail
        self.code = code


class NotFoundException(AppException):
    def __init__(self, resource: str):
        super().__init__(404, f"{resource} not found", ErrorCode.NOT_FOUND)


class ForbiddenException(AppException):
    def __init__(self):
        super().__init__(403, "Insufficient permissions", ErrorCode.FORBIDDEN)


class ConflictException(AppException):
    def __init__(self, detail: str):
        super().__init__(409, detail, ErrorCode.CONFLICT)


class UnauthorizedException(AppException):
    def __init__(self):
        super().__init__(401, "Not authenticated", ErrorCode.UNAUTHORIZED)