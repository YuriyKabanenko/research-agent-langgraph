# Implementation: Public hosting (CV demo)

## Approach

Split hosting, each piece on the platform that fits it best:

- **Backend + Postgres → Railway.** One service built from `server/Dockerfile` with the
  build context at the repo root (same as `docker-compose.yml`), plus Railway's Postgres
  add-on. Railway sets `DATABASE_URL`. Migrations run as a pre-deploy command
  (`alembic upgrade head`), which replaces the Compose `migrate` service. The
  `AsyncPostgresSaver.setup()` in `lifespan` already creates the checkpoint tables on
  startup. Railway services are always on, so `BackgroundTasks` runs aren't killed and
  there's no cold start.
- **Frontend → Vercel.** It builds `frontend/` with `npm run build` and serves `dist/`. A
  `vercel.json` rewrite proxies `/api/*` to the Railway URL with the prefix stripped. That
  matches what the Vite dev proxy does today, so `src/api/client.ts` (relative
  `fetch('/api' + path)`) and the server both stay unchanged, with no CORS. A catch-all
  rewrite to `index.html` handles React Router deep links.

Sketch of `frontend/vercel.json`:

```json
{
  "rewrites": [
    { "source": "/api/:path*", "destination": "https://<back>.up.railway.app/:path*" },
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```

## Alternatives Considered

- **Single VPS (Hetzner) + existing `docker compose`.** Reuses the most, and "self-hosted
  with Compose + Caddy" reads well on a CV. Deferred, not rejected: it needs `front`
  swapped for a static build behind nginx/Caddy, TLS setup, and ongoing OS upkeep.
- **Fully free (Neon Postgres + Render free + Vercel).** Rejected because free web services
  sleep when idle. That kills in-flight `BackgroundTasks` runs (breaks AC-5) and gives a
  30–60 s cold start (breaks AC-6).
- **Serverless backend (Vercel/Lambda functions).** Rejected because research runs last
  minutes and outlive the request, so they need a long-lived process.

## State changes (`research_assistant/state.py`)

None.

## Graph changes (`research_assistant/graph.py`, `nodes.py`)

None for hosting itself. Prerequisite (see Open Questions in requirements.md): remove the
redundant `add_edge("validate_input", "initial_plan")`.

## LLM / tools changes (`llm/model.py`, `llm/tools.py`)

None. BYOK keys keep coming from `AgentConfig`. `TAVILY_API_KEY` and `LANGSMITH_*` move to
Railway env vars.

## Server / API changes (`server/`)

- Possibly none. Check whether `server/Dockerfile` binds uvicorn to `0.0.0.0` and Railway's
  `$PORT` (Railway injects `PORT`; either read it or set the service port to 8000).
- `DATABASE_URL` / `CHECKPOINT_DATABASE_URL` in `server/db/session.py`: Railway gives a
  `postgresql://` URL. Confirm that both the asyncpg driver URL and the psycopg checkpoint
  URL are derived correctly from it (they may need different schemes).
- The `APP_DB_USER` non-superuser role from `docker-init/init-app-role.sh` doesn't exist on
  Railway. Either connect as Railway's default user or create the role manually once.
- Optional, depending on the open-registration decision: rate limiting on `/register` and
  `/research`.

## Affected files

- `frontend/vercel.json` — new; `/api` proxy + SPA fallback rewrites.
- `railway.json` (repo root) — new; Dockerfile path `server/Dockerfile`, pre-deploy
  `alembic upgrade head`, healthcheck `/health`.
- `server/Dockerfile` — maybe; `$PORT` / host binding.
- `server/db/session.py` — maybe; URL scheme handling for Railway's `DATABASE_URL`.
- `README.md` — live demo link, demo credentials, short screen recording/GIF.

## Risks / Landmines

- **Cost exposure:** open `/register` + the server-side Tavily key means strangers can spend
  our quota. Set spending caps before sharing the link (AC-8).
- **`BackgroundTasks` + redeploys:** a deploy restarts the process and kills in-flight runs,
  leaving rows stuck in `running`. That's acceptable for a demo, but note it.
- **Validate-input landmine** (CLAUDE.md): invalid topics still run the full paid loop.
- `tokens.txt` — never read from it, commit it, or copy it into platform env settings.
- `.dockerignore` already excludes `.env`/`tokens.txt`/`frontend/`. Keep it that way for the
  Railway build context.

## Tasks

- [ ] T1 — Resolve the open questions in requirements.md (platform, registration, demo data,
  prerequisite bug).
- [ ] T2 — Railway: Postgres add-on + backend service from `server/Dockerfile`, env vars,
  `railway.json` with pre-deploy migration and `/health` healthcheck (AC-4, AC-5, AC-6, AC-8).
- [ ] T3 — Fix `$PORT` binding / DB URL schemes if T2 surfaces them (AC-4).
- [ ] T4 — Vercel: project rooted at `frontend/`, `vercel.json` rewrites (AC-1, AC-2, AC-3).
- [ ] T5 — Demo account with a few finished research runs (AC-7).
- [ ] T6 — Spending caps on Tavily/Anthropic; rate limiting if decided in T1 (AC-8).
- [ ] T7 — README: live link, demo credentials, screen recording.

Reviewing and testing against the acceptance criteria above is the user's part, not the
agent's. Stop once the checklist is done.
