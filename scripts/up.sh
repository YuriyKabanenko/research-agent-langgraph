#!/usr/bin/env bash
# One entrypoint for the whole stack: rebuild images, apply Alembic migrations, and
# start db -> migrate -> back -> front, waiting until everything is up.
#
#   ./scripts/up.sh
#
# The migration step is the one-shot `migrate` service in docker-compose.yml, so a
# plain `docker compose up` runs it too - this script just adds the rebuild, the
# wait, and diagnostics when something fails.
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
  echo "error: .env not found at the repo root (see CLAUDE.md > Environment)" >&2
  exit 1
fi

echo "==> Rebuilding images and starting the stack (db -> migrate -> back -> front)"
# --wait blocks until the listed services are running/healthy; their dependencies
# (db, migrate) are started and awaited through depends_on. migrate isn't listed
# because it's supposed to exit, not stay running.
if ! docker compose up --detach --build --wait --wait-timeout 300 back front; then
  echo >&2
  echo "!! The stack failed to come up. Service states:" >&2
  docker compose ps --all >&2
  echo >&2
  echo "!! Last log lines from migrate and back:" >&2
  docker compose logs --tail 40 migrate back >&2
  exit 1
fi

echo
docker compose ps
echo
echo "Frontend:  http://localhost:5173"
echo "API docs:  http://localhost:8000/docs"
echo "Logs:      docker compose logs -f back"
echo "Stop:      docker compose down"
