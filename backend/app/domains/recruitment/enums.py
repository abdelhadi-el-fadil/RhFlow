"""Recruitment domain enums."""

from enum import Enum


class ProjetStatus(str, Enum):
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"


class BesoinStatus(str, Enum):
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class BesoinPriority(str, Enum):
    HAUTE = "HAUTE"
    NORMALE = "NORMALE"
    BASSE = "BASSE"
