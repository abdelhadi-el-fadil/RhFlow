# RH Flow v2 — Backend Rules

FastAPI + SQLAlchemy 2.0 + Alembic + PostgreSQL + JWT auth. Frontend is Next.js (see `frontend/CLAUDE.md`).

## Architecture — domain-driven

```
app/
  core/        # shared, domain-agnostic: codes, enums, exceptions, schemas, security, dependencies, logging
  models/      # base.py only: Base + TimestampMixin + SoftDeleteMixin
  domains/
    <domain>/
      model.py        # SQLAlchemy models
      router.py       # HTTP layer ONLY — no business logic
      service.py      # ALL business logic lives here
      schemas.py      # Pydantic request/response schemas
      exceptions.py   # domain exceptions, codes prefixed: AUTH_*, USERS_*, ...
```

- Routers are thin: parse input → call service → wrap in `ApiResponse`. No queries, no business rules in routers.
- Services never raise `HTTPException` — only `AppException` subclasses from the domain's `exceptions.py`.
- Generic error codes (`NOT_FOUND`, `FORBIDDEN`, ...) live in `core/codes.py`; domain-specific codes live in the domain, prefixed with the domain name.
- Shared enums (e.g. `UserRole`) live in `core/enums.py` — never redefine them locally.
- Cross-domain imports: a domain may import another domain's `model`/`exceptions`, never its `router`.

## API responses

- Every endpoint returns `ApiResponse[T]` or `PaginatedResponse[T]` from `core/schemas.py`. Only exceptions: `/` and `/health`.
- Error responses are always `{"detail", "code", "status"}` — produced by the global handlers in `main.py`. Never craft error JSON manually.
- Never expose `hashed_password` or any secret in a response schema.

## Schemas (DTOs) & validation

- Every request body and every response goes through a Pydantic schema (DTO) defined in the domain's `schemas.py`. Routers never accept raw `dict`s and never return ORM models directly.
- Validation lives in the schema, not in the service: use Pydantic types and constraints (`EmailStr`, `Field(min_length=..., max_length=..., ge=...)`, enums from `core/enums.py`). Custom rules go in `@field_validator` methods on the schema.
- Separate input and output DTOs: `XxxCreate` / `XxxUpdate` for requests, `XxxResponse` for responses — never reuse a response schema as input.
- Response schemas that map from ORM models use `model_config = ConfigDict(from_attributes=True)`.
- Invalid input is handled by the global `RequestValidationError` handler in `main.py` (422 with `VALIDATION_ERROR` code) — never catch or re-raise validation errors manually.

## Database

- Schema changes go through Alembic ONLY: `python -m alembic revision --autogenerate`, then **manually review** the generated `upgrade()`/`downgrade()` before committing.
- `Base.metadata.create_all()` is FORBIDDEN everywhere, including `seed.py`. The seeder assumes migrations have been applied (`alembic upgrade head` first).
- SQLAlchemy 2.0 style is mandatory: `select(User).where(...)` with `db.scalars()`/`db.execute()` — do not write new `db.query()` code; migrate old usages when touching them.
- Sessions come from `Depends(get_db)` only — never instantiate `SessionLocal` in domain code (seeder excepted).
- New models inherit `Base, TimestampMixin, SoftDeleteMixin` and must be imported in `alembic/env.py` for autogenerate to see them.

## Config & secrets

- `app/config.py` `Settings` is the single source of truth: every env var the code reads MUST be a declared field (no `os.getenv` elsewhere, no constants duplicating a setting — e.g. JWT algorithm comes from `settings.ALGORITHM`).
- `extra="ignore"` stays (the shared `.env` also holds Docker-only vars like `POSTGRES_*`).
- `.env` is never committed and never baked into a Docker image (`backend/.dockerignore` must exclude it). Containers receive secrets via compose `environment:`.
- Keep `.env.example` in sync with `Settings` fields.

## Security

- Passwords: only via `hash_password`/`verify_password` from `core/security.py` (bcrypt).
- Auth in routes: `Depends(get_current_user)`; RBAC: `Depends(require_role(UserRole.X))`.
- Login errors stay vague (anti account-enumeration). Never log tokens, passwords, or secrets.

## Engineering principles

- **ACID / transactions:** one request = one transaction. `get_db` commits on success and rolls back on any exception — services NEVER call `db.commit()` or `db.rollback()` themselves (they may `db.flush()` to get generated IDs). Multi-step writes must live in a single request/session so they succeed or fail atomically. Standalone scripts (e.g. seeder) manage their own session with explicit commit/rollback/close.
- **DRY:** one source of truth for everything — enums in `core/enums.py`, generic error codes in `core/codes.py`, response envelopes in `core/schemas.py`, settings in `config.py`, model mixins in `models/base.py`. Before writing a constant, schema, or helper, check whether it already exists in `core/`. Duplicated logic across domains gets extracted to `core/`.
- **SOLID:**
  - Single responsibility — the router/service/schemas/exceptions split per domain IS the rule: HTTP concerns in routers, business rules in services, validation in schemas. A function that does two things gets split.
  - Open/closed — extend by adding new domains/handlers, not by piling conditionals into existing functions (e.g. new roles go in `UserRole` + `require_role`, not `if/elif` chains in routes).
  - Liskov — exceptions subclass `AppException` and stay substitutable (handled uniformly in `main.py`).
  - Interface segregation — keep DTOs minimal: a schema exposes only what its endpoint needs (no god-schemas reused everywhere).
  - Dependency inversion — dependencies are injected via `Depends()` (`get_db`, `get_current_user`, `require_role`), never instantiated inside business logic.
- General practice: small functions, early returns over deep nesting, no dead/commented-out code, no copy-paste programming.

## Typing — strict everywhere

- Every function and method is fully annotated: all parameters AND the return type (including `-> None`). This applies to routers, services, dependencies, helpers, and scripts — no exceptions.
- Boundaries are typed by construction: request/response = Pydantic DTOs, DB rows = `Mapped[...]` models, config = `Settings` fields. A value should never cross a layer as a raw `dict` or `Any`.
- `Any` is forbidden unless there is no alternative, and then it must carry a comment justifying it. No bare collections: `list[UserResponse]`, `dict[str, int]` — never `list`/`dict` alone.
- Optionals are explicit: `str | None` (modern union syntax), and `None` handling is visible at the call site.
- Generic helpers use `TypeVar`/`Generic` (like `ApiResponse[T]`) instead of degrading to `Any`.

## Style

- Everything in English: identifiers, docstrings, comments, log messages. French business names are allowed only as domain/table names (`fiches_de_poste`, `recrutement`).
- Commits: Conventional Commits in English — `feat(auth): add JWT login`, `fix(users): ...`, `refactor:`, `chore:`, `docs:`.
- Keep `structure.md` up to date when adding/removing files.
