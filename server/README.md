# server

FastAPI app that wraps the LangGraph research assistant (`research_assistant/graph.py`) with
auth, persistence, and an async job API for running research. All commands below assume the repo
root as the working directory (so `load_dotenv()` and Alembic can find `.env` / `alembic.ini`).

## Prerequisites

- `.venv` created and the project installed editable (`pip install -e . --no-deps`), per the
  root `CLAUDE.md`.
- `.env` at the repo root with: `API_KEY`, `TAVILY_API_KEY`, `DATABASE_URL`, `POSTGRES_USER`,
  `POSTGRES_PASSWORD`, `POSTGRES_DB` (optional `LANGSMITH_*` for tracing).
- Postgres running and reachable at `DATABASE_URL` — the repo's `docker-compose.yml` provides one.

## Useful commands

### Start Postgres

```
docker compose up -d
```

Starts Postgres 16 on `localhost:5433` (mapped from container port 5432), using
`POSTGRES_USER`/`POSTGRES_PASSWORD`/`POSTGRES_DB` from `.env`.

### Apply database migrations

```
.venv/Scripts/python.exe -m alembic upgrade head
```

Other useful Alembic commands:

```
.venv/Scripts/python.exe -m alembic current              # show applied revision
.venv/Scripts/python.exe -m alembic history               # list all revisions
.venv/Scripts/python.exe -m alembic downgrade -1           # roll back one revision
.venv/Scripts/python.exe -m alembic revision --autogenerate -m "message"  # new migration from model diff
```

### Start the API server

```
.venv/Scripts/python.exe -m uvicorn server.main:app --reload
```

Useful flags:

| Flag | Purpose |
| --- | --- |
| `--reload` | Auto-restart on source changes (dev only). On Windows it also matters for the LangGraph checkpointer: async psycopg can't run on the default `ProactorEventLoop`, and `--reload` makes Uvicorn use a `SelectorEventLoop`. Without it, startup fails on Windows. Docker (Linux) is unaffected. |
| `--host 0.0.0.0` | Bind all interfaces instead of just `127.0.0.1` (e.g. to reach it from another machine/container). |
| `--port 8000` | Override the default port `8000`. |
| `--workers N` | Run N worker processes. Not compatible with `--reload`; only use for production-style runs. |
| `--log-level debug` | More verbose Uvicorn/app logging. |

On startup the server also opens the LangGraph Postgres checkpointer and runs its
`setup()`, which creates its own `checkpoint*` tables in the same database. They aren't Alembic
migrations, and `alembic/env.py` excludes them from autogenerate.

Once running, interactive docs are at `http://127.0.0.1:8000/docs` (Swagger UI) and
`http://127.0.0.1:8000/redoc`.

## Endpoints

All requests/responses are JSON. Authenticated endpoints expect `Authorization: Bearer <token>`.

### `GET /health`

Liveness check, no auth. Returns `{"status": "ok"}`.

### `POST /register`

```
curl -X POST http://127.0.0.1:8000/register \
  -H "Content-Type: application/json" \
  -d '{"name": "alice", "password": "hunter22"}'
```

Returns `{"user_id", "name", "token"}` — the token is only ever returned here, store it.

### `POST /login`

```
curl -X POST http://127.0.0.1:8000/login \
  -H "Content-Type: application/json" \
  -d '{"name": "alice", "password": "hunter22"}'
```

Returns a fresh `{"token"}`.

### `GET /agents` — list your agents

```
curl http://127.0.0.1:8000/agents -H "Authorization: Bearer <token>"
```

Returns `[{"id", "name", "user_id", "has_config"}]`. Only agents owned by the caller.

### `POST /agents` — create an agent

```
curl -X POST http://127.0.0.1:8000/agents \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "my-agent"}'
```

Returns `201` with `{"id", "name", "user_id", "has_config": false}`. An agent isn't usable for
research until it also has a config (below).

### `PATCH /agents/{agent_id}` — rename an agent

```
curl -X PATCH http://127.0.0.1:8000/agents/<agent_id> \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "renamed-agent"}'
```

Returns `{"id", "name", "user_id", "has_config"}`. `404` if the agent doesn't exist or isn't yours.

### `POST /agents/{agent_id}/config` — configure an agent

