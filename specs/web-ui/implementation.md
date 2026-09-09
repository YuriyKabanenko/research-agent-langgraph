# Implementation: web UI for auth / agents / research

## Approach

A new Vite + React + TypeScript app in a top-level `frontend/` directory (sibling to
`src/`, `alembic/`, `specs/` — keeps JS tooling out of the Python `src/` layout that
`pyproject.toml` scans). Material UI (`@mui/material`) supplies every visible control
(buttons, text fields, select, table, alerts) so no hand-written CSS is needed beyond
Vite's default global stylesheet. `react-router-dom` handles the six routes.

The app is built in three explicit layers, so "business logic" is never mixed into a
component the way it might be tempting to in a small app:

- **Data layer** (`src/api/`) — plain async functions wrapping `fetch`. No React, no
  state, just "call this endpoint, get this typed shape back." Equivalent to a Flutter
  Repository/DataSource.
- **Business logic layer** (`src/hooks/`) — custom hooks that are the *only* things
  allowed to call the data layer. Two kinds of state live here, kept deliberately
  separate:
  - **Server state** (the agents, the research runs — anything that actually lives in
    the DB) is managed by **TanStack Query** (`@tanstack/react-query`). A hook like
    `useAgents()` wraps `useQuery` around `api/agents.ts`'s `listAgents()` and gets
    caching, loading/error state, and refetch-after-mutation for free instead of
    hand-rolled `useState`/`useEffect`.
  - **Client state** (the auth token — the one piece of state that only ever lived in
    the browser) is managed by a **Zustand** store (`src/store/authStore.ts`), with
    Zustand's `persist` middleware backing it with `localStorage`.
- **Presentation layer** (`src/pages/`) — components call hooks, get back
  `{data, isLoading, error}` and some actions, and render MUI. A page never calls
  `fetch` or touches `localStorage` directly.

A thin typed `apiFetch` wrapper in `frontend/src/api/client.ts` (used by every function
in `src/api/`) attaches the `Authorization` header by reading the token straight off the
Zustand store (`authStore.getState().token` — stores are plain objects usable outside
React, not just via a hook, which is what makes this workable from non-component code),
parses `{detail}` error bodies into a typed `ApiError`, and on `401` calls
`authStore.getState().logout()` before rethrowing — one place, not spread across every
page. Request/response shapes live in `frontend/src/api/types.ts`, hand-mirrored 1:1
from the Pydantic models in `src/server/models/`.

In dev, Vite's server proxies `/api/*` to `http://localhost:8000` (`vite.config.ts`
`server.proxy`), so the browser only ever talks to one origin and the FastAPI app needs
no CORS changes. `apiFetch` calls are made against `/api/...` paths.

Two backend gaps block the required pages and are fixed as small, additive changes
alongside the frontend work (not a separate spec, since neither changes existing
behavior — see below): a `GET /research` list endpoint, and a `has_config` flag on
`AgentResponse`.

## Alternatives Considered

- **Plain HTML/CSS, no build step** — rejected: the developer wants React+TS experience
  specifically (job-market driven), not the simplest possible implementation.
- **Hand-written CSS / a CSS framework (Tailwind, Bootstrap)** — rejected in favor of a
  component library: Tailwind/Bootstrap still require writing markup+class soup by hand,
  which is exactly the "tag/CSS" work the developer said they don't want. MUI's
  components (`<TextField>`, `<Button>`, `<Table>`) are usable with near-zero CSS.
- **Plain `useState`/`useEffect` + Context, no TanStack Query/Zustand** — this was the
  original draft, and would work at 6 pages. Rejected once the goal was clarified: the
  point of this project is specifically to see production-standard separation of server
  state / client state / UI (the thing Flutter gets from Riverpod/BLoC out of the box),
  not to minimize dependency count. Revisited in favor of TanStack Query + Zustand.
- **Redux Toolkit instead of Zustand** — both are legitimate, equally "seen in real
  jobs" choices for client state. Zustand is picked here for less boilerplate (no
  actions/reducers/slices ceremony) — closer in feel to a Riverpod provider than
  Redux's action-dispatch model, which matters for a first look at the pattern.
