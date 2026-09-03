# Implementation: user registration and basic auth

## Approach

Add an `auth_tokens` table (one row per issued token, FK to `users`). `POST /register`
creates a `User` row, generates a high-entropy random token (`secrets.token_urlsafe`),
stores only its SHA-256 hash, and returns the plaintext token once. `POST /research`
gains a FastAPI dependency (`get_current_user`) that reads `Authorization: Bearer <token>`,
hashes it, looks up the matching `auth_tokens` row, and returns the owning `User` — raising
401 if the header is missing/malformed or the hash isn't found.

## Alternatives Considered

- **Password + login endpoint** — rejected: Non-Goals explicitly scope this down to an
  identity token, no credentials to manage/hash-with-a-slow-KDF/reset.
- **ASGI middleware guarding all routes by default** — rejected: it has to special-case
  `/register` and `/health` as exempt, which is an easy place to accidentally exempt a
  future sensitive route too. A per-route `Depends(get_current_user)` is opt-in and fails
  closed only where actually applied — matches how `get_agent_service` already wires deps.
- **Plaintext tokens in the DB** — rejected: matches AC-6; a DB leak would otherwise hand
  out live, directly-usable API tokens with zero extra work.
- **bcrypt/argon2 for the token hash** — rejected in favor of plain SHA-256: those KDFs
  exist to slow down brute-forcing a low-entropy human password. This token is already
  `secrets.token_urlsafe(32)` (256 bits of randomness) chosen by the server, so a fast
  hash is fine and lets lookup stay a simple indexed `WHERE token_hash = ?` — an attacker
  with the hash still has to invert 256 bits, not guess a dictionary word.

## State changes (`research_assistant/state.py`)

None — this feature is entirely in `src/server/`, doesn't touch the LangGraph state/graph.

## Graph changes (`research_assistant/graph.py`, `nodes.py`)

None.

## LLM / tools changes (`llm/model.py`, `llm/tools.py`)

None.

## Server / API changes (`src/server/`)

- New table `AuthToken` in `db/base.py`: `id` (uuid pk), `token_hash` (String(64), unique,
  not null, indexed), `user_id` (FK `users.id`, not null), `created_at` (server default
  now). `User` gets `tokens: Mapped[List["AuthToken"]] = relationship(back_populates="user")`.
- New Alembic migration (`revises` the existing `f3a1c9d2e8b4` head) creating `auth_tokens`
  with a unique index on `token_hash` and FK to `users.id`, with a matching `downgrade()`.
- New `server/auth.py`: `generate_token() -> str` (`secrets.token_urlsafe(32)`),
  `hash_token(token: str) -> str` (`hashlib.sha256(token.encode()).hexdigest()`).
- New `server/models/auth_models.py`: `RegisterRequest {name: str}` (min_length=1,
  max_length=50 — reuses the same bound as `User.name`'s column), `RegisterResponse
  {user_id: UUID, name: str, token: str}`.
- `server/dependencies.py`: new `get_current_user(authorization: Annotated[str | None,
  Header()] = None, session: Annotated[AsyncSession, Depends(get_db_session)]) -> User`.
  Parses the `Bearer ` prefix, 401s (with `WWW-Authenticate: Bearer` header) if absent/
  malformed, hashes the token, queries `AuthToken` joined to `User` by `token_hash`, 401s
  on no match, else returns the `User`.
- `server/main.py`:
  - `POST /register` — takes `RegisterRequest`, creates `User` then `AuthToken` (via
    `DBService`, using the request's `AsyncSession` directly since it's a two-step
    create where the second step needs the first's generated id), returns `201` +
    `RegisterResponse`. Plaintext token exists only in memory long enough to hash it and
    put it in the response — never assigned to a field that gets persisted or logged.
  - `POST /research` — add `user: Annotated[User, Depends(get_current_user)]` param. Not
    otherwise used yet (no per-user research history table exists) — its presence is what
    enforces AC-3/4/5; wiring research results to a user is future scope.

## Affected files

- `src/server/db/base.py` — add `AuthToken` model + `User.tokens` relationship.
- `alembic/versions/<new>_create_auth_tokens.py` — new migration.
- `src/server/auth.py` — new file, token generation/hashing helpers.
- `src/server/models/auth_models.py` — new file, register request/response models.
- `src/server/dependencies.py` — add `get_current_user`.
- `src/server/main.py` — add `POST /register`, protect `POST /research`.

## Risks / Landmines

- `server/db/session.py` reads `os.environ["DATABASE_URL"]` at import time — fine today
  since `server/main.py` and `alembic/env.py` both call `load_dotenv()` before importing
  anything that pulls in `server.db.session`; don't reorder those imports.
- Existing `AgentConfig` pydantic model (`server/models/agent_models.py`) already has an
  unrelated field called `token` (an LLM-provider API token per agent-config) — don't
  confuse it with the new auth token; different table, different purpose, kept separate.
- `tokens.txt` — not read from or written to; unrelated to this feature.
- Verifying this end-to-end requires a reachable Postgres at `DATABASE_URL` and running
  the Alembic migration — noted in the verification log below if that wasn't available in
  this environment.

## Tasks

- [x] T1 — Add `AuthToken` model + `User.tokens` relationship in `db/base.py` (AC-1, AC-6)
- [x] T2 — Alembic migration creating `auth_tokens` (AC-1)
- [x] T3 — `server/auth.py`: `generate_token`, `hash_token` (AC-1, AC-6)
- [x] T4 — `server/models/auth_models.py`: `RegisterRequest`/`RegisterResponse` (AC-1, AC-2)
- [x] T5 — `POST /register` route in `main.py` (AC-1, AC-2, AC-6, AC-7)
- [x] T6 — `get_current_user` dependency in `dependencies.py` (AC-3, AC-4, AC-5)
- [x] T7 — Protect `POST /research` with `Depends(get_current_user)` (AC-3, AC-4, AC-5)

Reviewing and testing against requirements.md's acceptance criteria (including applying
the Alembic migration, which wasn't run here) is the user's part — not verified by the
agent.
