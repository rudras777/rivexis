from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

import rivexis_api.services.db as db
from rivexis_api.services.postgres_identity import validate_standalone_service_role


class _Dialect:
    def __init__(self, name: str):
        self.name = name


class _Result:
    def __init__(self, *, rows=None):
        self._rows = rows or []

    def mappings(self):
        return self

    def all(self):
        return self._rows


class _Connection:
    def __init__(self, rows=None):
        self.rows = rows or []

    def execute(self, statement):
        sql = str(statement)
        if "information_schema.tables" in sql:
            return _Result(rows=self.rows)
        raise AssertionError(sql)


class _ConnectContext:
    def __init__(self, conn):
        self.conn = conn

    def __enter__(self):
        return self.conn

    def __exit__(self, exc_type, exc, tb):
        return False


class _Engine:
    def __init__(self, name: str, conn=None):
        self.dialect = _Dialect(name)
        self.conn = conn

    def connect(self):
        return _ConnectContext(self.conn)


def _state(*, bypass: bool = False) -> dict[str, object]:
    return {
        "current_user": "rivexis_service",
        "session_user": "rivexis_service",
        "rolsuper": False,
        "rolbypassrls": bypass,
        "rolcreatedb": False,
        "rolcreaterole": False,
        "rolreplication": False,
        "rolinherit": False,
        "rolcanlogin": True,
        "parent_role_memberships": [],
        "database_create": False,
        "schema_create": False,
        "owned_relations": [],
    }


def _rows(*, alerts=(True, False, True, False), other=(False, False, False, False)):
    return [
        {"table_name": "alerts", "can_select": alerts[0], "can_insert": alerts[1], "can_update": alerts[2], "can_delete": alerts[3]},
        {"table_name": "analyses", "can_select": other[0], "can_insert": other[1], "can_update": other[2], "can_delete": other[3]},
    ]


def test_standalone_application_identity_contract_accepts_exact_role() -> None:
    validate_standalone_service_role(_state(), label="application runtime", require_bypassrls=False)


def test_standalone_worker_identity_contract_accepts_exact_role() -> None:
    validate_standalone_service_role(_state(bypass=True), label="alert worker", require_bypassrls=True)


@pytest.mark.parametrize(
    ("field", "value", "match"),
    [
        ("session_user", "login_parent", "session authorization / SET ROLE"),
        ("rolsuper", True, "SUPERUSER"),
        ("rolbypassrls", True, "NOBYPASSRLS"),
        ("rolcreatedb", True, "CREATEDB"),
        ("rolcreaterole", True, "CREATEROLE"),
        ("rolreplication", True, "REPLICATION"),
        ("rolinherit", True, "NOINHERIT"),
        ("rolcanlogin", False, "LOGIN"),
        ("parent_role_memberships", ["neon_superuser"], "parent-role membership / SET ROLE"),
        ("database_create", True, "database CREATE"),
        ("schema_create", True, "schema CREATE"),
        ("owned_relations", ["analyses"], "own application relations"),
    ],
)
def test_application_identity_rejects_direct_and_transitive_privilege_paths(field, value, match) -> None:
    state = deepcopy(_state())
    state[field] = value
    with pytest.raises(RuntimeError, match=match):
        validate_standalone_service_role(state, label="application runtime", require_bypassrls=False)


def test_worker_identity_rejects_missing_bypassrls() -> None:
    with pytest.raises(RuntimeError, match="requires BYPASSRLS"):
        validate_standalone_service_role(_state(bypass=False), label="alert worker", require_bypassrls=True)


def test_application_validator_skips_postgres_contract_for_sqlite(monkeypatch) -> None:
    monkeypatch.setattr(db, "engine", _Engine("sqlite"))
    assert db.validate_application_database_role()["mode"] == "non_postgres"


def test_worker_validator_skips_postgres_contract_for_sqlite(monkeypatch) -> None:
    monkeypatch.setattr(db, "engine", _Engine("sqlite"))
    assert db.validate_alert_worker_database_role()["mode"] == "non_postgres"


def test_application_validator_uses_standalone_non_bypass_contract(monkeypatch) -> None:
    conn = _Connection()
    monkeypatch.setattr(db, "engine", _Engine("postgresql", conn))
    monkeypatch.setattr(db, "inspect_postgres_role_security_state", lambda _conn: _state())
    result = db.validate_application_database_role()
    assert result == {
        "dialect": "postgresql",
        "validated": True,
        "role": "rivexis_service",
        "bypassrls": False,
        "parent_role_memberships": 0,
    }


def test_worker_validator_accepts_only_alerts_select_update(monkeypatch) -> None:
    conn = _Connection(rows=_rows())
    monkeypatch.setattr(db, "engine", _Engine("postgresql", conn))
    monkeypatch.setattr(db, "inspect_postgres_role_security_state", lambda _conn: _state(bypass=True))
    result = db.validate_alert_worker_database_role()
    assert result["validated"] is True
    assert result["role"] == "rivexis_service"


@pytest.mark.parametrize(
    ("rows", "match"),
    [
        (_rows(alerts=(True, True, True, False)), "exactly SELECT\\+UPDATE"),
        (_rows(other=(True, False, False, False)), "over-privileged"),
    ],
)
def test_worker_validator_rejects_excess_table_dml(monkeypatch, rows, match) -> None:
    conn = _Connection(rows=rows)
    monkeypatch.setattr(db, "engine", _Engine("postgresql", conn))
    monkeypatch.setattr(db, "inspect_postgres_role_security_state", lambda _conn: _state(bypass=True))
    with pytest.raises(RuntimeError, match=match):
        db.validate_alert_worker_database_role()


def test_api_startup_and_rls_certification_enforce_effective_role_security() -> None:
    root = Path(__file__).resolve().parents[3]
    main = (root / "apps" / "api" / "rivexis_api" / "main.py").read_text()
    identity = (root / "apps" / "api" / "rivexis_api" / "services" / "postgres_identity.py").read_text()
    cert = (root / "scripts" / "certify_postgres_rls.py").read_text()
    configurator = (root / "apps" / "api" / "configure-alert-worker-role.py").read_text()
    roles = (root / "infrastructure" / "postgres" / "001_roles.sql").read_text()

    assert "validate_application_database_role()" in main
    assert "pg_has_role(current_user, r.oid, 'MEMBER')" in identity
    assert "rolcreatedb" in identity and "rolcreaterole" in identity and "rolreplication" in identity
    assert "NOINHERIT standalone database role" in identity
    assert "has_database_privilege" in identity and "has_schema_privilege" in identity
    assert "owned_relations" in identity
    assert "validate_standalone_service_role" in cert
    assert "pg_has_role(:role, r.oid, 'MEMBER')" in configurator
    assert "NOREPLICATION NOINHERIT NOBYPASSRLS" in roles
    assert "NOREPLICATION NOINHERIT BYPASSRLS" in roles
