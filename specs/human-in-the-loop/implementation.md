# Implementation: human-in-the-loop review of the final draft

## Approach

Use LangGraph's native HITL mechanism: a **checkpointer**, `interrupt()` and
`Command(resume=...)`.

1. Compile the outer graph with `AsyncPostgresSaver` (package
   `langgraph-checkpoint-postgres`). LangGraph then saves state after every step,
   keyed by `thread_id` = `Research.id`. The subgraphs (`research_loop`,
   `subtopic_worker`) are compiled without a checkpointer and inherit the parent's.
2. A new `human_review` node sits between `research_loop` and `give_final_respond`.
   It picks the candidate draft and calls `interrupt({"candidate": ...})`. The run
   stops, `ainvoke()` returns a result containing `__interrupt__`, and the background
   task ends. Nothing stays in memory while waiting for the user.
3. The user's decision starts a **new** `ainvoke(Command(resume=decision), config)`
   with the same `thread_id`. LangGraph loads the checkpoint and re-runs `human_review`
   from its first line. This time `interrupt()` returns `decision` instead of pausing.
   The node returns a `Command(goto=...)`:
   - approve → `give_final_respond`, with `final_response = candidate`
   - reject → `research_loop`, with `critical_analysis = feedback`, which
     `llm_research` already uses as its revision instruction (`nodes.py:247`)
4. The server maps the pause onto a new `ResearchStatus.awaiting_review` and adds
   `POST /research/{id}/review` to resume.

## Alternatives Considered

- **Reject → route to `critical_analysis` (the critique node)**: rejected. That node
  rates the *existing* latest draft. It would re-rate the same text and overwrite the
  human's feedback with its own critique. The draft has to be rewritten first, which is
  `llm_research`, the entry point of `research_loop`.
- **Keep `give_final_respond` picking the max-rated step**: rejected. A revision the
  human asked for can get a lower AI rating than the original. The human would approve
  the fix and get the unfixed draft back (see AC-3/AC-5). The candidate is chosen once,
  in `human_review`, and passed through unchanged.
- **Static breakpoints (`compile(interrupt_before=["give_final_respond"])`) +
  `update_state()`**: rejected. It's mostly a debugging tool, and routing (approve vs.
  revise) would need a separate conditional edge that reads a state field the server
  injects. `interrupt()` + `Command` keeps the decision and the routing in one node.
- **`InMemorySaver` in the server**: rejected. Checkpoints disappear on restart and on
  every `uvicorn --reload` (AC-9).
- **Hand-rolled state snapshot in our own table**: rejected. It reinvents the
  checkpointer, and the point of backlog #6 is to learn the idiomatic mechanism.
- **Read the pending draft from the checkpoint (`aget_state`) on `GET /research/{id}`**:
  rejected. It adds checkpoint reads to a hot read path and couples the API to graph
  internals. Writing the candidate into existing `Research` columns once, at pause time,
  is simpler.

## State changes (`research_assistant/state.py`)

- `ResearchState.human_feedback: str = ""`. No reducer (last write wins). Set to the
  human's feedback on reject. Non-empty means "the latest step is a human-requested
  revision", which `human_review` uses to choose the candidate (AC-5). It lives only on
  `ResearchState`, not `_SharedResearchFields`, so the subgraphs never see it.
- No changes to `ResearchStep` / `SubtopicResult`.
- `final_response` is now written by `human_review` (on approve) instead of
  `give_final_respond`.

## Graph changes (`research_assistant/graph.py`, `nodes.py`)

- **New node `human_review`** (node id = function name = `human_review`):
  ```python
  def human_review(state: ResearchState) -> Command[Literal["give_final_respond", "research_loop"]]:
      if state["human_feedback"]:
          candidate = state["research_steps"][-1]
      else:
          candidate = max(state["research_steps"], key=lambda s: s["research_rate"])

      decision = interrupt({"candidate": candidate})

      if decision["approved"]:
          return Command(goto="give_final_respond", update={"final_response": candidate})
      return Command(
          goto="research_loop",
          update={"critical_analysis": decision["feedback"], "human_feedback": decision["feedback"]},
      )
  ```
  - **Nothing with side effects before `interrupt()`.** On resume the node re-runs
    from its first line, so anything above `interrupt()` runs twice. Picking the
    candidate is pure and runs on the same checkpointed state both times, so it
    produces the same result.
  - The `Command[Literal[...]]` return annotation is how LangGraph learns the node's
    possible destinations (graph validation + `draw_graph.py`). No `add_edge` from
    `human_review`.
