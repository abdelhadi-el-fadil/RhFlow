"""
Shared enums — single source of truth (DRY).

Never redefine these as raw strings or local enums inside models, schemas,
or services. Always import from here.
"""
from enum import Enum


class UserRole(str, Enum):
    ADMIN = "ADMIN"
    DRH = "DRH"
    DIRECTEUR = "DIRECTEUR"
    DG = "DG"