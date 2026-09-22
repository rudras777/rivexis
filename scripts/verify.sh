#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/apps/api"
python -m compileall -q rivexis_api tests
PYTHONPATH="$ROOT/apps/api" pytest -q
cd "$ROOT"
python scripts/check_invariants.py
PYTHONPATH="$ROOT/apps/api" python scripts/check_deployment_registry.py
PYTHONPATH="$ROOT/apps/api" python scripts/check_registry_governance.py
python scripts/check_registry_attestations.py
PYTHONPATH="$ROOT/apps/api" python scripts/certify_otlp_export.py
python scripts/certify_registry_upstream.py
python scripts/check_migrations.py
python scripts/check_schema_contract.py
if [ -n "${RIVEXIS_RLS_ADMIN_DATABASE_URL:-}" ] && [ -n "${RIVEXIS_RLS_APP_DATABASE_URL:-}" ] && [ -n "${RIVEXIS_RLS_WORKER_DATABASE_URL:-}" ]; then
  python scripts/certify_postgres_rls.py
else
  echo "SKIP PostgreSQL RLS adversarial certification: set RIVEXIS_RLS_ADMIN_DATABASE_URL, RIVEXIS_RLS_APP_DATABASE_URL and RIVEXIS_RLS_WORKER_DATABASE_URL"
fi
PYTHONPATH="$ROOT/apps/api" python scripts/certify_redis_distributed.py
PYTHONPATH="$ROOT/apps/api" python scripts/certify_live_providers.py
PYTHONPATH="$ROOT/apps/api" python scripts/certify_protocol_adapters.py
PYTHONPATH="$ROOT/apps/api" python scripts/certify_protocol_history.py
PYTHONPATH="$ROOT/apps/api" python scripts/check_retention_policy.py
python scripts/certify_backup_restore.py
python scripts/secret_scan.py
node scripts/check_frontend_ast.js
python scripts/certify_dependency_gates.py

python scripts/create_certification_execution_manifest.py
PYTHONPATH="$ROOT/apps/api" python scripts/verify_certification_execution_manifest.py
RIVEXIS_CERT_RUNNER_PROFILE=local PYTHONPATH="$ROOT/apps/api" python scripts/certify_staging_suite.py
PYTHONPATH="$ROOT/apps/api" python scripts/verify_staging_evidence.py --profile local
PYTHONPATH="$ROOT/apps/api" python scripts/certify_release_bundle.py \
  --manifest "$ROOT/certification-execution-manifest.json" \
  --report "$ROOT/certification-reports/local.json"
PYTHONPATH="$ROOT/apps/api" python scripts/verify_release_bundle.py \
  "$ROOT/release-certification-bundle.json" \
  --manifest "$ROOT/certification-execution-manifest.json"
