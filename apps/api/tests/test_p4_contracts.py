from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def _load_migration(name: str):
    path = ROOT / "apps" / "api" / "alembic" / "versions" / name
    spec = importlib.util.spec_from_file_location("migration_under_test", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_organization_member_rls_policy_is_non_recursive():
    migration = _load_migration("0003_production_schema_rls.py")
    policy = migration._rls_policy_sql("organization_members")
    assert policy is not None
    assert "rivexis.organization_id" in policy
    assert "rivexis.organization_role" in policy
    assert "SELECT organization_id FROM organization_members" not in policy


def test_provider_requests_are_force_rls_protected():
    source = (ROOT / "apps" / "api" / "alembic" / "versions" / "0005_provider_runtime_telemetry.py").read_text()
    assert 'ALTER TABLE "provider_requests" ENABLE ROW LEVEL SECURITY' in source
    assert 'ALTER TABLE "provider_requests" FORCE ROW LEVEL SECURITY' in source
    assert "rivexis_tenant_isolation" in source


def test_container_uses_non_bypass_application_role_and_dedicated_migration_job():
    compose = (ROOT / "infrastructure" / "docker-compose.yml").read_text()
    roles = (ROOT / "infrastructure" / "postgres" / "001_roles.sql").read_text()
    dockerfile = (ROOT / "apps" / "api" / "Dockerfile").read_text()
    entrypoint = (ROOT / "apps" / "api" / "docker-entrypoint.sh").read_text()
    migrate = (ROOT / "apps" / "api" / "migrate-database.sh").read_text()
    assert "rivexis_app:" in compose
    assert "RIVEXIS_PROVIDER_CONTROL_BACKEND: redis" in compose
    assert "NOBYPASSRLS" in roles and "NOSUPERUSER" in roles
    assert 'ENTRYPOINT ["./docker-entrypoint.sh"]' in dockerfile
    assert "alembic upgrade head" not in entrypoint
    assert "RIVEXIS_MIGRATION_DATABASE_URL" in migrate
    assert "alembic upgrade head" in migrate
    assert 'entrypoint: ["./migrate-database.sh"]' in compose
    assert 'migrate: {condition: service_completed_successfully}' in compose
    assert ".[production]" in dockerfile or ".[full]" in dockerfile
