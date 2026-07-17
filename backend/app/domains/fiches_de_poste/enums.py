"""Domain enums for job descriptions."""

from enum import Enum


class FicheStatus(str, Enum):
    DRAFT = "DRAFT"
    VALIDATED = "VALIDATED"
    ARCHIVED = "ARCHIVED"