- **`give_final_respond`**: stop recomputing the max. Use `state["final_response"]`
  and keep the summary print.
- **`research_loop` wrapped in `_run_research_loop`** (found while implementing, checked
  on a toy graph): a compiled subgraph added directly as a node returns its *whole*
  `research_steps` list, and the parent's `operator.add` appends it to what the parent
  already has. On the first pass that's `[] + [s1..s3]`, which is fine. When
  `human_review` sends the graph back it becomes `[s1..s3] + [s1..s4]`, with every
  step duplicated. The wrapper invokes `research_loop` and returns only
  `result["research_steps"][len(state["research_steps"]):]`, plus `messages` (safe,
  because `add_messages` dedupes by id) and `critical_analysis`. The node id stays
  `research_loop`. Same pattern as the existing `_run_subtopic_worker`.
- **Edges**: replace `add_edge("research_loop", "give_final_respond")` with
  `add_edge("research_loop", "human_review")`. The fan-out path
  (`combine_subtopics → END`) stays unchanged (AC-6).
- **Compilation**: `graph.py` currently compiles `agent = agent_builder.compile()` at
  import time. Replace it with `build_agent(checkpointer)`, which returns
  `agent_builder.compile(checkpointer=checkpointer)`. The server calls it in `lifespan`
  with the Postgres saver, and the CLI calls it with `InMemorySaver`.
  `research_loop`/`subtopic_worker` keep compiling at module level with no checkpointer.
- **CLI** (AC-7): shared helper `run_with_cli_review(agent, initial_state)` in
  `graph.py`, used by both `graph.py` `main()` and `research_assistant/main.py`. Compile
  with `InMemorySaver`, pass a fixed `thread_id`, then loop: while `"__interrupt__" in result`, print the candidate, read `y` or
  feedback text via `input()`, and call `agent.invoke(Command(resume=...), config)`.
- **Retry cap interaction** (no code change): after a reject, `research_loop` restarts
  at `llm_research`. `route_after_analysis` usually already sees
  `len(research_steps) >= retry_max_count`, so each piece of feedback typically gives
  one revision. If the first loop ended early because the critique passed, the revision
  can use the remaining attempts.

## LLM / tools changes (`llm/model.py`, `llm/tools.py`)

None. The API-key contextvar mechanism stays as is. Because the key is not part of graph
state, it's never checkpointed (AC-19), but the **resume** path has to set it again (see
`AgentService` below).

## Server / API changes (`server/`)

- **Dependencies**: add `langgraph-checkpoint-postgres` and `psycopg[binary,pool]` to
  `pyproject.toml` / the server's requirements.
- **Checkpointer connection string**: psycopg 3 takes a plain `postgresql://...` URL.
  Derive it from `DATABASE_URL` by replacing `postgresql+asyncpg://` with
  `postgresql://`. Don't add a second env var.
- **`lifespan` (`main.py`)**:
  ```python
  async with AsyncPostgresSaver.from_conn_string(checkpoint_url) as saver:
      await saver.setup()                       # idempotent, creates checkpoint* tables
      app.state.checkpointer = saver
      app.state.agent = build_agent(saver)
      yield
  await engine.dispose()
  ```
  The app DB role has `ALL` on schema `public` (`docker-init/init-app-role.sh`), so
  `setup()` can create its tables.
- **`ResearchStatus`** (`server/models/research_models.py`): add
  `awaiting_review = "awaiting_review"`.
- **Alembic migration (hand-written)**:
  `op.execute("ALTER TYPE researchstatus ADD VALUE IF NOT EXISTS 'awaiting_review'")`.
  Autogenerate does not detect new enum values. Postgres cannot drop an enum value, so
  `downgrade()` is a commented no-op.
- **`alembic/env.py`** (AC-11): add an `include_object` hook to both `context.configure`
  calls that returns `False` for tables whose name starts with `checkpoint` (the saver
  creates `checkpoints`, `checkpoint_blobs`, `checkpoint_writes`,
  `checkpoint_migrations`).
- **`AgentService`** (`services/agent_service.py`):
  - `start(research_id, topic)`: builds the initial state as `invoke` does today (plus
    `human_feedback: ""`) and runs `ainvoke(initial_state, config)`.
  - `resume(research_id, decision)`: runs `ainvoke(Command(resume=decision), config)`.
  - Both use `config = {"configurable": {"thread_id": str(research_id)}}` and wrap the
    call in `set_api_key`/`reset_api_key`.
  - Both return a small result type: `Paused(candidate: ResearchStep)` when
    `"__interrupt__"` is in the result (`result["__interrupt__"][0].value["candidate"]`),
    otherwise `Completed(final: ResearchStep)`. `error_message` → `ValueError` as today.
