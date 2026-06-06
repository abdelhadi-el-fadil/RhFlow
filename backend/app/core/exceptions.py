class AppException(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail


class NotFoundException(AppException):
    def __init__(self, resource: str):
        super().__init__(404, f"{resource} not found")


class ForbiddenException(AppException):
    def __init__(self):
        super().__init__(403, "Insufficient permissions")


class ConflictException(AppException):
    def __init__(self, detail: str):
        super().__init__(409, detail)


class UnauthorizedException(AppException):
    def __init__(self):
        super().__init__(401, "Not authenticated")