- **FastAPI `CORSMiddleware` instead of a dev proxy** — rejected: a proxy keeps this
  purely a frontend change (plus the two additive schema changes below) and sidesteps
  deciding a production CORS policy before one is needed (Non-Goals excludes deployment
  topology).
- **Separate research detail page** (`/research/{id}`) — rejected: AC-17/AC-18 already
  show topic/status/result/error inline per row in the list; a dedicated detail route
  would be a second page showing the same fields with no new information.

## State changes (`research_assistant/state.py`)

None — this feature is entirely in `src/server/` (two additive changes) and the new
`frontend/`. No LangGraph state/graph/node changes.

## Graph changes (`research_assistant/graph.py`, `nodes.py`)

None.

## LLM / tools changes (`llm/model.py`, `llm/tools.py`)

None.

## Server / API changes (`src/server/`)

Two additive changes, both needed for the Non-Goals-scoped read-only UI (no existing
endpoint's request/response shape is removed or narrowed):

1. **`GET /research` (new)** — returns `list[ResearchResponse]` scoped to
   `Research.user_id == current_user.id`, ordered by `created_at` descending. Requires:
   - `Research` ORM model (`db/base.py`) gains `created_at: Mapped[datetime]`
     (`DateTime(timezone=True)`, `default=lambda: datetime.now(timezone.utc)`,
     `nullable=False`) — same pattern as `AuthToken.created_at`.
   - New Alembic migration (revises `d4e8a2f5c913`) adding the column with a
     `server_default=sa.text("now()")` for backfill, then dropping the server default
     (mirrors `c1d4b7a9f620`'s add-status-column migration, since new inserts always set
     it via the ORM default) — see that migration for the exact shape to copy.
   - `ResearchResponse` (`models/research_models.py`) gains `created_at: datetime` and
     `agent_name: str`. The endpoint (and `GET /research/{research_id}`, updated to match)
     eager-loads the agent via `.options(selectinload(Research.agent))` to read
     `record.agent.name` without an async lazy-load error.
2. **`AgentResponse.has_config: bool` (new field)** — `GET /agents` (`list_agents`) query
   gains `.options(selectinload(Agent.config))` and sets `has_config=agent.config is
   not None` per row. `POST /agents` (`create_agent`) always returns `has_config=False`
   (a config can't exist yet for a just-created agent).

No changes to `POST /register`, `POST /login`, `POST /agents/{agent_id}/config`, or
`POST /research` — the frontend calls them exactly as they exist today.

## Frontend (`frontend/`)

- **Scaffold:** `npm create vite@latest frontend -- --template react-ts`, then add
  `react-router-dom`, `@mui/material`, `@emotion/react`, `@emotion/styled`,
  `@tanstack/react-query`, `zustand`.
- **`vite.config.ts`** — `server.proxy['/api'] = { target: 'http://localhost:8000',
  changeOrigin: true, rewrite: path => path.replace(/^\/api/, '') }`.

**Data layer**

- **`src/api/types.ts`** — TS interfaces mirroring the Pydantic models: `RegisterRequest`,
  `RegisterResponse`, `LoginRequest`, `LoginResponse`, `AgentCreateRequest`,
  `AgentResponse` (incl. `has_config`), `AgentConfigCreateRequest`, `AgentConfigResponse`,
  `ResearchRequest`, `ResearchAcceptedResponse`, `ResearchResponse` (incl. `created_at`,
  `agent_name`), and a `ResearchStatus` string-literal union
  (`"pending"|"running"|"completed"|"failed"`).
- **`src/api/client.ts`** — `apiFetch<T>(path, options)`: prefixes `/api`, attaches
  `Authorization: Bearer <token>` by reading `authStore.getState().token`, JSON-encodes
  the body, throws `ApiError { status, detail }` on non-2xx, and on `401` calls
  `authStore.getState().logout()` before rethrowing.
- **`src/api/auth.ts`** — `register(body)`, `login(body)`.
- **`src/api/agents.ts`** — `listAgents()`, `createAgent(body)`,
  `createAgentConfig(agentId, body)`.
- **`src/api/research.ts`** — `listResearch()`, `createResearch(body)`.

**Business logic layer**

- **`src/store/authStore.ts`** — Zustand store, created with `persist` middleware
  (`localStorage`, key `"auth"`): `{ token: string | null, setToken(token), logout() }`.
  Read from components via the `useAuthStore` hook, and from non-component code (like
  `api/client.ts`) via `authStore.getState()`.
- **`src/hooks/useAuth.ts`** — thin convenience wrapper (`const token =
  useAuthStore(s => s.token)`) plus `useLogin()`/`useRegister()`: `useMutation`s wrapping
  `api/auth.ts`, calling `authStore.getState().setToken(...)` `onSuccess`.
- **`src/hooks/useAgents.ts`** — `useAgents()`: `useQuery({queryKey: ['agents'],
  queryFn: listAgents})`. `useCreateAgent()` / `useCreateAgentConfig()`: `useMutation`s
  that call `queryClient.invalidateQueries({queryKey: ['agents']})` `onSuccess`, so the
  Agents page's cached list is refetched right after a create.
- **`src/hooks/useResearch.ts`** — `useResearches()`: `useQuery({queryKey: ['research'],
  queryFn: listResearch})`. `useCreateResearch()`: `useMutation` that invalidates
  `['research']` `onSuccess`. The "Refresh" button (AC-19) just calls the query's
  `refetch()` — no separate mechanism needed.
- **`src/routes/RequireAuth.tsx`** — redirects to `/login` when `useAuthStore(s =>
  s.token)` is null (AC-5); rendered as a layout route wrapping the four authenticated
  pages.

**Presentation layer**

- **Pages** (`src/pages/`): `RegisterPage.tsx`, `LoginPage.tsx` (call `useRegister`/
  `useLogin`), `NewAgentPage.tsx` (two-step form calling `useCreateAgent` then
  `useCreateAgentConfig`), `AgentsPage.tsx` (`useAgents`, table), `NewResearchPage.tsx`
  (`useAgents` for the picker + `useCreateResearch`), `ResearchesPage.tsx`
  (`useResearches`, table + Refresh button).
- **`src/App.tsx`** — a root `QueryClientProvider` wrapping `<BrowserRouter>` with the
  six routes plus a `/` redirect to `/agents` (if a token is stored) or `/login`; a
  simple `<AppBar>` nav (Agents / New agent / Research / New research / Logout) shown
  only inside `RequireAuth`.

## Affected files

- `src/server/db/base.py` — `Research.created_at` column.
- `alembic/versions/<new>_add_created_at_to_researches.py` — new migration.
- `src/server/models/research_models.py` — `ResearchResponse` gains `created_at`,
  `agent_name`.
- `src/server/models/agent_models.py` — `AgentResponse` gains `has_config`.
- `src/server/main.py` — new `GET /research`; `list_agents`/`get_research` updated to
  eager-load and populate the new fields; `create_agent` sets `has_config=False`.
- `frontend/` — new Vite React+TS app (scaffold, config, `src/api/`, `src/store/`,
  `src/hooks/`, `src/routes/`, `src/pages/`, `src/components/AgentConfigForm.tsx`
  (extracted during implementation, shared by `NewAgentPage` and the new
  `ConfigureAgentPage`), `src/App.tsx`).
- `src/research_assistant/state.py` — fixed `ResearchMode`'s values (trailing commas
  made them 1-tuples, serializing over JSON as `[1]`/`[2]`; now plain `"quick"`/
  `"thorough"` strings). Discovered while writing `AgentConfigCreateRequest`'s TS type;
  DB storage is unaffected (the Postgres enum stores member *names*, not values — see
  `f3a1c9d2e8b4`'s migration comment). Not part of the original plan.
- `src/server/README.md` — updated to match the current API (was still describing the
  old nested `/research` body and the `research_mode` tuple quirk from before this and
  the prior session's changes; also documented the new `/agents` endpoints and
  `GET /research`, neither of which existed when this README was last touched).

## Risks / Landmines

- **Async lazy-loading.** `Agent.config` and `Research.agent` are ORM relationships;
  under `AsyncSession` an un-eager-loaded relationship access raises `MissingGreenlet`
  instead of transparently querying. Both new/changed endpoints must eager-load
  (`selectinload`) — don't reach for `.config`/`.agent` anywhere else without doing the
  same.
- **`agent_id` FK is `nullable=False`** on `Research` (`specs/` prior work) — the config
  form on `/agents/new` must exist and succeed before that agent is usable on
  `/research/new`; AC-13/14 already scope the picker to configured agents only, so this
  should never surface as a runtime error if the UI is followed, but a stale/expired
  token combined with a raw API call could still hit it — not this spec's concern.
- **No Node/npm prerequisite is documented anywhere yet.** `CLAUDE.md`'s Environment
  section only covers the Python venv. Once this lands, it needs a short addition (Node
  version, `cd frontend && npm install && npm run dev`) — not done as part of this spec
  since it doesn't exist until implemented.
- **Migration ordering** — the new `created_at` migration must `down_revision` off
  `d4e8a2f5c913` (the `agent_id`-on-researches migration from prior work), not off
  `c1d4b7a9f620` directly, since that's the current head.
- **Two-step agent creation UX (AC-8/9)** — if the user navigates away between creating
  the agent and submitting its config, they're left with an unconfigured agent; AC-12
  already covers recovering from that (the Agents list links back to the config step),
  so this is a UX consideration, not a bug, but worth remembering while building
  `NewAgentPage`.
- **Cache invalidation is manual and per-mutation.** TanStack Query doesn't know that
  `createAgent`/`createAgentConfig` affects the `['agents']` query, or that
  `createResearch` affects `['research']` — each mutation hook has to explicitly call
  `invalidateQueries` with the matching key. Forgetting one means a page silently shows
  stale data until the next full reload, not a crash — easy to miss when testing.
- **Zustand's `persist` middleware writes to `localStorage` on every `setToken`/`logout`
  call**, same storage key convention as the plain-`localStorage` approach in the
  original draft — nothing else in the app should read/write that key directly, or the
  two can drift out of sync.

## Tasks

- [x] T1 — `Research.created_at` column + Alembic migration (AC-17)
- [x] T2 — `ResearchResponse` gains `created_at`/`agent_name`; `GET /research/{id}` and
  new `GET /research` both eager-load and populate them (AC-17, AC-18)
- [x] T3 — `AgentResponse.has_config`; `GET /agents` eager-loads `Agent.config`;
  `POST /agents` sets `has_config=False` (AC-11, AC-13)
- [x] T4 — Scaffold `frontend/` (Vite React-TS, MUI, react-router-dom, TanStack Query,
  Zustand, dev proxy config)
- [x] T5 — `src/api/types.ts` + `src/api/client.ts` (typed fetch wrapper reading the
  token from `authStore`, 401 handling) (AC-6)
- [x] T6 — `src/api/auth.ts`, `agents.ts`, `research.ts` (data layer functions)
- [x] T7 — `src/store/authStore.ts` (Zustand + `persist`) and `src/routes/RequireAuth.tsx`
  (AC-5, AC-6, AC-7)
- [x] T8 — `src/hooks/useAuth.ts` (`useLogin`, `useRegister`); `RegisterPage`,
  `LoginPage` (AC-1, AC-2, AC-3, AC-4)
- [x] T9 — `src/hooks/useAgents.ts` (`useAgents`, `useCreateAgent`,
  `useCreateAgentConfig`); `NewAgentPage` (AC-8, AC-9, AC-10). Split the config half
  into a shared `src/components/AgentConfigForm.tsx` (not in the original plan) since
  AC-12 needed the same form reachable for an already-existing unconfigured agent, not
  just one just created.
- [x] T10 — `AgentsPage` (list + configured/not-configured state) (AC-11, AC-12), plus
  `ConfigureAgentPage` (`/agents/:agentId/config`) for the AC-12 link target.
- [x] T11 — `src/hooks/useResearch.ts` (`useResearches`, `useCreateResearch`);
  `NewResearchPage` (configured-agent picker + topic form) (AC-13, AC-14, AC-15, AC-16)
- [x] T12 — `ResearchesPage` (list + manual refresh via `refetch()`) (AC-17, AC-18, AC-19)
- [x] T13 — App shell: `QueryClientProvider`, routes, nav, `/` redirect (AC-5, AC-20).
  The nav bar and the auth-guard ended up in the same `RequireAuth` component (not a
  separate layout component) since both only apply once authenticated.

Reviewing and testing against requirements.md's acceptance criteria (including running
the new Alembic migration and manually exercising each page in a browser) is the user's
part — not verified by the agent. Don't mark `Status:` as `Done` in requirements.md.
