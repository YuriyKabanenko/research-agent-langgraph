# Feature Spec: <feature name>

- **Status:** Draft

## Problem

What's missing, broken, or needed, and why now. 2-4 sentences.

## Goal

One sentence: what "done" looks like, from the end user's (or, for internal/technical
features, the next developer's) perspective.

## Non-Goals

What this feature explicitly will NOT do. This is what stops scope from creeping while
you're in implementation.md.

## Acceptance Criteria

Numbered, testable, unambiguous. Prefer this shape (EARS-style):

- **AC-1:** WHEN <trigger/input>, the system SHALL <observable, checkable behavior>.
- **AC-2:** IF <condition>, THEN the system SHALL <behavior>.
- **AC-3:** ...

If you can't describe how you'd manually verify an AC by running the graph/server, it's
not specific enough yet — rewrite it.

## Open Questions

Anything undecided that blocks moving to implementation.md. Resolve or explicitly defer
each one (with a reason) before proceeding.
