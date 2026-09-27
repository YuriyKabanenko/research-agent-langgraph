# Feature Spec: human-in-the-loop review of the final draft

- **Status:** Implemented

## Problem

The research loop decides by itself when a draft is good enough: the AI critique
(`critical_analysis`) plus `retry_max_count` are the only gatekeepers, and the user only
sees the result once it's already `completed`. If the answer misses what the user
actually wanted, their only option is to start a new research from scratch and pay for
a full run again. Backlog item #5 in `research_assistant/specs/agent-improvement-ideas.md`.

## Goal

Before a single-topic research is finalized, the user sees the draft and either approves
it (it becomes the final answer) or sends it back with feedback (the agent revises it and
asks again). A paused research survives a server restart.

## Non-Goals

- **No review on the complex-topic (fan-out) path.** `split_topic → subtopic_worker →
  combine_subtopics → END` never reaches `give_final_respond` and stays fully automatic.
- **No per-subtopic review** or interrupts inside parallel `subtopic_worker` branches.
- **No limit on how many times the user can send a draft back.**
- **No editing the draft text directly.** The user gives feedback and the agent rewrites.
  Hand-editing can be added later as a third decision type.
- **No recovery of runs stuck in `running` after a crash** (an existing issue that isn't
  specific to HITL). Checkpoints make it possible later, but it isn't part of this spec.
- **No timeout / auto-approve** for a research left in `awaiting_review`.
- **No streaming or push notifications.** The frontend learns about the new status the
  same way it does today (manual refresh on `ResearchesPage`).
- **The server's `Research` table stays.** The LangGraph checkpointer is added next to
  it for graph-state persistence, not as a replacement for the job-status API.

## Acceptance Criteria

### Graph behaviour

- **AC-1:** WHEN the single-topic `research_loop` finishes, the graph SHALL pause
  before `give_final_respond` and expose the candidate draft (`content`, `tools_used`,
  `research_rate`) as the interrupt payload. No further LLM calls SHALL happen while
  paused.
- **AC-2:** WHEN the graph is paused for the first time, the candidate SHALL be the
  highest-rated entry of `research_steps` (the same one `give_final_respond` picks
  today).
- **AC-3:** WHEN the user approves, `final_response` SHALL be **exactly** the candidate
  the user was shown, and the run SHALL end through `give_final_respond`.
- **AC-4:** WHEN the user rejects with feedback, the feedback SHALL be used as the
  revision instruction for the next `llm_research` call (it reaches the prompt the same
  way an AI critique does today), and the graph SHALL pause again with a new candidate.
- **AC-5:** WHEN the graph pauses after a human-requested revision, the candidate SHALL
  be the **latest** research step, even if an earlier step has a higher `research_rate`.
- **AC-6:** WHEN the topic is judged complex (split into subtopics), the graph SHALL
  run to completion without pausing, exactly as it does today.
- **AC-7:** WHEN either CLI (`research_assistant/main.py`, `research_assistant/graph.py`
  `main()`) hits a pause, it SHALL
  print the candidate, read approve/feedback from stdin, and resume until the run
  completes.

### Persistence

- **AC-8:** Graph state SHALL be checkpointed to the app's Postgres database, with the
  `Research.id` as the `thread_id`.
- **AC-9:** IF the server is restarted while a research is `awaiting_review`, THEN
  approving or rejecting it after the restart SHALL resume it from where it paused
  (no repeat of research already done) and finish normally.
- **AC-10:** WHEN a research is deleted via `DELETE /research/{id}`, its checkpoint
  data SHALL be deleted too.
- **AC-11:** `alembic revision --autogenerate` SHALL NOT generate operations against
  the checkpointer's own tables.

### Server API

- **AC-12:** WHEN a run pauses, the `Research` row SHALL get status `awaiting_review`,
  and `GET /research/{id}` SHALL return the candidate in the existing `research`,
  `tools_used` and `research_rate` fields.
- **AC-13:** WHEN `POST /research/{id}/review` is called with `{"approved": true}` on
  the caller's own research in `awaiting_review`, the system SHALL respond `202`, move it
  to `running`, and resume the graph in the background. It ends as `completed` with the
  approved draft as its result.
- **AC-14:** WHEN `POST /research/{id}/review` is called with
  `{"approved": false, "feedback": "<non-empty>"}` under the same conditions, the system
  SHALL respond `202`, move it to `running`, and resume the graph with that feedback. It
  ends as `awaiting_review` again with the revised candidate.
- **AC-15:** IF `approved` is `false` and `feedback` is missing or blank, THEN the system
  SHALL respond `422` and SHALL NOT change the research or resume the graph.
- **AC-16:** IF the research doesn't exist or belongs to another user, THEN the system
  SHALL respond `404`.
- **AC-17:** IF the research is not in `awaiting_review`, THEN the system SHALL respond
  `409` and SHALL NOT resume the graph. This includes a second, near-simultaneous
  submit of the same review (double-click): exactly one of them resumes the graph.
- **AC-18:** The resumed run SHALL use the agent config (model, BYOK API key, knobs)
  of the agent the research was created with, taken from the `Research` row, never from
  the request body.
- **AC-19:** The BYOK API key SHALL NOT be written into checkpoint data.

### Frontend

- **AC-20:** A research in `awaiting_review` SHALL show a distinct status chip on
  `ResearchesPage`.
- **AC-21:** Opening a research in `awaiting_review` SHALL show the candidate draft
  with an **Approve** action and a feedback field with a **Send back** action. Send back
  SHALL be disabled while the feedback is blank.
- **AC-22:** After either action succeeds, the research SHALL show as `running` without
  a manual page reload. An error response (`409`/`422`/`404`) SHALL be shown to the user.

## Open Questions

None blocking. Decided while drafting:

- **Where does the pending draft live for the API?** In the existing `Research` columns
  (`resarch`/`tools_used`/`research_rate`), not read back from the checkpoint on every
  `GET`. The frontend already renders those fields.
- **How many revisions per piece of feedback?** Whatever the existing loop does. Usually
  exactly one, because `route_after_analysis` stops once `len(research_steps) >=
  retry_max_count`. No separate counter.
- **Postgres driver:** the checkpointer uses psycopg 3 next to the app's asyncpg. They
  are two independent connection pools against the same database.
