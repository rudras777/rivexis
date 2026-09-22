from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from rivexis_api.core.config import Settings, validate_runtime_security
from rivexis_api.main import app


def _settings(*, environment: str = "production", auth_secret: str = "x" * 48, demo: bool = False) -> Settings:
    return Settings(environment=environment, auth_secret=auth_secret, enable_demo_adapter=demo, allow_direct_org_member_add=False, allowed_origins=("https://app.rivexis.example",), auth_rate_limit_backend="redis", redis_url="redis://cache.internal:6379/0", provider_control_backend="redis", database_url="postgresql+psycopg://runtime@db.internal/rivexis")


def _auth_headers(client: TestClient, email: str = "provider-security@example.com") -> dict[str, str]:
    signup = client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": "correct-horse-battery", "role": "Analyst"},
    )
    assert signup.status_code == 200
    return {"Authorization": "Bearer " + signup.json()["access_token"]}


@pytest.mark.parametrize(
    "secret",
    ["", "development-only-change-me", "local-compose-secret-change-me", "replace-with-a-long-random-secret", "short-secret"],
)
def test_production_rejects_missing_placeholder_or_short_auth_secret(secret: str) -> None:
    with pytest.raises(RuntimeError, match="RIVEXIS_AUTH_SECRET"):
        validate_runtime_security(_settings(auth_secret=secret))


def test_production_accepts_long_non_placeholder_auth_secret() -> None:
    result = validate_runtime_security(_settings(auth_secret="prod-" + "a" * 64))
    assert result["production"] is True
    assert result["demo_adapter_enabled"] is False


def test_production_rejects_demo_adapter() -> None:
    with pytest.raises(RuntimeError, match="ENABLE_DEMO_ADAPTER"):
        validate_runtime_security(_settings(auth_secret="prod-" + "b" * 64, demo=True))


def test_development_allows_explicit_demo_and_development_secret() -> None:
    result = validate_runtime_security(
        _settings(environment="development", auth_secret="development-only-change-me", demo=True)
    )
    assert result["production"] is False
    assert result["demo_adapter_enabled"] is True


def test_provider_diagnostics_require_authentication(client: TestClient) -> None:
    for path in (
        "/api/v1/providers",
        "/api/v1/providers/status",
        "/api/v1/providers/status?deep=true",
        "/api/v1/providers/resolve/rpc?deep=true&allow_demo=true",
        "/api/v1/providers/mock",
    ):
        response = client.get(path)
        assert response.status_code == 401, path


def test_authenticated_provider_diagnostics_remain_available(client: TestClient) -> None:
    headers = _auth_headers(client)
    assert client.get("/api/v1/providers", headers=headers).status_code == 200
    status = client.get("/api/v1/providers/status", headers=headers)
    assert status.status_code == 200
    assert len(status.json()["providers"]) >= 20
    resolved = client.get("/api/v1/providers/resolve/rpc?allow_demo=true", headers=headers)
    assert resolved.status_code == 200
    detail = client.get("/api/v1/providers/mock", headers=headers)
    assert detail.status_code == 200