- **`_run_research` + new `_resume_research`** (`main.py`): share one helper that
  handles the outcome.
  - `Paused` → write the candidate into `resarch`/`tools_used`/`research_rate`, status
    `awaiting_review` (AC-12).
  - `Completed` → as today, status `completed`.
  - Exceptions → `failed`, as today.
- **`get_agent_service` refactor** (`dependencies.py`): pull the "agent belongs to user
  + has config → `AgentService`" logic into a helper,
  `build_agent_service(agent_id, user, session, agent)`. `get_agent_service` keeps
  reading `agent_id` from `ResearchRequest`. The review endpoint calls the helper with
  `research.agent_id` (AC-18).
- **New `ReviewRequest` model**: `approved: bool`, `feedback: str | None`. A model
  validator rejects `approved=False` with a missing or blank `feedback` (→ 422, AC-15).
  Strip `feedback`.
- **New route `POST /research/{research_id}/review`** → `202`,
  returns `ResearchAcceptedResponse`:
  1. Load the research. Missing or not owned → `404` (AC-16).
  2. Atomic transition:
     `UPDATE researches SET status='running' WHERE id=:id AND status='awaiting_review'`.
     If it matches 0 rows → `409` (AC-17). This conditional update is what stops a
     double-click from resuming twice. A read-then-write check would race.
  3. Build the `AgentService` via the helper with `research.agent_id`, then schedule
     `_resume_research(research.id, decision, agent_service)`.
- **`DELETE /research/{id}`** (AC-10): after deleting the row, call
  `await request.app.state.checkpointer.adelete_thread(str(research_id))`.

## Frontend changes (`frontend/`)

- `src/api/types.ts`: add `"awaiting_review"` to `ResearchStatus` and a `ReviewRequest`
  type that mirrors the server model.
- `src/api/research.ts`: add `submitReview(id, body)` → `POST /research/{id}/review`.
- `src/hooks/useResearch.ts`: add a mutation for `submitReview` that invalidates the
  research list/detail queries on success (AC-22).
- `src/pages/ResearchesPage.tsx`: track the viewed run by **id** (not a snapshot object), so
  the open dialog follows the list as it refetches after a review (AC-22). Add a chip color for `awaiting_review` to the status
  map (around line 40) (AC-20). If that map is typed `Record<ResearchStatus, ...>`, the
  compiler flags the missing key.
- `src/components/ResearchDetailDialog.tsx`: when the status is `awaiting_review`, show
  the candidate, an **Approve** button, a feedback text field and a **Send back** button
  (disabled while the feedback is blank). Show mutation errors inline (AC-21, AC-22).

## Affected files

- `pyproject.toml` — add `langgraph-checkpoint-postgres`, `psycopg[binary,pool]`.
- `research_assistant/state.py` — add `human_feedback` to `ResearchState`.
- `research_assistant/nodes.py` — new `human_review`; `give_final_respond` uses
  `final_response`.
- `research_assistant/graph.py` — `human_review` node + edge, `build_agent(checkpointer)`,
  interactive CLI loop.
- `research_assistant/draw_graph.py`, `research_assistant/main.py` — both import the
  module-level `agent`; switch to `build_agent(...)` (drawing can use no checkpointer).
- `server/main.py` — lifespan checkpointer, `_resume_research`, review route, delete
  cleanup.
- `server/services/agent_service.py` — `start`/`resume`, `Paused`/`Completed`.
- `server/dependencies.py` — `build_agent_service` helper.
- `server/models/research_models.py` — `awaiting_review`, `ReviewRequest`.
- `alembic/env.py` — `include_object` filter.
- `alembic/versions/<new>_add_awaiting_review_status.py` — enum value.
- `server/README.md` — document the new endpoint and status.
- `frontend/src/api/types.ts`, `frontend/src/api/research.ts`,
  `frontend/src/hooks/useResearch.ts`, `frontend/src/pages/ResearchesPage.tsx`,
  `frontend/src/components/ResearchDetailDialog.tsx` — review UI.
- `CLAUDE.md` — update the architecture section (new node, checkpointer, status).

## Risks / Landmines

