# RH Flow v2 — Backlog Stagiaire (v3)

> **Comment travailler avec ce backlog :**
> 1. Lis `backend/CLAUDE.md` AVANT de commencer — c'est la source de vérité des règles. Chaque ticket ci-dessous te dit **Quoi** faire, **Pourquoi**, et **Comment** ; en cas de conflit, le CLAUDE.md gagne.
> 2. Un ticket = une branche = une PR. Commits au format Conventional Commits anglais (`feat(users): add CRUD endpoints`).
> 3. À partir du TICKET-021, un ticket n'est **Done** que si `python -m pytest` est vert. « Testé sur Swagger » ne suffit plus.
> 4. Les tickets `encadrant-review` : ne passe pas au suivant sans validation.
> 5. Utilise toujours `python -m <module>` (pip, alembic, uvicorn, pytest) — évite les ambiguïtés d'environnement.
>
> **Labels :** `S1`…`S8` = semaine cible · `backend`/`frontend`/`ia` = couche · `good-first-issue` · `encadrant-review`

---

## EPIC 1 — Setup & Socle technique ✅ (terminé — pour mémoire)

| Ticket | Livré |
|---|---|
| **001** ✅ | FastAPI + structure domain-driven (`core/`, `domains/`, `models/`), CORS, logging middleware, exception handlers uniformes, `GET /health`, `Settings` fail-fast |
| **002** ✅ | PostgreSQL + SQLAlchemy 2.0 + Alembic, `get_db()` ACID (commit/rollback par requête), `Base` + `TimestampMixin` + `SoftDeleteMixin` |
| **003** ✅ | Auth JWT : login OAuth2 + `/auth/me`, `require_role()`, exceptions `AUTH_*`/`USERS_*`, migration `users` relue, seeder idempotent (`admin@example.com / Admin123`) |
| **004** ✅ | Docker Compose (postgres pgvector, minio, pgadmin, backend), secrets via `.env` racine unique injectés par compose, `.dockerignore`, `depends_on: service_healthy` |

---

## EPIC 1.5 — Qualité & Garde-fous (À FAIRE EN PREMIER)

### TICKET-026 · Fix : un user supprimé/désactivé ne doit pas pouvoir se connecter
**Labels :** `S3` `backend` `good-first-issue`
**Estimation :** 1h
**Bloqué par :** rien — c'est LE premier ticket

**Quoi :**
Dans `app/domains/auth/service.py`, faire respecter la règle R5 du CLAUDE.md : `login()` et `get_current_user_from_token()` doivent exclure les utilisateurs `is_deleted == True` et refuser les `enabled == False`.

**Pourquoi :**
Notre audit a montré que `select(User).where(User.email == email)` et `db.get(User, id)` ne filtrent rien. Aujourd'hui inexploitable (pas encore de endpoint DELETE), mais dès le TICKET-023 un admin pourra "supprimer" un user… qui pourra toujours se connecter, car le soft delete laisse la ligne en base. C'est le piège classique du soft delete : la suppression n'est qu'un booléen, chaque lecture doit le respecter.

**Comment :**
1. Dans `login()` : ajouter `.where(User.is_deleted == False)` au select ; après avoir trouvé le user, si `not user.enabled` → lever `InvalidCredentialsException()` (même message vague — on ne révèle pas pourquoi le compte échoue, anti-énumération).
2. Dans `get_current_user_from_token()` : remplacer `db.get(User, ...)` par un `select` filtrant `is_deleted == False` ; si `not user.enabled` → `InvalidTokenException()`.
3. Vérifier au boot + login Swagger que rien n'est cassé.

**Références :**
- Soft delete pattern : relire la section Database de `backend/CLAUDE.md`
- SQLAlchemy 2.0 `select()` : https://docs.sqlalchemy.org/en/20/orm/queryguide/select.html

**Définition of Done :**
Un user passé à `enabled=False` directement en base (via pgAdmin) reçoit 401 au login et 401 sur `/auth/me` avec un token déjà émis.

---

### TICKET-021 · Socle de tests pytest + couverture auth
**Labels :** `S3` `backend` `encadrant-review` `good-first-issue`
**Estimation :** 4h
**Bloqué par :** TICKET-026

**Quoi :**
Mettre en place l'infrastructure de test (`tests/conftest.py`) et écrire ~10 tests couvrant tout le domaine auth.

**Pourquoi :**
C'est le filet de sécurité de TOUS les tickets suivants. Sans tests, chaque module que tu ajouteras pourra casser l'auth sans que personne ne le voie. Avec eux, `python -m pytest` te dit en 2 secondes si tu as cassé quelque chose. Les tests sont aussi une spécification exécutable : `test_login_wrong_password_returns_401` documente le comportement mieux qu'un commentaire — et ne peut pas mentir.

**Comment :**
1. `python -m pip install pytest httpx` + ajouter au `requirements.txt`.
2. Créer `backend/tests/__init__.py` et `backend/tests/conftest.py` :
   - un engine SQLite **in-memory** (`create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)`) — les tests tournent sans Postgres ni Docker ;
   - `Base.metadata.create_all(engine)` — c'est l'UNIQUE endroit où `create_all` est autorisé (voir CLAUDE.md) ;
   - override de la dépendance : `app.dependency_overrides[get_db] = override_get_db` — c'est le mécanisme FastAPI clé : tout le code reçoit sa session via `Depends(get_db)`, donc on échange la DB sans toucher au code métier (c'est la *dependency inversion* de la section SOLID qui paie) ;
   - fixtures : `client` (TestClient), `db` (session), `make_user(email, password, role, enabled=True, is_deleted=False)` (factory).
