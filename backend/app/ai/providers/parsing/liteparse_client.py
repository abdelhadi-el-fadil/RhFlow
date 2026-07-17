"""LiteParse client factory for CV document parsing."""

from importlib import import_module
from pathlib import Path
from typing import Any, Protocol, cast

from app.config import settings


class LiteParseClient(Protocol):
    def parse(self, file_data: str | Path | bytes) -> Any: ...


def create_liteparse_client() -> LiteParseClient:
    """Build a configured LiteParse client from app settings."""
    module = import_module("liteparse")
    liteparse_cls = getattr(module, "LiteParse", None)
    if liteparse_cls is None:
        raise RuntimeError("liteparse.LiteParse is not available")

    client = liteparse_cls(
        quiet=settings.LITEPARSE_QUIET,
        max_pages=settings.LITEPARSE_MAX_PAGES,
        ocr_enabled=settings.LITEPARSE_OCR_ENABLED,
        ocr_language=settings.LITEPARSE_OCR_LANGUAGE,
        output_format="markdown",
        image_mode="off",
    )
    return cast(LiteParseClient, client)
