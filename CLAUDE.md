# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

This is a **self-checking research assistant** built on LangGraph. It takes a topic/question,
produces a draft answer, critiques its own draft, and loops back to research again if the
critique says the draft isn't good enough — up to a configurable retry limit. The full spec
(client brief + user stories US-1 through US-8) lives in `user_stories.txt` at the repo root;
consult it before changing graph behavior, since it defines the intended acceptance criteria
(e.g. empty-input handling, retry counting, best-effort vs. confident final output, run history).

The implementation is a work in progress: `llm/model.py` currently contains mock functions
(`llm_initial_research`, `llm_research`, `research_done`) that return canned strings / random
booleans instead of calling a real model, and `llm/tools.py`, `main.py`, and both `__init__.py`
files are empty stubs. `langchain-anthropic` and `anthropic` are installed but not yet wired up.

## Environment

- Python virtualenv at `.venv/`. Activate it or call `.venv/Scripts/python.exe` directly (Windows).
- The repo is a `src/` layout, installed editable via `pyproject.toml` at the repo root
  (`.venv/Scripts/python.exe -m pip install -e . --no-deps`). It contains two packages,
  `research_assistant` (`src/research_assistant/`) and `server` (`src/server/`), both using
  absolute imports (`from research_assistant.state import ...`, `from server.models.agent_models
  import ...`). No `sys.path` manipulation is needed anywhere — if the editable install ever goes
  stale (e.g. after moving files), re-run the `pip install -e .` above.
- Key dependencies (declared in `pyproject.toml`): `langgraph`, `langchain`, `langchain-anthropic`,
  `anthropic`, `tavily-python`, `fastapi`, `uvicorn`, `pydantic`, `python-dotenv`, `pillow`.
- No test runner, linter, or formatter is installed in this environment (no pytest/ruff/black/mypy).
  Don't assume `pytest`/`ruff` commands work — verify changes by running the graph directly.
- `.env` lives at the repo root (gitignored) and holds `API_KEY`, `TAVILY_API_KEY`, and LangSmith
  tracing vars. Both entrypoints call `load_dotenv()` with no arguments, which searches upward from
  the current working directory — run Python from the repo root (or a subdirectory of it), not from
  somewhere unrelated, or the key won't be found.

## Running the graph

Because the project is an editable install, both packages are importable from anywhere — run from
the repo root so `load_dotenv()` finds `.env`:

```
.venv/Scripts/python.exe -m research_assistant.main "your topic here"
```

`research_assistant/graph.py` still has an `if __name__ == "__main__":` block that runs a hardcoded
sample topic through `agent.invoke(...)` and makes a real LLM call — don't execute
`graph.py` directly unless you mean to trigger that; import it as a module instead
(`import research_assistant.graph`), which only builds the compiled graph and has no side effects.

To run the FastAPI server:

```
.venv/Scripts/python.exe -m uvicorn server.main:app --reload
```

`POST /research` takes a JSON body of `{"topic": "...", "config": {...AgentConfig fields...}}` and
returns the winning `ResearchStep`.

## Architecture

The graph is defined in `research_assistant/graph.py` using `langgraph.graph.StateGraph` over the
`ResearchState` TypedDict (`state.py`):

- **`validate_input`** → conditional edge **`route_after_validate`**: checks `topic` length
  (1–100 chars); routes to `error_print` (→ END) or into research on failure/success.
- **`initial_research`** (registered under the node id `"intial_research"` — note the typo is
  load-bearing, since `route_after_validate` returns that exact string as the routing target):
  calls `llm_initial_research`, seeding `state["initial_research"]`.
- **`llm_research`**: the core research-loop node. Builds its input from `initial_research` plus
  all prior `research_steps[*]["content"]`, and appends a new `ResearchStep` to `research_steps`
  (accumulated via `operator.add` on that field in `ResearchState`).
- **`critical_analysis`**: conditional edge off `llm_research`. Calls `research_done` and loops
  back to `llm_research` unless the research is done or `len(research_steps) >= retry_max_count`.
- **`give_final_respond`**: picks the `research_steps` entry with the highest `research_rate` as
  `final_response`.
- **`error_print`**: prints `error_message` and ends the run.

`ResearchStep` (`state.py`) is `{content, tools_used, research_rate}`; `ResearchState` carries
`topic`, `research_mode` (quick/thorough enum, for the US-8 stretch goal), `initial_research`,
`research_steps` (append-only list), `retry_max_count` (default 3, per US-5), `error_message`,
and `final_response`.

**Known landmine:** `nodes.py` imports a function named `llm_research` from `llm.model` *and*
defines its own node function also named `llm_research`. The module-level `def` shadows the
import in `nodes.py`'s namespace, so the node function's call to `llm_research(input)` resolves
to itself, not to `llm.model.llm_research` — an infinite-recursion bug. Be aware of this if you
rename or touch either function; the fix is to rename one of the two (e.g. import the model
function under an alias like `llm_research as generate_research_step`).

## Spec-driven development

If a request includes the flag **"USE SPEC"**, check `specs/` for a matching feature
folder before writing code. If one exists, follow it (`requirements.md` then
`implementation.md`); if not, create it from `specs/_template/` and fill in
`requirements.md` first. See `specs/README.md` for the full workflow.

## Sensitive files

`tokens.txt` at the repo root holds a live Anthropic API key in plain text. It is not referenced
by any code (no `os.getenv`/`os.environ` usage in `research_assistant/`), so it appears to be a
manually-pasted credential for local use. Never print/echo its contents, include it in commits,
or copy it into other files.
