# Feature Spec: web UI for auth / agents / research

- **Status:** Implemented

## Problem

The FastAPI backend (`src/server/`) supports registration/login, creating agents and their
configs, and running/checking research — but only via raw HTTP calls (curl/Postman/the
`/docs` page). There is no browser UI, so anyone who isn't comfortable hand-crafting
requests (and remembering to attach a bearer token) can't use the system at all.

The developer building this is a mobile developer, not a web frontend dev, doing this to
learn how a React+TypeScript frontend fits together (routing, forms, typed API calls,
auth-token state) rather than to ship a polished product — that shapes several of the
Non-Goals below.

## Goal

From a browser, a user can: register or log in, create an agent and give it a config,
see the list of their agents, start a research run against a configured agent, and see
the list/status/result of their past research runs — with every step driven by clicking
through pages, never a manual HTTP call.

## Non-Goals

- **No production deployment topology.** This covers local dev only: the frontend talks
  to the backend through the Vite dev server, not a reverse proxy or same-origin static
  hosting. Making this work in a real deployment (CORS, building/serving static assets) is
  future scope.
- **No edit/delete for agents, configs, or research runs.** Only create + list, matching
  the backend's current CRUD surface (no `PATCH`/`DELETE` endpoints exist for any of
  these) — adding delete/edit would require new backend endpoints, out of scope here.
- **No token refresh/expiry/revocation UI.** Matches `specs/auhtentication-security`'s
  design — a token is valid until deleted from the DB. "Logout" only forgets the token
  client-side.
- **No pagination** on the Agents or Researches lists — fine at the scale this is used at.
- **No automated frontend test suite.** Matches this repo's existing posture (no
  pytest/ruff installed for the Python side either) — verification is manual, in-browser.

## Acceptance Criteria

### Register (`/register`)

- **AC-1:** WHEN an unauthenticated visitor submits the Register form with a name
  (1-50 chars) and password (6-100 chars), the system SHALL call `POST /register`,
  store the returned token, and navigate to the Agents page.
- **AC-2:** IF `POST /register` responds with a non-2xx status, THEN the page SHALL
  display the server's error detail and SHALL NOT store a token or navigate away.

### Login (`/login`)

- **AC-3:** WHEN a visitor submits the Login form with name + password, the system SHALL
  call `POST /login`, store the returned token, and navigate to the Agents page.
- **AC-4:** IF `POST /login` responds `401`, THEN the page SHALL display "Invalid
  username or password" and SHALL NOT store a token or navigate away.

### Session handling (applies to every authenticated page)

- **AC-5:** WHEN a route that requires auth is opened with no token stored, the system
  SHALL redirect to `/login` without calling any backend endpoint that requires auth.
- **AC-6:** WHEN any API call made with a stored token responds `401`, the system SHALL
  clear the stored token and redirect to `/login`.
- **AC-7:** WHEN an authenticated user clicks "Logout", the system SHALL clear the stored
  token and redirect to `/login` (no backend call — there is no revoke endpoint).

### Create agent + config (`/agents/new`)

- **AC-8:** WHEN an authenticated user submits the "New agent" form with a name, the
  system SHALL call `POST /agents` and, on success, reveal a config form scoped to the
  newly created agent's id, with `research_mode`/`retry_max_count`/`critique_threshold`
  pre-filled with the backend's defaults (quick / 3 / 6) and `api_token` required blank.
- **AC-9:** WHEN the user submits the config form, the system SHALL call
  `POST /agents/{agent_id}/config` and, on success, show a confirmation with a link to
  the Agents page.
- **AC-10:** IF either call fails (e.g. `409` because a config already exists), THEN the
  page SHALL display the server's error detail and SHALL NOT navigate away.

### List agents (`/agents`)

- **AC-11:** WHEN an authenticated user opens this page, the system SHALL call
  `GET /agents` and render one row per agent showing its name and whether it has a
  config ("Configured" / "Not configured").
- **AC-12:** IF an agent is not configured, THEN its row SHALL link to the config step
  for that agent (reusing the config half of `/agents/new`) instead of being selectable
  for new research.

### Create research (`/research/new`)

- **AC-13:** WHEN an authenticated user opens this page, the system SHALL call
  `GET /agents` and populate an agent picker containing only configured agents.
- **AC-14:** IF the user has zero configured agents, THEN the page SHALL show a message
  pointing at "Create an agent" instead of rendering the picker/form.
- **AC-15:** WHEN the user submits a topic (>=5 chars) with a selected agent, the system
  SHALL call `POST /research` and, on the `202` response, navigate to the Researches page.
- **AC-16:** IF `POST /research` responds non-2xx, THEN the page SHALL display the
  server's error detail and SHALL NOT navigate away.

### List researches (`/research`)

- **AC-17:** WHEN an authenticated user opens this page, the system SHALL call
  `GET /research` and render one row per research the user owns — topic, agent name,
  status, and created-at — newest first.
- **AC-18:** WHEN a row's status is `completed`, it SHALL show the research result text;
  WHEN `failed`, it SHALL show `error_message`; WHEN `pending`/`running`, it SHALL show
  only the status (no result/error field exists yet).
- **AC-19:** WHEN the user clicks "Refresh", the system SHALL re-call `GET /research` and
  re-render the list with any updated statuses.

### Local dev connectivity

- **AC-20:** WHEN the frontend dev server calls any backend endpoint, the request SHALL
  reach the FastAPI server without a CORS error, using the Vite dev-server proxy (see
  implementation.md) rather than a backend CORS change.

## Open Questions

None — resolved:
- Framework: **React + TypeScript** (the developer's explicit choice, despite not
  planning to specialize in web frontend — this is deliberately a learning project).
- Styling approach: a component library (see implementation.md) instead of hand-written
  CSS, per the developer's stated dislike of "tag/CSS" work.
- Two backend gaps this UI needs are treated as in-scope prerequisites, not separate
  specs: (1) no endpoint lists all of a user's research runs, only single-record
  `GET /research/{id}`; (2) `AgentResponse` doesn't say whether an agent has a config.
  Both are additive, low-risk changes — see implementation.md.
