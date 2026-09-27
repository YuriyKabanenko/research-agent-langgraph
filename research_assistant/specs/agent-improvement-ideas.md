# Agent improvement ideas (backlog)

Conceptual next steps for `research_assistant/`, beyond the current linear
plan → research → critique loop. These are ideas to pick from, not agreed
specs — if one gets picked up for real, give it its own folder under the
root `specs/` following `specs/README.md` (requirements.md → implementation.md)
rather than expanding this file into a spec itself.

Roughly ordered by learning payoff / effort ratio.

## 1. Structured output instead of regex extraction

Replace the `<research>...research_rate=X</research>` regex parsing
(`_extract_research_content` / `_extract_research_rate` in `nodes.py`) with
`.with_structured_output()` or tool-calling against a Pydantic schema. Same
graph shape, but it's the standard way to get structured data out of an LLM
call, and removes the regex + fallback-LLM-call complexity entirely.

## 2. Subgraphs

Pull the `llm_research` ↔ `critical_analysis` retry loop into its own
compiled subgraph, invoked as a single node from the outer graph. Teaches
graph composition — the same mechanism used to embed one agent inside
another.

## 3. Fan-out / fan-in (map-reduce research)

Instead of one linear research pass, split `research_plan` into subtopics,
research each in parallel branches, then merge/rank in a join node. Natural
next step after conditional edges; exercises parallel-branch state merging
(`operator.add` reducers already used for `research_steps` would need to
handle concurrent writes).

## 4. Supervisor / multi-agent pattern

A router node that delegates to specialized sub-agents (e.g. a "web
researcher" vs. a "critic" vs. a "summarizer", each its own compiled graph)
instead of one node doing everything. This is closer to what "multi-agent"
usually means on a CV.

## 5. Human-in-the-loop (`interrupt()`)

Pause before `give_final_respond` (or after a low-rated critique) for a
human to approve/edit, then resume. Requires understanding LangGraph's
checkpointing/resume model, not just linear execution.

## 6. LangGraph checkpointer instead of hand-rolled Postgres persistence

Worth understanding even if the server keeps its own `Research` table for
the job-status API — it's the idiomatic state-persistence mechanism and a
prerequisite for #5.

## 7. Streaming

Stream node-by-node (or token-by-token) progress to the frontend instead of
the current fire-and-forget `BackgroundTasks` job that the client polls for
status.

---

Recommended starting point: **#3, fan-out/fan-in parallel research** — it
builds directly on conditional-edge knowledge already in place, and reads
well as "designed a map-reduce research pipeline" rather than just a retry
loop.
