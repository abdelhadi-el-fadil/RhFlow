"""Compatibility wrapper for legacy imports."""

from app.ai.service.cv.liteparse_service import LiteParseClient, create_liteparse_client

__all__ = ["LiteParseClient", "create_liteparse_client"]
