#!/usr/bin/env bash
set -euo pipefail

PG_BIN=$(ls -d /usr/lib/postgresql/*/bin | head -1)
export PATH="$PG_BIN:$PATH"

# An external DATABASE_URL means someone brought their own Postgres, so skip the
# bundled one entirely.
if [ -z "${EPOINT_DATABASE_URL:-}" ]; then
  export EPOINT_DATABASE_URL="postgresql+psycopg://epoint:epoint@127.0.0.1:5432/epoint_sandbox"

  if [ ! -s "$PGDATA/PG_VERSION" ]; then
    echo "Initialising bundled Postgres"
    su postgres -c "initdb -D $PGDATA -U epoint --auth=trust" > /dev/null
    echo "listen_addresses = '127.0.0.1'" >> "$PGDATA/postgresql.conf"
  fi

  su postgres -c "pg_ctl -D $PGDATA -o '-p 5432' -w -t 60 start" > /dev/null

  if ! su postgres -c "psql -U epoint -p 5432 -lqt" | cut -d'|' -f1 | grep -qw epoint_sandbox; then
    su postgres -c "createdb -U epoint -p 5432 epoint_sandbox"
  fi

  shutdown() {
    echo "Stopping Postgres"
    su postgres -c "pg_ctl -D $PGDATA -m fast stop" || true
  }
  trap shutdown EXIT INT TERM
fi

echo "Applying migrations"
alembic upgrade head

echo "Starting epoint sandbox on :${EPOINT_PORT}"
exec uvicorn epoint_sandbox.main:app \
  --host 0.0.0.0 \
  --port "${EPOINT_PORT}" \
  --no-access-log
