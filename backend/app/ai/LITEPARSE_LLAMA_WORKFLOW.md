# LiteParse + LlamaIndex Architecture and Workflow

This document describes the recommended folder structure for CV parsing and LLM usage, the runtime flow, and where each type of file should live.

## 1) Target structure

```text
backend/app/
  ai/
    LITEPARSE_LLAMA_WORKFLOW.md
    factory.py                         # legacy compatibility wrapper
    cv_extraction.py                   # legacy compatibility wrapper
    liteparse_factory.py               # legacy compatibility wrapper
    cv_analysis_agents.py              # legacy compatibility wrapper

    providers/
      llm/
        configuration.py               # configure Settings.llm at startup
        runtime.py                     # singleton llm proxy used by services
      parsing/
        liteparse_client.py            # LiteParse client factory + protocol

    pipelines/
      cv/
        extraction_pipeline.py         # file -> markdown extraction pipeline

    service/
      chat_service.py                  # chat use case (uses providers.llm.runtime)
      cv/
        analysis_agents_service.py     # CV extraction/evaluation LLM logic
        extraction_service.py          # wrapper to pipelines.cv.extraction_pipeline
        liteparse_service.py           # wrapper to providers.parsing.liteparse_client

    router/
      chat_router.py
      offer_router.py

  llama_index.py                       # legacy compatibility wrapper
```

## 2) Separation of responsibilities

- providers: external tools/SDKs and connection setup.
- pipelines: deterministic processing flow (document/file transformations).
- service: business use cases and orchestration logic.
- router: FastAPI HTTP endpoints only.
- compatibility wrappers: old import paths that now forward to the new modules.

## 3) Runtime workflow

### A) App startup (LLM setup)

1. FastAPI lifespan runs configure_llm().
2. configure_llm() sets llama_index.core.Settings.llm once.
3. Any service imports llm proxy from providers.llm.runtime.
4. Proxy always reads the current Settings.llm instance.

Main files:
- app/main.py
- app/ai/providers/llm/configuration.py
- app/ai/providers/llm/runtime.py

### B) CV parsing flow (LiteParse)

1. API/service receives CV file path.
2. extraction_pipeline.extract_cv_to_markdown() is called.
3. Pipeline creates LiteParse client from providers.parsing.liteparse_client.
4. LiteParse parses pages.
5. Pipeline merges page markdown; fallback to raw text if page markdown is empty.

Main files:
- app/ai/pipelines/cv/extraction_pipeline.py
- app/ai/providers/parsing/liteparse_client.py

### C) CV analysis flow (LlamaIndex)

1. Service receives cv_markdown and optional fiche context.
2. analysis_agents_service builds system/user prompts.
3. llm.as_structured_llm(...) is attempted first.
4. If provider rejects tool-based structured output, fallback forces JSON schema output.
5. Pydantic validates and normalizes final payload.

Main files:
- app/ai/service/cv/analysis_agents_service.py
- app/ai/providers/llm/runtime.py

## 4) Where to store each thing

- New LLM provider setup/config/proxy:
  - app/ai/providers/llm/
- New parser SDK clients and parser provider adapters:
  - app/ai/providers/parsing/
- New transformation pipelines (input -> output, no HTTP):
  - app/ai/pipelines/
- New business logic orchestration:
  - app/ai/service/
- New API endpoints:
  - app/ai/router/
- Legacy path support for old imports:
  - keep wrappers in app/ai/*.py and app/llama_index.py

## 5) Rules for future additions

- Do not import SDK clients directly inside routers.
- Do not place provider configuration in routers or domain modules.
- Keep prompts and response normalization in service layer.
- Put reusable external-client code in providers first, then consume from pipelines/services.
- Keep old wrappers until all imports across app/tests have migrated.

## 6) Migration checklist for next steps

- Replace any remaining imports from app.llama_index with app.ai.providers.llm.runtime.
- Replace app.ai.factory imports with app.ai.providers.llm.configuration.
- When all references are migrated, wrappers can be removed safely in a separate cleanup PR.
