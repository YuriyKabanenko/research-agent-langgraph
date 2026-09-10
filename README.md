# Self-Checking Research Assistant

A research agent that takes a topic, drafts an answer using an LLM with tools, 
critiques its own draft, and automatically retries the research step if the critique isn't
good enough — up to a configurable retry limit. Built with LangGraph, wrapped in a FastAPI service
with auth and persistence, and fronted by a React SPA.

## How it works

1. **Research** — the agent researches the topic (calling out to web search / date tools as
   needed) and drafts an answer.
2. **Critique** — a separate step rates the draft against a configurable quality threshold.
3. **Retry or finish** — if the critique isn't good enough, the agent loops back and researches
   again, informed by the critique, up to a max number of attempts. Otherwise (or once attempts
   run out), it returns the best-rated draft as the final answer.

## Project layout

- **`research_assistant/`** — the LangGraph agent itself (state graph, prompts, LLM/tool calls).
  Runnable standalone as a CLI.
- **`server/`** — a FastAPI app wrapping the agent with auth, Postgres-backed persistence (users,
  agents, agent configs, research runs), and an async job API. See `server/README.md` for the full
  endpoint list.
- **`frontend/`** — a Vite + React + TypeScript SPA that talks to the server.

## Quick start

Everything via Docker Compose (Postgres + API + frontend):

```
docker compose up -d
```

Frontend at `http://localhost:5173`, API docs at `http://localhost:8000/docs`.

Or run the agent alone from the CLI:

```
.venv/Scripts/python.exe -m research_assistant.main "your topic here"
```

See `CLAUDE.md` for full environment setup (virtualenv, `.env` variables, editable installs) and
architecture notes, and `server/README.md` for the API reference.

## Tech stack

LangGraph / LangChain (Anthropic, OpenAI, and Google model support) for the agent, Tavily for web
search, FastAPI + SQLAlchemy (async) + Alembic + Postgres for the backend, React + TypeScript +
MUI + TanStack Query + Zustand for the frontend.