```
curl -X POST http://127.0.0.1:8000/agents/<agent_id>/config \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"api_token": "<anthropic-api-key>", "research_mode": "quick", "retry_max_count": 3, "critique_threshold": 6}'
```

Returns `201` with `{"agent_id", "research_mode", "retry_max_count", "critique_threshold",
"model_family", "model_name", "web_search_enabled"}` (`api_token` is accepted but never echoed
back). `404` if the agent doesn't exist or isn't yours, `409` if it already has a config (one
config per agent).

Web search is opt-in and bring-your-own-key: send `"web_search_enabled": true` together with
`"tavily_api_token": "<tavily-api-key>"` (stored encrypted, never returned). Enabling it without a
key is a `422`. Without it, the agent researches with no web search tool at all, and the server
never falls back to its own `TAVILY_API_KEY`.

### `GET /agents/{agent_id}/config` — read an agent's config

```
curl http://127.0.0.1:8000/agents/<agent_id>/config -H "Authorization: Bearer <token>"
```

Returns `{"agent_id", "research_mode", "retry_max_count", "critique_threshold", "model_family",
"model_name", "web_search_enabled"}` (`api_token` and `tavily_api_token` are never returned;
`web_search_enabled: true` means a Tavily key is stored). `404` if the agent doesn't exist, isn't yours, or
has no config yet.

### `PATCH /agents/{agent_id}/config` — update an agent's config

```
curl -X PATCH http://127.0.0.1:8000/agents/<agent_id>/config \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"research_mode": "thorough", "retry_max_count": 5, "critique_threshold": 7}'
```

Updates `research_mode`, `retry_max_count`, and `critique_threshold`. `api_token` is optional here
— omit or leave it blank to keep the existing token, or include it to rotate it. `404` if the
agent doesn't exist, isn't yours, or has no config yet.

`web_search_enabled` defaults to `false` here, so send it on every update. With it `true`,
`tavily_api_token` follows the same keep-if-blank rule (but is required, `422`, if no key is
stored yet). With it `false`, the stored Tavily key is deleted.

### `POST /research` — start a research run

Research runs in the background (it can take a while), so this returns immediately with a job id
instead of the result. `agent_id` must reference one of your own, configured agents:

```
curl -X POST http://127.0.0.1:8000/research \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"topic": "quantum computing", "agent_id": "<agent_id>"}'
```

Returns `202` with `{"id", "status": "pending"}`.

### `GET /research` — list your research runs

```
curl http://127.0.0.1:8000/research -H "Authorization: Bearer <token>"
```

Returns `[{"id", "topic", "status", "research", "error_message", "created_at", "agent_name"}]`,
newest first.

### `GET /research/{id}` — poll a single run

```
curl http://127.0.0.1:8000/research/<id> \
  -H "Authorization: Bearer <token>"
```

Returns `{"id", "topic", "status", "research", "error_message", "created_at", "agent_name"}`.
`status` moves `pending` → `running` → `awaiting_review` (see below) → `running` → … →
`completed`, or to `failed` at any point. Complex topics that get split into subtopics skip review
and go straight from `running` to `completed`. `research` holds the draft awaiting review while
`awaiting_review`, and the final result once `completed`. `error_message` is `null` unless
`failed`. 404s if the id doesn't exist or belongs to another user.

### `POST /research/{id}/review` — approve or send back a draft

When a run reaches `awaiting_review`, the graph is paused (its state is checkpointed in Postgres,
so this survives a server restart) until you decide on the draft shown in `research`:

```
curl -X POST http://127.0.0.1:8000/research/<id>/review \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"approved": true}'

curl -X POST http://127.0.0.1:8000/research/<id>/review \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"approved": false, "feedback": "Add concrete numbers for 2025"}'
```

Returns `202` with `{"id", "status": "running"}` and resumes the run in the background. Approving
makes that exact draft the final result (`completed`). Sending it back revises the draft using
your feedback, and the run returns to `awaiting_review` with the new draft. `422` if `approved` is
`false` without a non-blank `feedback`. `404` if the research doesn't exist or isn't yours. `409`
if it isn't `awaiting_review`, including the second of two quick submits.

Deleting a research (`DELETE /research/{id}`) also deletes its checkpointed graph state.
