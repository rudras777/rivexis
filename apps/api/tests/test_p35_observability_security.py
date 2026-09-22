from __future__ import annotations

from contextlib import contextmanager

import pytest

from rivexis_api.core import telemetry
from rivexis_api.provider_runtime import execute, reset_runtime_state


def _auth(client, email: str = "p35-observability@example.com") -> dict[str, str]:
    signup = client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": "correct-horse-battery", "role": "Analyst"},
    )
    assert signup.status_code == 200
    return {"Authorization": "Bearer " + signup.json()["access_token"]}


def test_provider_span_never_exports_raw_secret_bearing_endpoint(monkeypatch):
    captured: list[dict[str, object]] = []

    class Span:
        def set_attribute(self, key, value):
            captured[-1][key] = value

    @contextmanager
    def fake_child_span(name, *, kind="internal", attributes=None):
        captured.append({"name": name, "kind": kind, **dict(attributes or {})})
        yield Span()

    monkeypatch.setenv("RIVEXIS_PROVIDER_CONTROL_BACKEND", "memory")
    monkeypatch.setattr("rivexis_api.provider_runtime.child_span", fake_child_span)
    reset_runtime_state()
    secret = "p35-super-secret-rpc-token"
    value = execute(
        "alchemy",
        "eth_blockNumber",
        lambda: "0x123",
        endpoint=f"https://eth-mainnet.g.alchemy.com/v2/{secret}",
    )
    assert value == "0x123"
    assert captured
    exported = captured[-1]
    assert exported["server.address"] == "alchemy:json-rpc"
    assert secret not in repr(exported)


def test_http_trace_uses_route_template_not_resource_identifier(client, monkeypatch):
    import rivexis_api.main as main

    seen: dict[str, object] = {"attributes": {}}

    class Context:
        trace_id = "a" * 32
        traceparent = "00-" + "a" * 32 + "-" + "b" * 16 + "01"

    class Span:
        context = Context()

        def set_status_code(self, status_code):
            seen["status_code"] = status_code

        def set_attribute(self, key, value):
            seen["attributes"][key] = value

        def update_name(self, name):
            seen["name"] = name

    @contextmanager
    def fake_request_span(name, *, incoming_traceparent=None, attributes=None):
        seen["initial_name"] = name
        seen["attributes"].update(dict(attributes or {}))
        yield Span()

    monkeypatch.setattr(main, "request_span", fake_request_span)
    resource_id = "tenant-resource-SECRET-12345"
    response = client.get(f"/api/v1/workspaces/{resource_id}")
    assert response.status_code == 401
    assert seen["initial_name"] == "HTTP GET"
    assert seen["name"] == "GET /api/v1/workspaces/{workspace_id}"
    assert seen["attributes"]["http.route"] == "/api/v1/workspaces/{workspace_id}"
    assert resource_id not in repr(seen)
    assert "url.path" not in seen["attributes"]


def test_production_tenant_api_refuses_deep_provider_probes(client, monkeypatch):
    headers = _auth(client, "p35-deep-probe@example.com")
    monkeypatch.setenv("RIVEXIS_ENV", "production")

    assert client.get("/api/v1/providers/status?deep=true", headers=headers).status_code == 403
    assert client.get("/api/v1/providers/alchemy?deep=true", headers=headers).status_code == 403
    assert client.get("/api/v1/providers/resolve/rpc?deep=true", headers=headers).status_code == 403

    # Shallow inventory/health remains available to an authenticated tenant.
    assert client.get("/api/v1/providers/status?deep=false", headers=headers).status_code == 200


def test_production_otlp_requires_secure_remote_transport(monkeypatch):
    monkeypatch.setenv("RIVEXIS_ENV", "production")
    with pytest.raises(telemetry.TelemetryConfigurationError, match="requires HTTPS"):
        telemetry.validate_otlp_endpoint("http://collector.example.com:4318/v1/traces")
    with pytest.raises(telemetry.TelemetryConfigurationError, match="must not contain"):
        telemetry.validate_otlp_endpoint("https://user:password@collector.example.com/v1/traces")
    with pytest.raises(telemetry.TelemetryConfigurationError, match="must not contain"):
        telemetry.validate_otlp_endpoint("https://collector.example.com/v1/traces?token=secret")

    assert telemetry.validate_otlp_endpoint("https://collector.example.com/v1/traces").startswith("https://")
    assert telemetry.validate_otlp_endpoint("http://127.0.0.1:4318/v1/traces").startswith("http://127.0.0.1")


