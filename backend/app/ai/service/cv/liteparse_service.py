"""Compatibility wrapper for legacy imports."""

from app.ai.providers.parsing.liteparse_client import (
    LiteParseClient,
    create_liteparse_client,
)

__all__ = ["LiteParseClient", "create_liteparse_client"]
