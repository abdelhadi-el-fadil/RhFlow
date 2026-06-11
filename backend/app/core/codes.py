"""
Generic error codes — single source of truth (DRY) for the base
exceptions (app/core/exceptions.py), reused by every domain.

Domain-specific codes (e.g. AUTH_INVALID_CREDENTIALS,
USERS_EMAIL_ALREADY_EXISTS) do NOT belong here — they are defined directly
in app/domains/<domain>/exceptions.py, prefixed with the domain name.
"""


class ErrorCode:
    NOT_FOUND = "NOT_FOUND"
    FORBIDDEN = "FORBIDDEN"
    UNAUTHORIZED = "UNAUTHORIZED"
    CONFLICT = "CONFLICT"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"