- **Subgraph nodes + `operator.add` reducers.** Any compiled subgraph that is
  re-entered and shares a reducer-backed key with the parent duplicates that key. Keep
  `research_loop` behind `_run_research_loop` (see Graph changes).
- **Node re-runs on resume.** Anything placed above `interrupt()` in `human_review`
  later (logging to the DB, an LLM "summarize for reviewer" call) runs twice. Keep it
  pure.
- **Windows + async psycopg.** psycopg's async mode doesn't support the
  `ProactorEventLoop` (the Windows default). If local `uvicorn` fails with an error
  about it, set a `WindowsSelectorEventLoopPolicy` before the loop starts. Docker
  (Linux) is not affected.
- **Checkpointer connections (decided in T1).** `lifespan` uses a psycopg
  `AsyncConnectionPool` (autocommit, dict_row, prepare_threshold=0) with
  `AsyncPostgresSaver(pool)`, not `from_conn_string`, which holds a single connection
  behind a lock and would serialize checkpoint writes across concurrent runs.
- **Checkpoint deserialization of custom types (resolved in T1).** Confirmed: the
  default serializer warns on `ModelFamily`/`ResearchMode` and says they will be blocked
  in a future version. `graph.py` `CHECKPOINT_SERDE` allow-lists both, and every saver
  (Postgres + CLI `InMemorySaver`) uses it. Original note: State contains the `ModelFamily` and
  `ResearchMode` enums. Recent `langgraph-checkpoint` versions can warn about or refuse
  deserializing types that aren't allow-listed. If resume logs such a warning,
  register these types with the saver's serializer.
- **Autogenerate vs. checkpoint tables.** Without the `include_object` filter, the next
  autogenerated revision drops the saver's tables. Always review autogenerated
  revisions (per `alembic/README`).
- **Enum migration is one-way.** `ADD VALUE` can't be reverted in Postgres. Downgrading
  below this revision leaves the value in place.
- **Two connection pools** (asyncpg for the app, psycopg for the saver) against the same
  DB. Fine at this scale, but it doubles the connection count.
- **Paused rows hold checkpoints forever** until deleted (no timeout, see Non-Goals).
  Checkpoint size grows with `messages`, which the `add_messages` reducer accumulates.
- **Stale candidate on reject → error.** If the resumed run fails, the row goes to
  `failed` and keeps the previous candidate in `resarch`. That's acceptable, but the UI
  shouldn't present it as a final answer. `failed` status already signals this.
- `tokens.txt` — never read from or write into this file.

## Tasks

- [x] T1 — Add dependencies; derive the psycopg URL from `DATABASE_URL`; open
      `AsyncPostgresSaver` in `lifespan`, `setup()`, keep it on `app.state` (AC-8)
- [x] T2 — `alembic/env.py` `include_object` filter for `checkpoint*` tables (AC-11)
- [x] T3 — `graph.py`: replace module-level `agent` with `build_agent(checkpointer)`;
      update `server/main.py`, `draw_graph.py` and `research_assistant/main.py`
      imports (AC-8)
- [x] T4 — `state.py` `human_feedback`; `nodes.py` `human_review`; `give_final_respond`
      uses `final_response`; rewire `research_loop → human_review` (AC-1–AC-6)
- [x] T5 — CLI `main()` with `InMemorySaver` + interactive resume loop (AC-7)
- [x] T6 — `ResearchStatus.awaiting_review` + hand-written Alembic enum migration (AC-12)
- [x] T7 — `AgentService.start`/`resume` returning `Paused`/`Completed`, contextvar set
      on both paths (AC-9, AC-18, AC-19)
- [x] T8 — `_run_research`/`_resume_research` shared outcome handling (AC-12–AC-14)
- [x] T9 — `build_agent_service` helper; `ReviewRequest` with the blank-feedback
      validator; `POST /research/{id}/review` with the atomic status transition
      (AC-13–AC-18)
- [x] T10 — `DELETE /research/{id}` deletes the checkpoint thread (AC-10)
- [x] T11 — Frontend: types, `submitReview`, mutation hook, status chip, review UI in
      `ResearchDetailDialog` (AC-20–AC-22)
- [x] T12 — Update `server/README.md` and `CLAUDE.md`

Reviewing and testing against the acceptance criteria above is the user's part, not the
agent's — stop once the checklist is done. Don't add a verification log, don't run the
app/tests to confirm ACs pass, and don't mark `Status:` as `Done` in requirements.md.