def test_exception_telemetry_records_type_only(monkeypatch):
    recorded: dict[str, object] = {}

    class Span:
        def set_attribute(self, key, value):
            recorded[key] = value

        def set_status(self, status):
            recorded["status"] = status

        def record_exception(self, exc):  # pragma: no cover - must never be called
            raise AssertionError("record_exception would export raw message/stacktrace")

    secret = "postgresql://user:super-secret-password@db.internal/rivexis"
    telemetry._record_exception_class(Span(), RuntimeError(secret))
    assert recorded["exception.type"] == "RuntimeError"
    assert secret not in repr(recorded)



def test_global_auth_budget_blocks_rotating_account_identifiers(monkeypatch):
    from rivexis_api.services.auth_rate_limit import consume_login_attempt, reset_auth_rate_limit_for_tests

    reset_auth_rate_limit_for_tests()
    monkeypatch.setenv("RIVEXIS_AUTH_RATE_LIMIT_BACKEND", "memory")
    monkeypatch.setenv("RIVEXIS_AUTH_LOGIN_ATTEMPTS_PER_MINUTE", "100")
    monkeypatch.setenv("RIVEXIS_AUTH_GLOBAL_ATTEMPTS_PER_MINUTE", "3")
    assert consume_login_attempt("one@example.com", now=1000.0) is True
    assert consume_login_attempt("two@example.com", now=1000.1) is True
    assert consume_login_attempt("three@example.com", now=1000.2) is True
    assert consume_login_attempt("four@example.com", now=1000.3) is False
    reset_auth_rate_limit_for_tests()


def test_signup_budget_runs_before_expensive_password_hash(client, monkeypatch):
    import rivexis_api.main as main

    monkeypatch.setattr(main, "consume_login_attempt", lambda _email: False)
    called = {"hash": False}

    def forbidden_hash(_password):
        called["hash"] = True
        raise AssertionError("password hash should not run after budget rejection")

    monkeypatch.setattr(main, "hash_password", forbidden_hash)
    response = client.post(
        "/api/v1/auth/signup",
        json={"email": "budget-rejected@example.com", "password": "correct-horse-battery", "role": "Analyst"},
    )
    assert response.status_code == 429
    assert called["hash"] is False


def test_duplicate_signup_rejects_before_rehashing_existing_account(client, monkeypatch):
    first = client.post(
        "/api/v1/auth/signup",
        json={"email": "duplicate-p35@example.com", "password": "correct-horse-battery", "role": "Analyst"},
    )
    assert first.status_code == 200
    import rivexis_api.main as main
    monkeypatch.setattr(main, "consume_login_attempt", lambda _email: True)

    def forbidden_hash(_password):
        raise AssertionError("duplicate signup should not perform a second scrypt hash")

    monkeypatch.setattr(main, "hash_password", forbidden_hash)
    duplicate = client.post(
        "/api/v1/auth/signup",
        json={"email": "duplicate-p35@example.com", "password": "another-password", "role": "Analyst"},
    )
    assert duplicate.status_code == 409


def test_production_global_auth_budget_has_bounded_configuration():
    from rivexis_api.core.config import Settings, validate_runtime_security

    base = dict(
        environment="production",
        auth_secret="prod-" + "z" * 64,
        enable_demo_adapter=False,
        allow_direct_org_member_add=False,
        allowed_origins=("https://app.rivexis.example",),
        auth_rate_limit_backend="redis",
        auth_login_attempts_per_minute=20,
        auth_global_attempts_per_minute=300,
        redis_url="redis://cache.internal:6379/0",
        provider_control_backend="redis",
        database_url="postgresql+psycopg://runtime@db.internal/rivexis",
    )
    assert validate_runtime_security(Settings(**base))["production"] is True
    with pytest.raises(RuntimeError, match="AUTH_GLOBAL_ATTEMPTS_PER_MINUTE"):
        validate_runtime_security(Settings(**{**base, "auth_global_attempts_per_minute": 5}))
