"""
Schémas de réponse génériques — source unique de vérité pour le format
des réponses API (DRY), réutilisés par tous les domaines.

Usage :
    return ApiResponse(data=user_schema)
    return PaginatedResponse(data=items, meta=PaginationMeta(...))
"""
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """Enveloppe standard pour une ressource unique."""
    data: T
    message: str | None = None


class PaginationMeta(BaseModel):
    """Métadonnées de pagination renvoyées au frontend."""
    page: int
    page_size: int
    total_items: int
    total_pages: int


class PaginatedResponse(BaseModel, Generic[T]):
    """Enveloppe standard pour une liste paginée."""
    data: list[T]
    meta: PaginationMeta


class PaginationParams(BaseModel):
    """Query params communs (?page=1&page_size=20) pour les endpoints de liste."""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size