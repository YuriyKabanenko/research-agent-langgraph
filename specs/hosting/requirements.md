# Feature Spec: Public hosting (CV demo)

- **Status:** Draft

## Problem

The project only runs locally (`./scripts/up.sh`), so there's no link to put on a CV. The
current Compose setup isn't production-shaped either: `front` runs the Vite dev server, and
`migrate` is a Compose-only one-shot service that a hosting platform won't run.

## Goal

A recruiter can open a public HTTPS URL, see the app, and look at example research runs
without installing anything or pasting an API key.

## Non-Goals

- Custom domain (a platform subdomain is fine for now).
- CI/CD beyond the platforms' built-in "deploy on push to `master`".
- Horizontal scaling, background job queues (Celery/RQ), or moving off FastAPI
  `BackgroundTasks`.
- Changing the auth model (opaque bearer tokens stay as-is).

## Acceptance Criteria

- **AC-1:** WHEN a visitor opens the public frontend URL, the system SHALL serve the
  production build (`npm run build` output), not the Vite dev server.
- **AC-2:** WHEN the frontend calls `/api/<path>`, the hosting layer SHALL forward it to the
  backend as `/<path>` (prefix stripped, same as `frontend/vite.config.ts`), with no CORS
  changes on the server.
- **AC-3:** WHEN a visitor opens a deep link (e.g. `/researches`) directly or refreshes it,
  the system SHALL serve the SPA's `index.html` instead of a 404.
- **AC-4:** WHEN the backend is deployed, the system SHALL run `alembic upgrade head` before
  the new version starts serving traffic, and a failed migration SHALL block the deploy.
- **AC-5:** WHEN a research run is in progress, the backend process SHALL NOT be put to sleep
  for inactivity (the run lives in `BackgroundTasks`; it must finish and reach
  `completed`/`failed`/`awaiting_review`).
- **AC-6:** WHEN a visitor opens the site after a long idle period, the first page SHALL load
  without a cold-start delay (always-on backend, not a free tier that sleeps).
- **AC-7:** WHEN a visitor logs into the demo account, the system SHALL show at least one
  finished research run, so the app can be judged without a personal Anthropic key.
- **AC-8:** The Tavily and Anthropic accounts used by the deployment SHALL have spending caps
  set, and the backend's secrets SHALL live only in the platform's env settings (never in
  the repo, never `tokens.txt`).

## Open Questions

- **Platform:** Railway (backend + Postgres) + Vercel (frontend) is the recommended default
  (~$5/mo). Alternative: a single Hetzner VPS running the existing Compose setup
  (~€4/mo, more upkeep, arguably better CV story). Decide before implementation.
- **Open registration:** keep `/register` public, or add rate limiting / disable it and ship
  only the demo account? Anyone registering can trigger Tavily calls on our key.
- **Demo account data:** seed it via a script/migration, or run a few researches manually
  once and leave them? (Manual is simpler; a script is reproducible.)
- **Prerequisite bug:** fix the redundant `add_edge("validate_input", "initial_plan")`
  (see CLAUDE.md) before going public, since an invalid topic currently still burns a full
  paid research run. Track here or in its own spec?
