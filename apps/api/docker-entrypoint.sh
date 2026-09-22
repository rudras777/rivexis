#!/bin/sh
set -eu

# Runtime containers must never receive schema-migration credentials.
# Run migrations through migrate-database.sh / the dedicated migration job first.
if [ -n "${RIVEXIS_MIGRATION_DATABASE_URL:-}" ]; then
  echo "Rivexis: refusing runtime startup because RIVEXIS_MIGRATION_DATABASE_URL is exposed to the application container" >&2
  exit 2
fi

exec "$@"
