"""LLM provider configuration for llama_index Settings."""

from llama_index.core import Settings
from llama_index.llms.openai_like import OpenAILike

from app.config import settings


def _normalize_api_base(url: str) -> str:
    base = url.strip().strip('"').strip("'").rstrip("/")
    for suffix in ("/chat/completions", "/completions"):
        if base.endswith(suffix):
            base = base[: -len(suffix)]
    return base


def configure_llm() -> None:
    """Configure the singleton LLM used by application services."""
    api_base = _normalize_api_base(settings.LLM_BASE_URL)

    Settings.llm = OpenAILike(
        model=settings.LLM_MODEL,
        api_key=settings.LLM_API_KEY,
        api_base=api_base,
        is_chat_model=True,
    )
