"""
Generic response schemas — single source of truth for the API response
format (DRY), reused by every domain.

Usage:
    return ApiResponse(data=user_schema)
    return PaginatedResponse(data=items, meta=PaginationMeta(...))
"""
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """Standard envelope for a single resource."""
    data: T
    message: str | None = None


class PaginationMeta(BaseModel):
    """Pagination metadata returned to the frontend."""
    page: int
    page_size: int
    total_items: int
    total_pages: int


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard envelope for a paginated list."""
    data: list[T]
    meta: PaginationMeta


class PaginationParams(BaseModel):
    """Common query params (?page=1&page_size=20) for list endpoints."""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size