3. Créer `tests/test_auth.py` :
   - login OK → 200, `data.access_token` présent
   - mauvais mot de passe → 401 + code `AUTH_INVALID_CREDENTIALS`
   - email inconnu → 401 + **même code** (anti-énumération vérifiée)
   - `GET /auth/me` avec token → 200, email correct, `hashed_password` ABSENT de la réponse
   - `/auth/me` sans token → 401
   - token expiré (générer avec `expires_delta=timedelta(seconds=-1)`) → 401 + `AUTH_TOKEN_EXPIRED`
   - token signé avec une autre clé → 401 + `AUTH_INVALID_TOKEN`
   - user `is_deleted=True` → login 401 (prouve TICKET-026)
   - user `enabled=False` → login 401 (idem)
   - `require_role` : mauvais rôle → 403 + `FORBIDDEN`

**Références (lecture ~1h avant de coder) :**
- FastAPI testing : https://fastapi.tiangolo.com/tutorial/testing/
- Override de dépendances : https://fastapi.tiangolo.com/advanced/testing-dependencies/
- pytest fixtures : https://docs.pytest.org/en/stable/how-to/fixtures.html

**Définition of Done :**
`python -m pytest` → 10+ tests verts, Postgres/Docker éteints.

---

### TICKET-022 · Tooling : ruff + mypy + CI GitHub Actions
**Labels :** `S3` `backend`
**Estimation :** 3h
**Bloqué par :** TICKET-021

**Quoi :**
Linter (ruff), type-checker (mypy) et CI qui exécute lint + types + tests à chaque push.

**Pourquoi :**
Le CLAUDE.md impose le typage strict et un style propre — mais une règle que personne ne vérifie automatiquement finit toujours violée. Après ce ticket, un commit qui viole les règles fait échouer la CI : les règles se défendent toutes seules. C'est aussi ce qui distingue un projet d'étudiant d'un projet professionnel.

