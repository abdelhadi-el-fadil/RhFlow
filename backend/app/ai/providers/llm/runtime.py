"""Dynamic access to the configured llama_index LLM.

The app configures Settings.llm at startup. This proxy keeps imports
stable while always delegating to the current configured instance.
"""

from __future__ import annotations

from typing import Any

from llama_index.core import Settings


class _LlmProxy:
    def _target(self) -> Any:
        llm_instance = Settings.llm
        if llm_instance is None:
            raise RuntimeError("LLM is not configured. Check startup initialization.")
        return llm_instance

    def chat(self, *args: Any, **kwargs: Any) -> Any:
        return self._target().chat(*args, **kwargs)

    def complete(self, *args: Any, **kwargs: Any) -> Any:
        return self._target().complete(*args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._target(), name)


llm = _LlmProxy()
