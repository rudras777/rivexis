from __future__ import annotations

import tomllib
from pathlib import Path

from fastapi.testclient import TestClient

import rivexis_api
from rivexis_api.main import app
from rivexis_api.version import API_VERSION, RELEASE_CODENAME


def test_release_version_has_one_runtime_source_of_truth() -> None:
    root = Path(__file__).resolve().parents[3]
    project = tomllib.loads((root / "apps" / "api" / "pyproject.toml").read_text())
    assert API_VERSION == "3.4.3"
    assert RELEASE_CODENAME == "P37"
    assert rivexis_api.__version__ == API_VERSION
    assert project["project"]["version"] == API_VERSION
    assert app.version == API_VERSION


def test_health_reports_api_version() -> None:
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["api_version"] == API_VERSION


def test_release_signing_workflow_uses_detached_single_key_ceremony() -> None:
    root = Path(__file__).resolve().parents[3]
    assert not (root / "scripts" / "create_release_attestation.py").exists()
    for name in (
        "create_release_signing_request.py",
        "sign_release_request.py",
        "assemble_release_attestation.py",
        "verify_release_attestation.py",
        "advance_release_lineage.py",
        "verify_release_lineage.py",
    ):
        assert (root / "scripts" / name).is_file()


def test_operator_configuration_and_current_docs_match_release_identity() -> None:
    root = Path(__file__).resolve().parents[3]
    env_text = (root / ".env.example").read_text()
    assert f"RIVEXIS_RELEASE_VERSION={API_VERSION}" in env_text
    for relative in (
        "docs/RELEASE_TRUST_POLICY.md",
        "docs/STAGING_CERTIFICATION.md",
        "docs/BROWSER_CERTIFICATION.md",
        "docs/VERIFICATION_RESULTS.md",
        "FINAL_ENGINEERING_REPORT.md",
    ):
        first_lines = "\n".join((root / relative).read_text().splitlines()[:4])
        assert RELEASE_CODENAME in first_lines, f"{relative} is not labeled for {RELEASE_CODENAME}"


def test_release_operator_cli_labels_match_current_release() -> None:
    root = Path(__file__).resolve().parents[3]
    for relative in (
        "scripts/create_release_signing_request.py",
        "scripts/sign_release_request.py",
        "scripts/assemble_release_attestation.py",
        "scripts/verify_release_attestation.py",
        "scripts/advance_release_lineage.py",
        "scripts/verify_release_lineage.py",
        "scripts/certification_plan.py",
        "scripts/verify_certification_execution_manifest.py",
    ):
        text = (root / relative).read_text()
        assert RELEASE_CODENAME in text, f"{relative} does not identify {RELEASE_CODENAME}"


def test_container_migrations_are_one_shot_and_not_exposed_to_runtime() -> None:
    root = Path(__file__).resolve().parents[3]
    dockerfile = (root / "apps" / "api" / "Dockerfile").read_text()
    entrypoint = (root / "apps" / "api" / "docker-entrypoint.sh").read_text()
    migrate = (root / "apps" / "api" / "migrate-database.sh").read_text()
    compose = (root / "infrastructure" / "docker-compose.yml").read_text()
    assert 'ENTRYPOINT ["./docker-entrypoint.sh"]' in dockerfile
    assert 'COPY migrate-database.sh ./migrate-database.sh' in dockerfile
    assert 'COPY configure-alert-worker-role.py ./configure-alert-worker-role.py' in dockerfile
    assert 'alembic upgrade head' not in entrypoint
    assert 'refusing runtime startup' in entrypoint
    assert 'DATABASE_URL="$RIVEXIS_MIGRATION_DATABASE_URL" alembic upgrade head' in migrate
    assert 'migrate:' in compose
    assert 'entrypoint: ["./migrate-database.sh"]' in compose
    assert 'migrate: {condition: service_completed_successfully}' in compose
    assert compose.count('RIVEXIS_MIGRATION_DATABASE_URL:') == 1
    assert 'DATABASE_URL: postgresql+psycopg://rivexis_app:' in compose
    assert 'DATABASE_URL: postgresql+psycopg://rivexis_alert_worker:' in compose


def test_local_runtime_postgres_role_has_no_schema_creation_authority() -> None:
    root = Path(__file__).resolve().parents[3]
    roles = (root / "infrastructure" / "postgres" / "001_roles.sql").read_text()
    assert 'NOSUPERUSER' in roles and 'NOBYPASSRLS' in roles
    assert 'GRANT USAGE ON SCHEMA public TO rivexis_app' in roles
    assert 'GRANT USAGE, CREATE ON SCHEMA public TO rivexis_app' not in roles
    assert 'ALTER DEFAULT PRIVILEGES FOR ROLE rivexis_admin' in roles
    assert 'GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO rivexis_app' in roles


def test_deployment_template_exposes_separate_migration_url() -> None:
    root = Path(__file__).resolve().parents[3]
    env_text = (root / ".env.example").read_text()
    assert "RIVEXIS_MIGRATION_DATABASE_URL=" in env_text


def test_deployment_template_does_not_enable_runtime_schema_creation() -> None:
    root = Path(__file__).resolve().parents[3]
    env_text = (root / ".env.example").read_text()
    assert "RIVEXIS_AUTO_CREATE_SCHEMA=false" in env_text
    db_text = (root / "apps" / "api" / "rivexis_api" / "services" / "db.py").read_text()
    assert "RIVEXIS_AUTO_CREATE_SCHEMA is SQLite-only" in db_text


