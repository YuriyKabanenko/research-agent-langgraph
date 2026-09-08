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

### `GET /login`

Note this is a `GET` with a JSON body, so `curl` needs `-X GET` explicit (it switches to `POST`
automatically when `-d` is given without `-X`):

```
curl -X GET http://127.0.0.1:8000/login \
  -H "Content-Type: application/json" \
  -d '{"name": "alice", "password": "hunter22"}'
```

Returns a fresh `{"token"}`.

### `POST /research` — start a research run

Research runs in the background (it can take a while), so this returns immediately with a job id
instead of the result:

```
curl -X POST http://127.0.0.1:8000/research \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
        "body": {"topic": "quantum computing"},
        "config": {"token": "<anthropic-api-key>", "research_mode": [1], "retry_max_count": 3, "critique_threshold": 6}
      }'
```

Returns `202` with `{"id", "status": "pending"}`.

> **Note:** the request body is nested (`body`/`config`), not the flat `{"topic", "config"}` shape
> described in the root `CLAUDE.md` — `get_agent_service`'s `config: AgentConfig` parameter is an
> implicit second body param, so FastAPI nests both by name. Also note `research_mode` currently
> has to be passed as `[1]` (quick) or `[2]` (thorough) — a trailing comma in `ResearchMode`
> (`research_assistant/state.py`) accidentally makes its values 1-tuples instead of plain ints.
> Both are pre-existing quirks, not intentional API design.

### `GET /research/{id}` — poll for the result

```
curl http://127.0.0.1:8000/research/<id> \
  -H "Authorization: Bearer <token>"
```

Returns `{"id", "topic", "status", "research", "error_message"}`. `status` moves
`pending` → `running` → `completed` or `failed`; `research` is `null` until `completed`,
`error_message` is `null` unless `failed`. 404s if the id doesn't exist or belongs to another user.
