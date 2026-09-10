# Implementation: <feature name>

## Approach

Plain-language description of the chosen approach.

## Alternatives Considered

- **Option A** — rejected because ...
- **Option B** — rejected because ...

## State changes (`research_assistant/state.py`)

New or changed fields on `ResearchState` / `ResearchStep`: name, type, default, and
whether it needs a reducer (e.g. `operator.add` for an append-only list, like
`research_steps`).

## Graph changes (`research_assistant/graph.py`, `nodes.py`)

- New nodes:
- New/changed conditional edges and their routing logic:
- Node **id** vs. node **function name** — call out explicitly if they diverge (see the
  `"intial_research"` typo in CLAUDE.md, which is load-bearing because
  `route_after_validate` returns that exact string as a routing target).

## LLM / tools changes (`llm/model.py`, `llm/tools.py`)

Note if this touches the mock functions (`llm_initial_research`, `llm_research`,
`research_done`) or wires up a real model/tool call for the first time.

## Server / API changes (`server/`)

Any change to request/response models, routes, or `AgentConfig` fields.

## Affected files

One line per file: path — what changes.

## Risks / Landmines

Known sharp edges this touches or is adjacent to, e.g.:
- The `llm_research` import/def name-shadowing bug in `nodes.py` (see CLAUDE.md
  "Known landmine").
- Empty stub files (`llm/tools.py`, `main.py`, both `__init__.py`) that this feature may
  need to actually fill in for the first time.
- `tokens.txt` — never read from or write into this file.

## Tasks

Ordered checklist. Each task references the AC(s) from requirements.md it satisfies.
Keep tasks small enough that each one is independently verifiable.

- [ ] T1 — <task> (AC-1)
- [ ] T2 — <task> (AC-2, AC-3)
- [ ] T3 — <task> (AC-...)

Reviewing and testing against the acceptance criteria above is the user's part, not the
agent's — stop once the checklist is done. Don't add a verification log, don't run the
app/tests to confirm ACs pass, and don't mark `Status:` as `Done` in requirements.md.