**Comment :**
1. `pyproject.toml` à la racine de `backend/` : sections `[tool.ruff]` (line-length, règles `E,F,I,UP`) et `[tool.mypy]` (`strict = true` sur `app/` ; commence souple si trop d'erreurs : active `disallow_untyped_defs` d'abord).
2. `python -m ruff check app/ tests/` puis `python -m mypy app/` — corrige ce qui sort (il y aura des surprises, c'est normal).
3. `.github/workflows/ci.yml` : job unique Python 3.11 → install deps → ruff → mypy → pytest.
4. Nettoyer `requirements.txt` : garde uniquement les dépendances DIRECTES (fastapi, uvicorn, sqlalchemy, alembic, psycopg2-binary, pydantic-settings, pyjwt, passlib[bcrypt], python-multipart, minio, pytest, httpx, ruff, mypy). Supprime `pip`, `setuptools`, `argon2-cffi`, `pwdlib`, `ecdsa`, `rsa`, `six`… (un freeze complet rend les upgrades illisibles).

**Références :**
- ruff : https://docs.astral.sh/ruff/
- mypy : https://mypy.readthedocs.io/en/stable/getting_started.html
- GitHub Actions Python : https://docs.github.com/en/actions/automating-builds-and-tests/building-and-testing-python

**Définition of Done :**
CI verte sur un push. Une fonction sans annotation de retour fait échouer la CI.

---

## EPIC 2 — Modules RH Core

### TICKET-023 · CRUD Users
**Labels :** `S3` `backend` `encadrant-review`
**Estimation :** 4h
**Bloqué par :** TICKET-021

**Quoi :**
Gestion des comptes par l'ADMIN : `GET /users` (paginé), `POST`, `PUT`, `DELETE` (soft). DTOs `UserCreate`/`UserUpdate` avec vraie validation.

**Pourquoi :**
C'est le premier vrai CRUD — il devient le **gabarit** de tous les modules suivants (directions, fiches…). Tout ce que tu apprends ici (DTO in/out séparés, pagination, soft delete, exceptions domaine, tests) se réutilise à l'identique. C'est aussi lui qui rend le TICKET-026 réellement utile : sans DELETE, le soft delete n'était que théorique.

**Comment :**
1. `domains/users/schemas.py` : `UserCreate` (`email: EmailStr`, `password: str = Field(min_length=8)`, `full_name`, `gsm`, `role: UserRole`) ; `UserUpdate` (tous champs optionnels — `str | None = None`) ; `UserResponse` existe déjà. Règle CLAUDE.md : la validation vit dans le schema (contraintes `Field`, `EmailStr`), pas dans le service.
2. `domains/users/exceptions.py` : `EmailAlreadyExistsException` (409, `USERS_EMAIL_ALREADY_EXISTS`), `UserDisabledException` (403, `USERS_DISABLED`).
3. `domains/users/service.py` (fonctions, pas de classe) : `create_user`, `get_user`, `list_users(params: PaginationParams)`, `update_user`, `soft_delete_user`. TOUTES les lectures filtrent `is_deleted == False` (règle R5). `soft_delete_user` : `is_deleted=True` + `deleted_at=now()` — jamais `db.delete()`.
4. `domains/users/router.py` : les 4 endpoints, tous derrière `require_role(UserRole.ADMIN)` sauf `GET /users` (ADMIN + DRH). `GET /users` retourne `PaginatedResponse[UserResponse]` — premier consommateur réel de `PaginationParams` (`?page=1&page_size=20`).
5. Enregistrer le router dans `main.py`.
6. `tests/test_users.py` — **scénarios exigés** :
   - **Happy paths** : POST crée (201/200, `data.id` présent, pas de `hashed_password`) ; GET liste paginée ; PUT modifie ; DELETE → `ApiResponse[None]`
   - **Validation (422 Pydantic)** : email invalide ; password < 8 caractères ; rôle inexistant
   - **Conflits (409)** : POST avec email existant → `USERS_EMAIL_ALREADY_EXISTS` ; PUT qui change l'email vers un email déjà pris → idem
   - **404** : PUT et DELETE sur id inexistant → `USERS_NOT_FOUND`
   - **RBAC (403)** : DRH sur POST/PUT/DELETE ; DIRECTEUR sur GET /users
   - **Pagination** : 25 users → `page_size=10` donne `total_pages=3`, page 3 contient 5 éléments
   - **Soft delete** : user supprimé absent de GET /users ; login refusé ; re-DELETE du même user → 404 (déjà invisible)

**Références :**
- Validation Pydantic (Field, EmailStr) : https://docs.pydantic.dev/latest/concepts/fields/
- FastAPI response_model : https://fastapi.tiangolo.com/tutorial/response-model/

**Définition of Done :**
pytest vert. Un DRH ne peut pas créer de user (403 uniforme). Un user supprimé disparaît des listes ET ne peut plus se connecter.

---

### TICKET-024 · AuditMixin
**Labels :** `S3` `backend` `good-first-issue`
**Estimation :** 1h
**Bloqué par :** TICKET-023

**Quoi :**
Ajouter `AuditMixin` (`created_by_id` / `updated_by_id`, FK nullable vers `users.id`) dans `models/base.py`.

**Pourquoi :**
Règle R6 du CLAUDE.md : dans une app RH, « qui a validé cette fiche ? qui a rejeté ce besoin ? » est une exigence métier, pas un luxe. Le mixin garantit l'uniformité : tous les modèles métier auront l'audit, de la même façon, sans copier-coller (DRY).

**Comment :**
Un mixin avec FK nécessite `declared_attr` (une subtilité SQLAlchemy : la FK doit être créée par classe fille, pas partagée) :
```python
class AuditMixin:
    @declared_attr
    def created_by_id(cls) -> Mapped[int | None]:
        return mapped_column(ForeignKey("users.id"), nullable=True)

    @declared_attr
    def updated_by_id(cls) -> Mapped[int | None]:
        return mapped_column(ForeignKey("users.id"), nullable=True)
```
Pas de migration isolée : les colonnes partiront avec les tables des modules qui l'utilisent (005+). Les services renseigneront ces champs depuis `current_user`.

**Références :**
- Mixins SQLAlchemy / `declared_attr` : https://docs.sqlalchemy.org/en/20/orm/declarative_mixins.html

**Définition of Done :**
Un modèle de test héritant du mixin produit les 2 colonnes + FKs dans une migration autogenerate.

---

### TICKET-005 · Module Directions
**Labels :** `S3` `backend`
**Estimation :** 3h
**Bloqué par :** TICKET-024

**Quoi :**
CRUD des directions organisationnelles (ADMIN). Premier module métier complet : modèle + migration + DTOs + service + router + exceptions + tests.

**Pourquoi :**
Les directions sont le référentiel sur lequel s'appuient les fiches de poste (FK `direction_id`). Module volontairement simple : c'est ta répétition générale du pattern avant les modules à workflow.

**Comment :**
Champs **en anglais** (règle CLAUDE.md — seuls tables/routes gardent le vocabulaire métier) :
```python
class Direction(Base, TimestampMixin, SoftDeleteMixin, AuditMixin):
    __tablename__ = "directions"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True)  # e.g. "DIR-IT"
    description: Mapped[str | None]
    director_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
```
1. Modèle ci-dessus + import dans `alembic/env.py` + `python -m alembic revision --autogenerate` + **relire la migration** (vérifie les FKs et le `server_default` des booléens du mixin) + `upgrade head`.
2. `schemas.py` : `DirectionCreate`, `DirectionUpdate`, `DirectionResponse`.
3. `exceptions.py` : `DIRECTIONS_NOT_FOUND` (404), `DIRECTIONS_CODE_ALREADY_EXISTS` (409).
4. `service.py` : fonctions CRUD, filtre `is_deleted`, audit renseigné depuis `current_user`.
5. `router.py` : `GET` (tous rôles authentifiés, paginé) / `POST` / `PUT` / `DELETE` soft (ADMIN).
6. `tests/test_directions.py` — **scénarios exigés** :
   - Happy paths : CRUD complet, audit renseigné (`created_by_id` = l'admin qui a créé)
   - 409 : code dupliqué (`DIRECTIONS_CODE_ALREADY_EXISTS`), à la création ET à la modification
   - 404 : GET/PUT/DELETE sur id inexistant ou soft-deleted (`DIRECTIONS_NOT_FOUND`)
   - 403 : DIRECTEUR/DRH/DG sur POST, PUT, DELETE
   - 401 : GET /directions sans token
   - Soft delete : direction supprimée invisible en liste et en GET /{id}

**Définition of Done :**
pytest vert sur tous les scénarios ci-dessus.

---

### TICKET-006 · Module Fiches de Poste
**Labels :** `S3` `backend` `encadrant-review`
**Estimation :** 5h
**Bloqué par :** TICKET-005

**Quoi :**
CRUD des fiches de poste + premier **workflow de statuts** (DRAFT → VALIDATED → ARCHIVED) avec règles de rôle par transition.

**Pourquoi :**
Le workflow d'états est LE pattern central de l'app (besoins et offres l'utilisent aussi). Tu apprends ici : machine à états dans le service, enum de domaine, erreur 409 pour transition invalide, permission par propriétaire (`created_by_id`).

**Comment :**
1. `domains/fiches_de_poste/enums.py` : `FicheStatus(str, Enum)` — DRAFT, VALIDATED, ARCHIVED. L'enum vit dans le DOMAINE, pas dans `core/enums.py` (règle R3 : core = transverse uniquement).
2. Modèle (champs anglais) : `title`, `description`, `missions`, `required_skills`, `experience_level`, `status` (default + `server_default`), `direction_id` (FK), `validated_by_id` (FK nullable) + les 3 mixins. Migration relue.
3. La logique de transition vit dans le **service** :
   - `validate_fiche()` : seulement si `status == DRAFT`, sinon lever une exception 409 `FICHES_INVALID_TRANSITION` (règle R2 : 409 = état incompatible ; 422 reste réservé à Pydantic). Renseigne `validated_by_id`.
   - `archive_fiche()` : seulement depuis VALIDATED.
   - `update_fiche()` : seulement par le créateur (`created_by_id == current_user.id`) et seulement en DRAFT — sinon 403.
4. Endpoints : `GET` (filtres `?status=&direction_id=`, paginé), `POST` (DIRECTEUR/DRH), `GET /{id}`, `PUT /{id}`, `PATCH /{id}/valider` (DRH), `PATCH /{id}/archiver` (DRH/ADMIN).
5. `tests/test_fiches.py` — **scénarios exigés** :
   - Workflow nominal : DIRECTEUR crée (status DRAFT) → DRH valide (VALIDATED, `validated_by_id` renseigné) → ADMIN archive (ARCHIVED)
   - **Matrice des transitions interdites (chacune → 409 `FICHES_INVALID_TRANSITION`)** : valider une VALIDATED, valider une ARCHIVED, archiver une DRAFT
   - RBAC transitions (403) : DIRECTEUR tente de valider ; DIRECTEUR tente d'archiver
   - Propriété : PUT par un autre user que le créateur → 403 ; PUT sur une fiche VALIDATED (même par le créateur) → 409
   - Filtres : `?status=VALIDATED` ne retourne que les validées ; `?direction_id=X` filtre correctement ; combinaison des deux
   - 404 : fiche inexistante ; FK invalide : POST avec `direction_id` inexistant → 404 `DIRECTIONS_NOT_FOUND`

**Références :**
- Pourquoi 409 et pas 422 : https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/409
- Enums Python : https://docs.python.org/3/library/enum.html

**Définition of Done :**
pytest vert : DIRECTEUR crée (DRAFT) → DRH valide → DIRECTEUR tente de valider → 403 ; re-valider une fiche VALIDATED → 409 `FICHES_INVALID_TRANSITION`.

---

### TICKET-007 · Module Besoins en Recrutement
**Labels :** `S4` `backend` `encadrant-review`
**Estimation :** 5h
**Bloqué par :** TICKET-006

**Quoi :**
Besoins en recrutement avec lifecycle DRAFT → SUBMITTED → APPROVED/REJECTED.

**Pourquoi :**
Deuxième workflow — tu consolides le pattern du 006 avec deux nouveautés : une transition avec donnée obligatoire (le rejet exige un motif) et la traçabilité de qui a soumis/traité.

**Comment :**
1. `domains/recrutement/enums.py` : `BesoinStatus` (DRAFT, SUBMITTED, APPROVED, REJECTED).
2. Modèle (anglais) : `title`, `description`, `positions_count`, `desired_date`, `justification`, `status`, `rejection_reason: Mapped[str | None]`, FKs `fiche_de_poste_id`, `submitted_by_id`, `processed_by_id` + mixins. Migration relue.
3. Transitions (service) : `submit` (DIRECTEUR, DRAFT→SUBMITTED), `approve` (DRH, SUBMITTED→APPROVED), `reject` (DRH, SUBMITTED→REJECTED, motif obligatoire **validé par le DTO** `RejectBesoinRequest(reason: str = Field(min_length=10))` — la validation vit dans le schema). Transition invalide → 409 `RECRUTEMENT_INVALID_TRANSITION`.
4. Endpoints : CRUD + `POST /besoins/{id}/soumettre|approuver|rejeter`.
5. `tests/test_besoins.py` — **scénarios exigés** :
   - Workflow nominal : DIRECTEUR crée → soumet (SUBMITTED, `submitted_by_id`) → DRH approuve (APPROVED, `processed_by_id`) ; variante rejet avec motif (REJECTED + `rejection_reason` stocké)
   - **Matrice transitions interdites (409 `RECRUTEMENT_INVALID_TRANSITION`)** : DRAFT→APPROVED direct, approuver un APPROVED, rejeter un DRAFT, soumettre un SUBMITTED, toute transition depuis REJECTED
   - **409 vs 422 — les deux côte à côte** : rejet sans motif → 422 (Pydantic) ; rejet d'un besoin DRAFT avec motif valide → 409 (état). Comprendre cette paire = comprendre la règle R2
   - RBAC (403) : DRH tente de soumettre ; DIRECTEUR tente d'approuver/rejeter
   - 404 : besoin inexistant ; POST avec `fiche_de_poste_id` inexistant

**Définition of Done :**
pytest vert sur tous les scénarios ci-dessus.

---

### TICKET-008 · Module Projets de Recrutement
**Labels :** `S4` `backend`
**Estimation :** 3h
**Bloqué par :** TICKET-007

**Quoi :**
Regrouper des besoins APPROVED en projets de recrutement.

**Pourquoi :**
Première **relation entre agrégats** : un projet référence des besoins, avec une règle métier au rattachement (seuls les besoins approuvés sont éligibles).

**Comment :**
1. Modèle `ProjetRecrutement` (anglais) : `title`, `description`, `start_date`, `expected_end_date`, `status: ProjetStatus`, `manager_id` + Timestamp/Audit.
2. Lien : ajouter `projet_id: Mapped[int | None] = mapped_column(ForeignKey("projets_recrutement.id"))` sur `BesoinRecrutement` (1 besoin = 1 projet max — le plus simple). Migration relue (elle modifie une table existante : vérifie le `op.add_column`).
3. `attach_besoin(projet_id, besoin_id)` dans le service : refuse si `besoin.status != APPROVED` → 409 `RECRUTEMENT_BESOIN_NOT_APPROVED`.
4. Endpoints : `POST /projets` (DRH), `POST /projets/{id}/besoins/{besoin_id}`, `GET /projets/{id}` (détail avec besoins).
5. `tests/test_projets.py` — **scénarios exigés** :
   - Happy path : créer un projet, rattacher un besoin APPROVED, le voir dans `GET /projets/{id}`
   - 409 `RECRUTEMENT_BESOIN_NOT_APPROVED` : rattacher un besoin DRAFT, SUBMITTED et REJECTED (les 3)
   - Besoin déjà rattaché à un autre projet → 409 (décide du code avec l'encadrant, ex: `RECRUTEMENT_BESOIN_ALREADY_ATTACHED`)
   - 404 : projet ou besoin inexistant
   - 403 : DIRECTEUR tente de créer un projet ou de rattacher

**Définition of Done :**
pytest vert sur tous les scénarios ci-dessus.

---

### TICKET-009 · Module Offres d'Emploi
**Labels :** `S4` `backend`
**Estimation :** 3h
**Bloqué par :** TICKET-008

**Quoi :**
Offres publiées depuis les besoins approuvés — avec un endpoint **public**.

**Pourquoi :**
Premier endpoint sans authentification : tu appliques la règle R4 (DTO public dédié). C'est un réflexe de sécurité fondamental : ce qu'on expose à un anonyme se décide explicitement, champ par champ.

**Comment :**
1. Modèle `Offre` (anglais) : `title`, `description`, `requirements`, `published_at: Mapped[datetime | None]`, `deadline`, `status: OffreStatus` (DRAFT, PUBLISHED, CLOSED), FKs `besoin_id`, `published_by_id` + mixins. Migration relue.
2. **Deux DTOs de réponse** : `OffreResponse` (interne, complet) et `OffrePublicResponse` (`title`, `description`, `requirements`, `published_at`, `deadline` — RIEN d'autre : pas de FKs, pas d'audit).
3. `GET /offres` → public, ne liste QUE les `status == PUBLISHED` (+ filtre soft delete), retourne `PaginatedResponse[OffrePublicResponse]`.
4. `POST /offres` (DRH), `PATCH /offres/{id}/publier` (DRAFT→PUBLISHED, set `published_at`), `PATCH /offres/{id}/cloturer` (PUBLISHED→CLOSED). Transitions invalides → 409.
5. `tests/test_offres.py` — **scénarios exigés** :
   - Cycle nominal : DRH crée (DRAFT) → publie (PUBLISHED, `published_at` non null) → clôture (CLOSED)
   - **Liste publique** : accessible sans token (200) ; ne contient QUE les PUBLISHED (ni DRAFT, ni CLOSED, ni soft-deleted) ; `set(response_keys) == {"title", "description", "requirements", "published_at", "deadline"}` — teste les clés EXACTES, c'est le test de la règle R4
   - Transitions interdites (409) : publier une PUBLISHED, clôturer une DRAFT, publier une CLOSED
   - 403 : DIRECTEUR sur POST/publier/clôturer
   - 404 : offre inexistante ; POST avec `besoin_id` inexistant ou non APPROVED → 409

**Définition of Done :**
pytest vert sur tous les scénarios ci-dessus.

---

## EPIC 3 — IA : Pipeline CV & Matching

### TICKET-010 · Upload et stockage des CV dans MinIO
**Labels :** `S4` `S5` `backend`
**Estimation :** 3h
**Bloqué par :** TICKET-009

**Quoi :**
`POST /candidatures` (public) : upload d'un CV PDF, stocké dans MinIO, candidature en base.

**Pourquoi :**
Premier upload de fichier et premier service externe (MinIO = stockage objet compatible S3, déjà dans ton docker-compose). Tu apprends : multipart/form-data, validation de fichier (type + taille — ne JAMAIS faire confiance à un upload), et l'isolation d'un service externe derrière un module `core/` pour pouvoir le mocker en test.

**Comment :**
1. Ajouter à `Settings` : `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`, `MINIO_BUCKET_CV` (+ sync `.env.example` — règle CLAUDE.md : jamais de `os.getenv` ailleurs que Settings).
2. `app/core/storage.py` : `upload_file(file: BinaryIO, key: str, content_type: str) -> str` et `get_presigned_url(key: str) -> str` — entièrement typés. Tout MinIO passe par là.
3. Modèle `Candidature` (anglais) : `candidate_name`, `candidate_email`, `cv_url`, `cv_key`, `status: CandidatureStatus` (RECEIVED, ...), `matching_score: Mapped[float | None]`, `cv_data: Mapped[dict[str, Any] | None] = mapped_column(JSON)` (typé — jamais `dict` nu), FK `offre_id` + mixins. Migration relue.
4. `POST /candidatures` : `UploadFile` + `offre_id` en form-data. Validations AVANT stockage : content-type `application/pdf` + extension `.pdf` + taille ≤ 5 Mo → sinon erreur uniforme. L'offre doit être PUBLISHED → 409 sinon.
5. `tests/test_candidatures.py` (storage **mocké** via `monkeypatch` — les tests ne touchent jamais le vrai MinIO, règle CLAUDE.md) — **scénarios exigés** :
   - Happy path : upload PDF valide sur offre PUBLISHED → 200, candidature RECEIVED en base, `upload_file` appelé avec le bon bucket/key
   - Validations fichier : content-type non-PDF → erreur uniforme ; extension `.docx` → idem ; fichier > 5 Mo → idem (génère un faux fichier de 6 Mo en mémoire)
   - Offre non éligible : candidature sur offre DRAFT → 409 ; sur offre CLOSED → 409 ; sur offre inexistante → 404
   - Le mock storage qui lève une exception → 500 uniforme (`INTERNAL_ERROR`), pas de candidature orpheline en base (vérifie le rollback — c'est ton test ACID)

**Références :**
- FastAPI UploadFile : https://fastapi.tiangolo.com/tutorial/request-files/
- MinIO Python SDK : https://min.io/docs/minio/linux/developers/python/minio-py.html
- Mocking pytest : https://docs.pytest.org/en/stable/how-to/monkeypatch.html

**Définition of Done :**
pytest vert (storage mocké) + test manuel : upload PDF → fichier visible dans la console MinIO (http://localhost:9001) → ligne en BDD.

---

### TICKET-011 · Parsing de CV avec LlamaParse
**Labels :** `S5` `ia` `encadrant-review`
**Estimation :** 4h
**Bloqué par :** TICKET-010

**Quoi :**
Après upload, parser le PDF via LlamaParse et stocker un JSON structuré (`CVData`) dans `candidature.cv_data`.

**Pourquoi :**
Un CV PDF est illisible pour une machine. LlamaParse le convertit en texte/markdown structuré, qu'on transforme en données exploitables (compétences, expériences…). C'est la matière première du matching (013). Tu découvres aussi l'extraction structurée : forcer un LLM à répondre dans un schema Pydantic.

**Comment :**
1. Compte LlamaCloud (free tier) sur https://cloud.llamaindex.ai → `LLAMA_CLOUD_API_KEY` dans `Settings` + `.env.example` + `.env`.
2. `python -m pip install llama-parse llama-index-core` (+ requirements).
3. DTOs dans `domains/ia/schemas.py` (anglais) : `WorkExperience` (`position`, `company`, `duration_months`, `description`) et `CVData` (`full_name`, `email`, `phone`, `skills: list[str]`, `experiences: list[WorkExperience]`, `education: list[str]`, `languages: list[str]`).
4. `domains/ia/parser.py` : `parse_cv(cv_key: str) -> CVData` — télécharge depuis MinIO (via `core/storage`), parse, extrait.
5. Intégration dans `POST /candidatures` en **non-bloquant** : FastAPI `BackgroundTasks` (le candidat n'attend pas les 10-30 s du parsing ; la candidature est créée en RECEIVED, le parsing met à jour `cv_data` ensuite).
6. Tests avec le parser mocké (retourne un `CVData` fixe).

**Références (lecture ~1h) :**
- LlamaParse : https://developers.llamaindex.ai/llamaparse/
- BackgroundTasks : https://fastapi.tiangolo.com/tutorial/background-tasks/

**Définition of Done :**
Upload d'un vrai CV → `candidature.cv_data` contient le JSON structuré avec les vraies données. pytest vert (parser mocké).

---

### TICKET-012 · Indexation des CV dans un VectorStoreIndex (pgvector)
**Labels :** `S5` `S6` `ia`
**Estimation :** 3h
**Bloqué par :** TICKET-011

**Quoi :**
Indexer chaque CV parsé comme vecteur dans PostgreSQL (extension pgvector) via LlamaIndex.

**Pourquoi :**
Le matching sémantique (013) doit retrouver les CV *proches du sens* d'une offre, pas juste des mots-clés identiques. Pour ça on transforme chaque CV en **embedding** (vecteur numérique qui capture le sens du texte) et on les stocke dans pgvector — c'est l'infrastructure du RAG (Retrieval-Augmented Generation). Lis la référence RAG avant de coder : 30 min qui rendent tout le reste limpide.

**Comment :**
1. Migration Alembic avec `op.execute("CREATE EXTENSION IF NOT EXISTS vector")` — même l'extension passe par une migration (règle Alembic-only), pas par psql à la main. (L'image `pgvector/pg16` du compose la fournit, il suffit de l'activer.)
2. `python -m pip install llama-index-vector-stores-postgres`.
3. `domains/ia/index.py` : initialiser `PGVectorStore` (connexion depuis `settings.DATABASE_URL`) + `VectorStoreIndex`.
4. Après parsing (dans la background task du 011) : créer un `Document(text=cv_text, metadata={"candidature_id": ..., "full_name": ...})` et `index.insert(doc)`. La métadonnée `candidature_id` est cruciale : c'est elle qui permettra de remonter du vecteur à la candidature.

**Références :**
- Introduction RAG (à lire en premier) : https://developers.llamaindex.ai/python/framework/understanding/rag/
- Concepts LlamaIndex : https://developers.llamaindex.ai/python/framework/getting_started/concepts/

**Définition of Done :**
Après upload de 5 CV, la table `data_llamaindex_*` contient 5 vecteurs (vérifiable dans pgAdmin).

---

### TICKET-013 · Matching sémantique candidat ↔ poste
**Labels :** `S6` `ia` `encadrant-review`
**Estimation :** 5h
**Bloqué par :** TICKET-012

**Quoi :**
`GET /ai/offres/{offre_id}/matching` (DRH) : les meilleurs candidats pour une offre, triés par score.

**Pourquoi :**
C'est la fonctionnalité différenciante du projet — celle de la démo finale. Techniquement : tu interroges l'index vectoriel avec le texte de l'offre, tu récupères les CV les plus proches sémantiquement, et tu exposes ça au format API uniforme.

**Comment :**
1. `domains/ia/tools.py` : `QueryEngineTool` construit sur le `cv_index` (012).
2. `domains/ia/router.py` : `GET /ai/offres/{offre_id}/matching` — récupère l'offre **via le service recrutement** (règle R7 : jamais de `select(Offre)` dans le domaine ia), construit la requête depuis `title + description + requirements`, interroge l'index.
3. DTOs typés : `CandidateMatch` (`candidature_id`, `full_name`, `score: float`, `strengths: str`) et `MatchingResponse` (`offre_id`, `recommendations: list[CandidateMatch]`) — jamais de dict brut (règle Typing).
4. Sauvegarder `matching_score` sur chaque `Candidature` retournée (via le service recrutement).
5. Réponse : `ApiResponse[MatchingResponse]`.

**Références :**
- Query engines & tools : https://developers.llamaindex.ai/python/framework/module_guides/deploying/agents/tools/

**Définition of Done :**
Test avec 10 CV dont 3 pertinents pour l'offre → les 3 en tête, classés par score. pytest sur le endpoint (index mocké).

---

## EPIC 4 — IA : Génération & Agent

### TICKET-014 · FunctionTool : génération d'offre d'emploi
**Labels :** `S7` `ia` `encadrant-review`
**Estimation :** 4h
**Bloqué par :** TICKET-006

**Quoi :**
`POST /ai/offres/generate` (DRH) : générer le texte d'une offre d'emploi depuis une fiche de poste.

**Pourquoi :**
Premier **FunctionTool** : une fonction Python que le LLM peut appeler. Point clé à comprendre : la signature typée + la docstring SONT la spec que le LLM lit pour décider quand/comment appeler l'outil — ta règle de typage strict devient littéralement fonctionnelle ici.

**Comment :**
1. `generate_job_offer(fiche_id: int) -> str` dans `domains/ia/tools.py` : récupère la fiche **via le service** fiches_de_poste (R7), construit un prompt avec title/missions/required_skills, appelle le LLM.
2. Wrapper : `FunctionTool.from_defaults(fn=generate_job_offer)` — note que LlamaIndex lit la signature et la docstring.
3. Endpoint : body `GenerateOfferRequest(fiche_id: int)` → `ApiResponse[GeneratedOfferResponse]`. Fiche inexistante → 404 `FICHES_NOT_FOUND` uniforme.

**Références :**
- FunctionTool : https://developers.llamaindex.ai/python/framework/module_guides/deploying/agents/tools/

**Définition of Done :**
Offre bien rédigée en < 10 s. 404 uniforme sur fiche inexistante. pytest (LLM mocké).

---

### TICKET-015 · FunctionTools utilitaires pour l'agent
**Labels :** `S7` `ia`
**Estimation :** 3h
**Bloqué par :** TICKET-013

**Quoi :**
4 outils de consultation : `get_candidatures_summary(offre_id: int) -> str`, `get_open_offers() -> str`, `get_besoin_status(besoin_id: int) -> str`, `get_recruitment_stats() -> str`.

**Pourquoi :**
Ce sont les « mains » de l'agent du 016 — chaque question métier qu'il devra traiter correspond à un outil. Règle d'architecture à respecter scrupuleusement (R7) : ces tools appellent les **services** des domaines, jamais la DB directement — le domaine `ia` est un consommateur comme un autre, sinon les règles métier (filtre soft-delete inclus) se dupliquent.

**Comment :**
Chaque tool : annotations complètes + docstring claire en anglais (le LLM la lit), appel au service du domaine concerné, retour formaté en texte lisible.

**Définition of Done :**
Chaque tool testé unitairement (pytest, DB de test, données créées via les services).

---

### TICKET-016 · ReActAgent RH conversationnel
**Labels :** `S7` `ia` `encadrant-review`
**Estimation :** 4h
**Bloqué par :** TICKET-014, TICKET-015

**Quoi :**
`POST /ai/chat` : un agent conversationnel qui répond aux questions RH en utilisant les tools (014 + 015 + matching).

**Pourquoi :**
Un agent **ReAct** boucle Raisonnement → Action (appel d'un tool) → Observation jusqu'à pouvoir répondre. C'est le ticket le plus impressionnant en démo — et il ne marche que si tes tools (015) sont bien décrits, d'où l'importance des docstrings.

**Comment :**
1. `domains/ia/agent.py` : `ReActAgent` avec tous les tools ; `system_prompt` en français (c'est du contenu utilisateur, pas du code — l'exception à la règle anglais).
2. `POST /ai/chat` (authentifié) : `ChatRequest(message: str)` → `ApiResponse[ChatResponse]`.
3. Logger chaque appel : question + tools utilisés (jamais le token — règle Security).

**Références :**
- Agents : https://developers.llamaindex.ai/python/framework/use_cases/agents/

**Définition of Done :**
Démo live, 4 questions : « Combien de candidatures cette semaine ? », « Top 3 profils pour l'offre 5 ? », « Génère une offre pour la fiche 2 », « Quels besoins en attente ? » — réponses correctes.

---

### TICKET-025 · Durcissement & finitions infra
**Labels :** `S6` `backend`
**Estimation :** 4h
**Bloqué par :** TICKET-022

**Quoi :**
Rate-limiting login, migration passlib→pwdlib, CORS configurable, Dockerfile durci, frontend dans le compose, README.

**Pourquoi :**
Le « vernis pro » : `/auth/login` sans rate-limit = brute-force possible ; passlib n'est plus maintenu ; un container root est une mauvaise pratique ; et un README de setup en 5 commandes est la première impression du projet.

**Comment :**
1. `slowapi` : limite `5/minute` sur `POST /auth/login` → 429.
2. `pwdlib` remplace passlib — ATTENTION : vérifier que les hashes bcrypt existants restent vérifiables (test : login d'un user seedé avant migration).
3. `Settings.CORS_ORIGINS: list[str]` au lieu du hardcode dans `main.py`.
4. Dockerfile : `USER` non-root, `HEALTHCHECK` sur `/health`, entrypoint qui exécute `alembic upgrade head` avant uvicorn.
5. Service `frontend` dans le compose.
6. README racine : prérequis + 5 commandes pour tout démarrer.

**Références :**
- slowapi : https://slowapi.readthedocs.io/
- pwdlib : https://frankie567.github.io/pwdlib/
- Dockerfile best practices : https://docs.docker.com/build/building/best-practices/

**Définition of Done :**
6e login en 1 min → 429. `docker compose up` migre et démarre tout. pytest vert après migration pwdlib.

---

## EPIC 5 — Frontend Next.js

> Pour tout l'EPIC 5 : lis `frontend/CLAUDE.md` / `AGENTS.md` — la version de Next.js installée a des breaking changes, la doc locale (`node_modules/next/dist/docs/`) fait foi.

### TICKET-017 · Setup Next.js + Auth
**Labels :** `S8` `frontend` — **Estimation :** 4h — **Bloqué par :** TICKET-003

**Quoi/Comment :** `create-next-app` (TS + Tailwind + App Router) ; shadcn/ui ; `lib/api.ts` = wrapper fetch typé qui injecte le JWT et parse l'enveloppe `{data, message}` / erreurs `{detail, code, status}` (un seul endroit qui connaît le format API) ; page `/login` (attention : le login backend attend du **form-data OAuth2** `username`/`password`, pas du JSON) ; middleware redirect si pas de token ; `UserMenu` (nom + rôle + logout).
**DoD :** login avec `admin@example.com / Admin123` → dashboard → déconnexion.

### TICKET-018 · Dashboard + Fiches de Poste
**Labels :** `S8` `frontend` — **Estimation :** 4h — **Bloqué par :** TICKET-017

**Quoi/Comment :** KPIs (offres actives, candidatures du mois, besoins en attente) ; liste fiches + filtres (status, direction) ; création (DIRECTEUR) ; bouton « Valider » affiché seulement si rôle DRH (le rôle est dans le JWT — mais rappel : le frontend ne fait que *masquer*, c'est le backend qui *protège*).
**DoD :** DIRECTEUR voit ses fiches ; DRH peut valider ; rôle affiché dans le header.

### TICKET-019 · Candidatures + Upload CV
**Labels :** `S8` `frontend` — **Estimation :** 3h — **Bloqué par :** TICKET-017

**Quoi/Comment :** `/candidatures` (liste, statut coloré) ; `/candidatures/upload` (drag-and-drop PDF + sélection d'offre, validations front PDF/5 Mo en *miroir* du backend) ; affichage du `cv_data` extrait ; bouton « Voir le matching ».
**DoD :** upload → données structurées affichées.

### TICKET-020 · Interface IA (Matching + Chat)
**Labels :** `S8` `frontend` `ia` `encadrant-review` — **Estimation :** 4h — **Bloqué par :** TICKET-019, TICKET-016

**Quoi/Comment :** `/ai/matching` (sélecteur d'offre → candidats avec barre de score) ; `/ai/chat` (bulles user/assistant, loader, historique de session).
**DoD :** démo complète : upload CV → matching → chat en live.

---

## Ordre d'exécution

| Ordre | # | Titre | Sprint | Couche | Priorité |
|---|---|---|---|---|---|
| — | 001-004 | Socle (FastAPI, DB, Auth, Docker) | S1-S2 | backend | ✅ Done |
| 1 | **026** | Fix login soft-delete/enabled (R5) | S3 | backend | 🔴 critique |
| 2 | **021** | Tests pytest : socle + auth | S3 | backend | 🔴 critique |
| 3 | **022** | ruff + mypy + CI | S3 | backend | 🔴 critique |
| 4 | **023** | CRUD Users | S3 | backend | 🟠 haute |
| 5 | **024** | AuditMixin | S3 | backend | 🟠 haute |
| 6 | 005 | Module Directions | S3 | backend | 🟠 haute |
| 7 | 006 | Module Fiches de Poste | S3 | backend | 🟠 haute |
| 8 | 007 | Module Besoins Recrutement | S4 | backend | 🟠 haute |
| 9 | 008 | Module Projets Recrutement | S4 | backend | 🟡 moyenne |
| 10 | 009 | Module Offres | S4 | backend | 🟠 haute |
| 11 | 010 | Upload CV MinIO | S4/S5 | backend | 🟠 haute |
| 12 | 011 | Parsing CV LlamaParse | S5 | ia | 🟠 haute |
| 13 | 012 | Indexation pgvector | S5/S6 | ia | 🟠 haute |
| 14 | 013 | Matching sémantique | S6 | ia | 🟠 haute |
| 15 | **025** | Durcissement infra | S6 | backend | 🟡 moyenne |
| 16 | 014 | FunctionTool génération offre | S7 | ia | 🟡 moyenne |
| 17 | 015 | FunctionTools utilitaires | S7 | ia | 🟡 moyenne |
| 18 | 016 | ReActAgent RH | S7 | ia | 🟠 haute |
| 19 | 017 | Setup Next.js + Auth | S8 | frontend | 🟠 haute |
| 20 | 018 | Dashboard + Fiches | S8 | frontend | 🟡 moyenne |
| 21 | 019 | Candidatures + Upload | S8 | frontend | 🟡 moyenne |
| 22 | 020 | Interface IA | S8 | frontend | 🟡 moyenne |