# Spec-driven workflow for this repo

Each concrete change to the graph/state/nodes/server gets its own small spec before
any code is written, so implementation always traces back to an explicit, agreed-upon
decision instead of being made up on the fly while editing files.

## Workflow

1. Copy `specs/_template/` to `specs/<feature-slug>/` (e.g. `specs/web-search-tool/`).
2. Fill in **requirements.md** completely — what's wanted and how to tell it's done. Do
   not start implementation.md until the acceptance criteria are concrete and testable —
   if you can't tell whether an AC passed or failed just by reading it, it's not done yet.
3. Fill in **implementation.md** — how it gets built: approach, alternatives considered,
   state/graph/node changes, affected files, risks, and a task checklist. Get agreement
   on the approach before writing code — this is the step that catches a bad approach
   before it's implemented.
4. Implement task by task, checking items off the checklist in implementation.md.
   Reviewing and testing the result is the user's part, not the agent's — don't run the
   app/tests to verify acceptance criteria; stop once the code for each task is written.
5. Update `Status:` in requirements.md as you go (Draft → Approved → In Progress →
   Implemented). Only the user moves it to Done, once they've reviewed and tested it.