def test_non_sqlite_runtime_refuses_orm_auto_create(monkeypatch) -> None:
    import rivexis_api.services.db as db

    class _Dialect:
        name = "postgresql"

    class _Engine:
        dialect = _Dialect()

    monkeypatch.setattr(db, "engine", _Engine())
    monkeypatch.setenv("RIVEXIS_AUTO_CREATE_SCHEMA", "true")
    called = False

    def _unexpected_create_all(_engine) -> None:
        nonlocal called
        called = True

    monkeypatch.setattr(db.Base.metadata, "create_all", _unexpected_create_all)
    import pytest
    with pytest.raises(RuntimeError, match="SQLite-only"):
        db.init_db()
    assert called is False


def test_non_sqlite_runtime_never_calls_create_all_when_flag_is_false(monkeypatch) -> None:
    import rivexis_api.services.db as db

    class _Dialect:
        name = "postgresql"

    class _Engine:
        dialect = _Dialect()

    monkeypatch.setattr(db, "engine", _Engine())
    monkeypatch.setenv("RIVEXIS_AUTO_CREATE_SCHEMA", "false")
    called = False

    def _unexpected_create_all(_engine) -> None:
        nonlocal called
        called = True

    monkeypatch.setattr(db.Base.metadata, "create_all", _unexpected_create_all)
    db.init_db()
    assert called is False


def test_alert_worker_uses_dedicated_least_privilege_bypassrls_role() -> None:
    root = Path(__file__).resolve().parents[3]
    roles = (root / "infrastructure" / "postgres" / "001_roles.sql").read_text()
    compose = (root / "infrastructure" / "docker-compose.yml").read_text()
    migrate = (root / "apps" / "api" / "migrate-database.sh").read_text()
    configurator = (root / "apps" / "api" / "configure-alert-worker-role.py").read_text()
    worker = (root / "apps" / "api" / "rivexis_api" / "workers" / "alerts.py").read_text()

    assert "rivexis_alert_worker" in roles
    assert "BYPASSRLS" in roles
    assert "NOSUPERUSER" in roles
    assert "DATABASE_URL: postgresql+psycopg://rivexis_alert_worker:" in compose
    assert "DATABASE_URL: postgresql+psycopg://rivexis_app:" in compose
    assert "RIVEXIS_ALERT_WORKER_ROLE: rivexis_alert_worker" in compose
    assert "python ./configure-alert-worker-role.py" in migrate
    assert "GRANT SELECT, UPDATE ON TABLE alerts" in configurator
    assert "REVOKE ALL PRIVILEGES ON ALL TABLES" in configurator
    assert "validate_alert_worker_database_role" in worker


def test_postgres_rls_certification_requires_worker_database_identity() -> None:
    root = Path(__file__).resolve().parents[3]
    env_text = (root / ".env.example").read_text()
    profile_text = (root / "apps" / "api" / "rivexis_api" / "certification_profiles.py").read_text()
    cert_text = (root / "scripts" / "certify_postgres_rls.py").read_text()
    assert "RIVEXIS_RLS_WORKER_DATABASE_URL=" in env_text
    assert "RIVEXIS_RLS_WORKER_DATABASE_URL" in profile_text
    assert "least-privilege BYPASSRLS alert worker" in cert_text


def test_alert_worker_runtime_logs_are_payload_free() -> None:
    root = Path(__file__).resolve().parents[3]
    worker = (root / "apps" / "api" / "rivexis_api" / "workers" / "alerts.py").read_text()
    cli = (root / "scripts" / "process_alert_queue.py").read_text()
    delivery = (root / "apps" / "api" / "rivexis_api" / "services" / "alert_delivery.py").read_text()
    assert '"results":results' not in worker
    assert '"error":str(exc)' not in worker
    assert '_emit_cycle_log(results)' in worker
    assert 'delivery_error_type(exc)' in worker
    assert 'delivery_log_summary(results)' in worker
    assert 'delivery_log_summary([result])' in cli
    assert 'delivery_error_type(exc)' in cli
    assert 'json.dumps(process_due_alerts(' not in cli
    assert 'def delivery_log_summary(' in delivery
    assert 'def delivery_error_type(' in delivery


def test_production_configuration_is_fail_closed_and_provider_diagnostics_are_authenticated() -> None:
    root = Path(__file__).resolve().parents[3]
    config = (root / "apps" / "api" / "rivexis_api" / "core" / "config.py").read_text()
    main = (root / "apps" / "api" / "rivexis_api" / "main.py").read_text()
    env_text = (root / ".env.example").read_text()
    assert "validate_runtime_security()" in main
    assert "RIVEXIS_AUTH_SECRET must be a non-placeholder secret of at least 32 characters in production" in config
    assert "ENABLE_DEMO_ADAPTER must be false in production" in config
    assert "ENABLE_DEMO_ADAPTER=false" in env_text
    assert "def providers(user=Depends(current_user))" in main
    assert "def provider_status(deep:bool=Query(False),chain:str=Query(\"ethereum\"),user=Depends(current_user))" in main
    assert "def provider_resolve(category:str,deep:bool=Query(False),allow_demo:bool=Query(False),chain:str=Query(\"ethereum\"),user=Depends(current_user))" in main
    assert "def provider(provider_id:str,deep:bool=Query(False),chain:str=Query(\"ethereum\"),user=Depends(current_user))" in main
