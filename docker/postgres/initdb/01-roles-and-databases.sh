#!/bin/sh
# Runs once, on first initialisation of the postgres-data volume.
# Role split:
#   rehabmind_migrator - owns databases and schema; used only by Alembic.
#   rehabmind_app      - runtime role; DML only. Cannot alter schema, disable
#                      triggers, or bypass DB-level clinical safety checks.
set -eu

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname postgres \
  -v migrator_pw="$POSTGRES_MIGRATOR_PASSWORD" \
  -v app_pw="$POSTGRES_APP_PASSWORD" <<'SQL'
CREATE ROLE rehabmind_migrator LOGIN PASSWORD :'migrator_pw';
CREATE ROLE rehabmind_app LOGIN PASSWORD :'app_pw';
SQL

for db in rehabmind rehabmind_test; do
  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname postgres <<SQL
CREATE DATABASE $db OWNER rehabmind_migrator;
REVOKE ALL ON DATABASE $db FROM PUBLIC;
GRANT CONNECT, TEMPORARY ON DATABASE $db TO rehabmind_app;
SQL

  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$db" <<'SQL'
ALTER SCHEMA public OWNER TO rehabmind_migrator;
REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO rehabmind_app;
ALTER DEFAULT PRIVILEGES FOR ROLE rehabmind_migrator IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO rehabmind_app;
ALTER DEFAULT PRIVILEGES FOR ROLE rehabmind_migrator IN SCHEMA public
  GRANT USAGE, SELECT ON SEQUENCES TO rehabmind_app;
SQL
done
