# Feature Spec: user registration and basic auth

- **Status:** Implemented

## Problem

FastAPI has no notion of "who is calling" — every request is anonymous. The DB already
has a `users` table and `agents` relate to it, but nothing on the API surface creates a
user or ties a request to one. `POST /research` runs for anyone who can reach the server.

## Goal

A client can call `POST /register` to obtain an identity (a user row + an opaque token),
and `POST /research` refuses to run unless the caller presents that token.

## Non-Goals

- No passwords, no login endpoint. `/register` is identity issuance, not account creation
  with credentials — matches the "basic auth identity layer" the client asked for.
- No token refresh/rotation/expiry. A token is valid until deleted from the DB.
- No roles/permissions (RBAC) — authenticated is authenticated, there's only one tier.
- No rate limiting, no HTTPS enforcement (assumed handled by whatever sits in front of
  uvicorn in a real deployment).
- Registering does not require the caller to already have a token (it's how you get one).

## Acceptance Criteria

- **AC-1:** WHEN a client calls `POST /register` with a JSON body `{"name": "<1-50 chars>"}`,
  the system SHALL create a new `users` row and a new auth token for it, and respond `201`
  with `{"user_id": "<uuid>", "name": "<name>", "token": "<opaque string>"}`.
- **AC-2:** IF `name` is missing, empty, or longer than 50 characters, THEN `POST /register`
  SHALL respond `422` and SHALL NOT create a user or token.
- **AC-3:** WHEN `POST /research` is called with no `Authorization` header (or one that
  isn't `Bearer <token>`), the system SHALL respond `401` and SHALL NOT invoke the graph.
- **AC-4:** WHEN `POST /research` is called with `Authorization: Bearer <token>` where
  `<token>` doesn't match any issued token, the system SHALL respond `401` and SHALL NOT
  invoke the graph.
- **AC-5:** WHEN `POST /research` is called with a valid, previously-issued token, the
  system SHALL resolve it to the user that owns it and proceed exactly as it does today
  (existing topic/config validation and error handling unchanged).
- **AC-6:** The plaintext token SHALL appear in the `POST /register` response body and
  nowhere else — it SHALL NOT be persisted to the database or written to logs. Only a
  one-way hash of it is stored, so a DB read (backup, dump, leaked credential) does not
  hand out usable tokens.
- **AC-7:** Calling `POST /register` again (same or different name) SHALL create an
  independent user + token, never reuse or look up an existing user by name — there is no
  concept of "already registered," only "issue me an identity."

## Open Questions

None — resolved above (no passwords/expiry/roles, register is idempotent-free identity
issuance, tokens hashed at rest).
