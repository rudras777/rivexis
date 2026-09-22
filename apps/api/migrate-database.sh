#!/bin/sh
set -eu

if [ -z "${RIVEXIS_MIGRATION_DATABASE_URL:-}" ]; then
  echo "Rivexis migration: RIVEXIS_MIGRATION_DATABASE_URL is required" >&2
  exit 2
fi

# Scope DDL authority to this one-shot process only.
echo "Rivexis migration: applying Alembic migrations with dedicated migration role"
DATABASE_URL="$RIVEXIS_MIGRATION_DATABASE_URL" alembic upgrade head
python ./configure-alert-worker-role.py
