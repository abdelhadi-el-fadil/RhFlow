"""
Codes d'erreur génériques — source unique de vérité (DRY) pour les
exceptions de base (app/core/exceptions.py), réutilisées par tous les domaines.

Les codes spécifiques à un domaine (ex: AUTH_INVALID_CREDENTIALS,
USERS_EMAIL_ALREADY_EXISTS) ne vont PAS ici — ils sont définis directement
dans app/domains/<domaine>/exceptions.py, préfixés par le nom du domaine.
"""


class ErrorCode:
    NOT_FOUND = "NOT_FOUND"
    FORBIDDEN = "FORBIDDEN"
    UNAUTHORIZED = "UNAUTHORIZED"
    CONFLICT = "CONFLICT"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"