# RhFlow Project Structure

## Root

- `README.md`
- `backend/`
- `frontend/`

## Backend

- `backend/alembic.ini`
- `backend/requirements.txt`
- `backend/alembic/`
  - `env.py`
  - `README`
  - `script.py.mako`
  - `versions/`
    - migration files like `18f8ff1385b8_create_users_table.py`, `575973217fd0_create_users_table.py`, etc.
- `backend/app/`
  - `__init__.py`
  - `config.py`
  - `database.py`
  - `main.py`
  - `seed.py`
  - `core/`
    - `__init__.py`
    - `dependencies.py`
    - `exceptions.py`
    - `logging.py`
    - `rbac.py`
    - `security.py`
  - `domains/`
    - `__init__.py`
    - `auth/`
      - `__init__.py`
    - `directions/`
      - `__init__.py`
    - `fiches_de_poste/`
      - `__init__.py`
    - `ia/`
      - `__init__.py`
    - `recrutement/`
      - `__init__.py`
    - `users/`
      - `__init__.py`
  - `models/`
    - `__init__.py`
    - `base.py`
    - `user.py`
  - `routers/`
    - `auth.py`

## Frontend

- `frontend/AGENTS.md`
- `frontend/CLAUDE.md`
- `frontend/eslint.config.mjs`
- `frontend/next-env.d.ts`
- `frontend/next.config.ts`
- `frontend/package.json`
- `frontend/postcss.config.mjs`
- `frontend/README.md`
- `frontend/tsconfig.json`
- `frontend/app/`
  - `globals.css`
  - `layout.tsx`
  - `page.tsx`
- `frontend/public/`
