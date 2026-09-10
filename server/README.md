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
| `--reload` | Auto-restart on source changes (dev only). |
| `--host 0.0.0.0` | Bind all interfaces instead of just `127.0.0.1` (e.g. to reach it from another machine/container). |
| `--port 8000` | Override the default port `8000`. |
| `--workers N` | Run N worker processes. Not compatible with `--reload`; only use for production-style runs. |
| `--log-level debug` | More verbose Uvicorn/app logging. |

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

Returns `201` with `{"agent_id", "research_mode", "retry_max_count", "critique_threshold"}`
(`api_token` is accepted but never echoed back). `404` if the agent doesn't exist or isn't yours,
`409` if it already has a config (one config per agent).

### `GET /agents/{agent_id}/config` — read an agent's config

```
curl http://127.0.0.1:8000/agents/<agent_id>/config -H "Authorization: Bearer <token>"
```

Returns `{"agent_id", "research_mode", "retry_max_count", "critique_threshold", "model_family",
"model_name"}` (`api_token` is never returned). `404` if the agent doesn't exist, isn't yours, or
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
`status` moves `pending` → `running` → `completed` or `failed`; `research` is `null` until
`completed`, `error_message` is `null` unless `failed`. 404s if the id doesn't exist or belongs
to another user.
