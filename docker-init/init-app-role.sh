#!/bin/sh
# Runs once, on first container init (docker-entrypoint-initdb.d), against the
# database POSTGRES_DB already created for the postgres superuser. Creates a
# non-superuser role the app connects as, scoped to just this database/schema.
# APP_DB_USER/APP_DB_PASSWORD come from the db service's environment (see .env
# and docker-compose.yml) so the credentials aren't hardcoded here.
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE ROLE "$APP_DB_USER" WITH LOGIN PASSWORD '$APP_DB_PASSWORD';

    GRANT CONNECT ON DATABASE "$POSTGRES_DB" TO "$APP_DB_USER";
    GRANT ALL PRIVILEGES ON SCHEMA public TO "$APP_DB_USER";

    -- So tables/sequences created later (by Alembic migrations run as this role,
    -- or by anything still run as postgres) stay usable by this role too.
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO "$APP_DB_USER";
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO "$APP_DB_USER";
EOSQL
