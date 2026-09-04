-- Runs once, on first container init (docker-entrypoint-initdb.d), against the
-- database POSTGRES_DB already created for the postgres superuser. Creates a
-- non-superuser role the app connects as, scoped to just this database/schema.
CREATE ROLE research_assistant_app WITH LOGIN PASSWORD 'research_assistant_app';

GRANT CONNECT ON DATABASE research_assistant TO research_assistant_app;
GRANT ALL PRIVILEGES ON SCHEMA public TO research_assistant_app;

-- So tables/sequences created later (by Alembic migrations run as this role,
-- or by anything still run as postgres) stay usable by this role too.
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO research_assistant_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO research_assistant_app;
