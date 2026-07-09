"""Recruitment domain enums."""
from enum import Enum


class ProjetStatus(str, Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"


class BesoinStatus(str, Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class BesoinPriority(str, Enum):
    HAUTE = "HAUTE"
    NORMALE = "NORMALE"
    BASSE = "BASSE"
