from __future__ import annotations

from pathlib import Path

import pytest

from rivexis_api.core.config import Settings, validate_runtime_security
from rivexis_api.services.store import add_organization_member


def bearer_signup(client, email: str):
    r = client.post('/api/v1/auth/signup', json={"email": email, "password": "correct-horse-battery", "role": "Analyst"})
    assert r.status_code == 200
    return r.json(), {"Authorization": "Bearer " + r.json()["access_token"]}


def test_web_auth_uses_httponly_cookie_and_csrf_not_browser_bearer_storage(client):
    signup = client.post('/api/v1/auth/web/signup', json={"email": "cookie@example.com", "password": "correct-horse-battery", "role": "Analyst"})
    assert signup.status_code == 200
    body = signup.json()
    assert "access_token" not in body
    assert body["csrf_token"]
    cookie = signup.headers.get("set-cookie", "")
    assert "rivexis_session=" in cookie
    assert "HttpOnly" in cookie

    # The cookie authenticates safe reads.
    me = client.get('/api/v1/me')
    assert me.status_code == 200
    assert me.json()["email"] == "cookie@example.com"

    # Unsafe cookie-authenticated methods fail closed without CSRF.
    denied = client.post('/api/v1/workspaces', json={"name": "Denied", "role": "Analyst"})
    assert denied.status_code == 403
    assert denied.json()["detail"] == "CSRF validation failed"

    created = client.post(
        '/api/v1/workspaces',
        headers={"X-Rivexis-CSRF": body["csrf_token"]},
        json={"name": "Cookie workspace", "role": "Analyst"},
    )
    assert created.status_code == 200

    # A fresh CSRF token can be recovered after an SPA reload without exposing the session cookie.
    refreshed = client.get('/api/v1/auth/web/csrf')
    assert refreshed.status_code == 200
    assert refreshed.json()["csrf_token"] == body["csrf_token"]


def test_browser_signup_conflict_does_not_enumerate_existing_account(client):
    payload={"email":"existing-browser@example.com","password":"correct-horse-battery","role":"Analyst"}
    first=client.post('/api/v1/auth/web/signup',json=payload)
    assert first.status_code==200
    duplicate=client.post('/api/v1/auth/web/signup',json=payload)
    assert duplicate.status_code==409
    assert duplicate.json()["detail"]=="Unable to create account with those details"
    lowered=duplicate.text.lower()
    assert "already registered" not in lowered
    assert payload["email"] not in lowered


def test_cookie_logout_requires_csrf_clears_cookie_and_revokes_session(client):
    login_seed, bearer = bearer_signup(client, "logout-cookie@example.com")
    # Establish cookie session through web login.
    web = client.post('/api/v1/auth/web/login', json={"email": "logout-cookie@example.com", "password": "correct-horse-battery"})
    csrf = web.json()["csrf_token"]
    assert client.post('/api/v1/auth/logout').status_code == 403
    out = client.post('/api/v1/auth/logout', headers={"X-Rivexis-CSRF": csrf})
    assert out.status_code == 200
    assert "rivexis_session=" in out.headers.get("set-cookie", "")
    assert client.get('/api/v1/me').status_code == 401
    # Logout bumps token_version, so a previously issued bearer token is revoked too.
    assert client.get('/api/v1/me', headers=bearer).status_code == 401


def test_bearer_clients_remain_csrf_exempt_and_backward_compatible(client):
    data, headers = bearer_signup(client, "bearer-compatible@example.com")
    assert data["access_token"]
    r = client.post('/api/v1/workspaces', headers=headers, json={"name": "Bearer workspace", "role": "Analyst"})
    assert r.status_code == 200


def test_membership_claim_binds_authenticated_user_to_specific_org(client):
    owner, owner_h = bearer_signup(client, "claim-owner@example.com")
    member, member_h = bearer_signup(client, "claim-member@example.com")
    other_owner, other_h = bearer_signup(client, "claim-other-owner@example.com")
    org = client.post('/api/v1/organizations', headers=owner_h, json={"name": "Claim Org"}).json()
    other = client.post('/api/v1/organizations', headers=other_h, json={"name": "Other Claim Org"}).json()

    claim = client.post(f'/api/v1/organizations/{org["id"]}/membership-claim', headers=member_h)
    assert claim.status_code == 200
    token = claim.json()["claim_token"]

    wrong = client.post(
        f'/api/v1/organizations/{other["id"]}/members/claim', headers=other_h,
        json={"claim_token": token, "role": "ANALYST"},
    )
    assert wrong.status_code == 409

    accepted = client.post(
        f'/api/v1/organizations/{org["id"]}/members/claim', headers=owner_h,
        json={"claim_token": token, "role": "ANALYST"},
    )
    assert accepted.status_code == 200
    assert accepted.json()["user_id"] == member["user"]["id"]
    members = client.get(f'/api/v1/organizations/{org["id"]}/members', headers=owner_h).json()["items"]
    assert any(x["user_id"] == member["user"]["id"] and x["role"] == "ANALYST" for x in members)


def test_revoked_membership_claim_cannot_be_accepted(client):
    _, owner_h = bearer_signup(client, "revoked-claim-owner@example.com")
    _, member_h = bearer_signup(client, "revoked-claim-member@example.com")
    org = client.post('/api/v1/organizations', headers=owner_h, json={"name": "Revoked Claim Org"}).json()
    claim = client.post(f'/api/v1/organizations/{org["id"]}/membership-claim', headers=member_h).json()["claim_token"]
    assert client.post('/api/v1/auth/logout', headers=member_h).status_code == 200
    denied = client.post(
        f'/api/v1/organizations/{org["id"]}/members/claim', headers=owner_h,
        json={"claim_token": claim, "role": "ANALYST"},
    )
    assert denied.status_code == 409
    assert "revoked" in denied.json()["detail"].lower()


def test_direct_new_member_add_can_be_disabled_without_breaking_existing_role_updates(client):
    owner, owner_h = bearer_signup(client, "direct-owner@example.com")
    member, member_h = bearer_signup(client, "direct-member@example.com")
    org = client.post('/api/v1/organizations', headers=owner_h, json={"name": "Direct Guard Org"}).json()
    with pytest.raises(PermissionError, match="membership claim"):
        add_organization_member(owner["user"]["id"], org["id"], "direct-member@example.com", "ANALYST", allow_new=False)
    # Establish membership using the authenticated claim path, then direct email may update that known member.
    claim = client.post(f'/api/v1/organizations/{org["id"]}/membership-claim', headers=member_h).json()["claim_token"]
    assert client.post(f'/api/v1/organizations/{org["id"]}/members/claim', headers=owner_h, json={"claim_token": claim, "role": "ANALYST"}).status_code == 200
    updated = add_organization_member(owner["user"]["id"], org["id"], "direct-member@example.com", "VIEWER", allow_new=False)
    assert updated["role"] == "VIEWER"


def test_production_requires_https_origins_and_disables_direct_email_member_add():
    base = dict(
        environment="production",
        auth_secret="prod-" + "x" * 64,
        enable_demo_adapter=False,
        allow_direct_org_member_add=False,
        allowed_origins=("https://app.rivexis.example",),
        auth_rate_limit_backend="redis",
        redis_url="redis://cache.internal:6379/0",
        provider_control_backend="redis",
        database_url="postgresql+psycopg://runtime@db.internal/rivexis",
    )
    assert validate_runtime_security(Settings(**base))["production"] is True
    with pytest.raises(RuntimeError, match="RIVEXIS_ALLOW_DIRECT_ORG_MEMBER_ADD"):
        validate_runtime_security(Settings(**{**base, "allow_direct_org_member_add": True}))
    with pytest.raises(RuntimeError, match="HTTPS origins"):
        validate_runtime_security(Settings(**{**base, "allowed_origins": ("http://app.rivexis.example",)}))
    with pytest.raises(RuntimeError, match="wildcards"):
        validate_runtime_security(Settings(**{**base, "allowed_origins": ("https://*.rivexis.example",)}))
    with pytest.raises(RuntimeError, match="PROVIDER_CONTROL_BACKEND"):
        validate_runtime_security(Settings(**{**base, "provider_control_backend": "memory"}))
    with pytest.raises(RuntimeError, match="PostgreSQL"):
        validate_runtime_security(Settings(**{**base, "database_url": "sqlite:///./rivexis.db"}))


def test_frontend_contains_no_persistent_bearer_token_storage_and_has_security_headers():
    root = Path(__file__).resolve().parents[3]
    api = (root / "apps/web/lib/api.ts").read_text()
    login = (root / "apps/web/app/login/page.tsx").read_text()
    signup = (root / "apps/web/app/signup/page.tsx").read_text()
    next_config = (root / "apps/web/next.config.ts").read_text()
    combined = api + login + signup
    assert "rivexis_token" not in combined
    assert "localStorage.setItem(\"rivexis_token\"" not in combined
    assert 'credentials:"include"' in api
    assert 'X-Rivexis-CSRF' in api
    assert '/api/v1/auth/web/login' in login
    assert '/api/v1/auth/web/signup' in signup
    assert 'api,setCsrfToken' in login
    assert 'api,setCsrfToken' in signup
    shell = (root / "apps/web/components/AppShell.tsx").read_text()
    assert '/api/v1/auth/logout' in shell
    assert 'setCsrfToken(null)' in shell
    assert "Strict-Transport-Security" in next_config
    assert "Content-Security-Policy" in next_config


def test_hypernative_production_uses_monitor_scoped_credentials(client, monkeypatch):
    monkeypatch.setenv("RIVEXIS_ENV", "production")
    root_secret = "hypernative-production-root-" + "x" * 40
    monkeypatch.setenv("HYPERNATIVE_WEBHOOK_SECRET", root_secret)
    _, h1 = bearer_signup(client, "hn-tenant-1@example.com")
    _, h2 = bearer_signup(client, "hn-tenant-2@example.com")
    w1 = client.post('/api/v1/workspaces', headers=h1, json={"name": "HN Tenant One", "role": "Analyst"}).json()
    w2 = client.post('/api/v1/workspaces', headers=h2, json={"name": "HN Tenant Two", "role": "Analyst"}).json()
    m1 = client.post('/api/v1/monitors', headers=h1, json={"workspace_id": w1["id"], "entity": "0x1", "rules": ["threat"]}).json()
    m2 = client.post('/api/v1/monitors', headers=h2, json={"workspace_id": w2["id"], "entity": "0x2", "rules": ["threat"]}).json()
    c1 = client.get(f'/api/v1/monitors/{m1["id"]}/hypernative-webhook-credential', headers=h1)
    c2 = client.get(f'/api/v1/monitors/{m2["id"]}/hypernative-webhook-credential', headers=h2)
    assert c1.status_code == c2.status_code == 200
    token1 = c1.json()["credential"]
    token2 = c2.json()["credential"]
    assert token1 != token2
    assert root_secret not in token1 and root_secret not in token2

    body2 = {
        "workspace_id": w2["id"], "monitor_id": m2["id"], "event_type": "threat",
        "severity": "high", "provider_payload": {"source_event_id": "cross-tenant-attempt"},
    }
    # Tenant-one credential cannot authenticate tenant-two ingestion.
    assert client.post('/api/v1/integrations/hypernative/events', json=body2, headers={"X-Rivexis-Webhook-Secret": token1}).status_code == 401
    accepted = client.post('/api/v1/integrations/hypernative/events', json=body2, headers={"X-Rivexis-Webhook-Secret": token2})
    assert accepted.status_code == 202
    assert accepted.json()["authentication"] == "rivexis_monitor_derived_secret_v1"
    # Root secret itself is no longer a customer-facing credential in production.
    assert client.post('/api/v1/integrations/hypernative/events', json=body2, headers={"X-Rivexis-Webhook-Secret": root_secret}).status_code == 401


def test_hypernative_credential_requires_workspace_management(client, monkeypatch):
    monkeypatch.setenv("HYPERNATIVE_WEBHOOK_SECRET", "root-secret-for-test")
    _, owner_h = bearer_signup(client, "hn-org-owner@example.com")
    _, analyst_h = bearer_signup(client, "hn-org-analyst@example.com")
    org = client.post('/api/v1/organizations', headers=owner_h, json={"name": "HN Org"}).json()
    assert client.post(f'/api/v1/organizations/{org["id"]}/members', headers=owner_h, json={"email": "hn-org-analyst@example.com", "role": "ANALYST"}).status_code == 200
    workspace = client.post('/api/v1/workspaces', headers=owner_h, json={"name": "HN Shared", "role": "Analyst", "organization_id": org["id"]}).json()
    monitor = client.post('/api/v1/monitors', headers=analyst_h, json={"workspace_id": workspace["id"], "entity": "0x3", "rules": ["threat"]}).json()
    assert client.get(f'/api/v1/monitors/{monitor["id"]}/hypernative-webhook-credential', headers=analyst_h).status_code == 403
    assert client.get(f'/api/v1/monitors/{monitor["id"]}/hypernative-webhook-credential', headers=owner_h).status_code == 200


def test_login_rate_limit_is_account_keyed_and_success_clears_budget(client, monkeypatch):
    from rivexis_api.services.auth_rate_limit import reset_auth_rate_limit_for_tests

    reset_auth_rate_limit_for_tests()
    monkeypatch.setenv("RIVEXIS_AUTH_RATE_LIMIT_BACKEND", "memory")
    monkeypatch.setenv("RIVEXIS_AUTH_LOGIN_ATTEMPTS_PER_MINUTE", "2")
    bearer_signup(client, "limited-login@example.com")
    payload = {"email": "limited-login@example.com", "password": "wrong-password"}
    assert client.post('/api/v1/auth/login', json=payload).status_code == 401
    assert client.post('/api/v1/auth/login', json=payload).status_code == 401
    assert client.post('/api/v1/auth/login', json=payload).status_code == 429
    # A different account identity has a distinct rate bucket.
    assert client.post('/api/v1/auth/login', json={"email": "different@example.com", "password": "wrong-password"}).status_code == 401
    reset_auth_rate_limit_for_tests()
    good = client.post('/api/v1/auth/login', json={"email": "limited-login@example.com", "password": "correct-horse-battery"})
    assert good.status_code == 200
    # Success clears the previous attempt bucket.
    assert client.post('/api/v1/auth/login', json=payload).status_code == 401


def test_production_requires_distributed_auth_rate_limiter():
    base = dict(
        environment="production", auth_secret="prod-" + "z" * 64, enable_demo_adapter=False,
        allow_direct_org_member_add=False, allowed_origins=("https://app.rivexis.example",),
        auth_rate_limit_backend="redis", redis_url="redis://cache.internal:6379/0",
        provider_control_backend="redis", database_url="postgresql+psycopg://runtime@db.internal/rivexis",
    )
    assert validate_runtime_security(Settings(**base))["auth_rate_limit_backend"] == "redis"
    postgres = {**base, "auth_rate_limit_backend": "postgres", "provider_control_backend": "postgres", "redis_url": ""}
    validated = validate_runtime_security(Settings(**postgres))
    assert validated["auth_rate_limit_backend"] == "postgres"
    assert validated["provider_control_backend"] == "postgres"
    with pytest.raises(RuntimeError, match="AUTH_RATE_LIMIT_BACKEND"):
        validate_runtime_security(Settings(**{**base, "auth_rate_limit_backend": "memory"}))
    with pytest.raises(RuntimeError, match="PROVIDER_CONTROL_BACKEND"):
        validate_runtime_security(Settings(**{**base, "provider_control_backend": "memory"}))
    with pytest.raises(RuntimeError, match="REDIS_URL"):
        validate_runtime_security(Settings(**{**base, "redis_url": ""}))


def test_redis_certification_includes_distributed_auth_login_budget():
    root = Path(__file__).resolve().parents[3]
    source = (root / "scripts/certify_redis_distributed.py").read_text()
    assert "AUTH_LOGIN_BUDGET_SCRIPT" in source
    assert "shared auth budget" in source
    assert "shared auth login budget" in source


def test_production_web_session_cookie_is_secure(client, monkeypatch):
    bearer_signup(client, "secure-cookie@example.com")
    monkeypatch.setenv("RIVEXIS_ENV", "production")
    r = client.post('/api/v1/auth/web/login', json={"email": "secure-cookie@example.com", "password": "correct-horse-battery"})
    assert r.status_code == 200
    cookie = r.headers.get("set-cookie", "")
    assert "HttpOnly" in cookie
    assert "Secure" in cookie


def test_api_route_authentication_allowlist_has_no_accidental_public_tenant_route():
    from rivexis_api.main import app

    public = {
        "/api/v1/auth/signup",
        "/api/v1/auth/login",
        "/api/v1/auth/web/signup",
        "/api/v1/auth/web/login",
        "/api/v1/protocol-adapters",
        "/api/v1/protocol-deployments",
        "/api/v1/integrations/hypernative/events",
    }
    for route in app.routes:
        path = getattr(route, "path", "")
        if not path.startswith("/api/v1/") or path in public:
            continue
        dependant = getattr(route, "dependant", None)
        dependency_names = {
            getattr(getattr(dep, "call", None), "__name__", "")
            for dep in (getattr(dependant, "dependencies", None) or [])
        }
        assert "current_user" in dependency_names, f"unexpected unauthenticated API route: {path}"


def test_p34_rls_migration_and_certifier_encode_membership_revocation_and_telemetry_scrub():
    root = Path(__file__).resolve().parents[3]
    migration = (root / "apps/api/alembic/versions/0010_org_workspace_membership_rls.py").read_text()
    initial = (root / "apps/api/alembic/versions/0003_production_schema_rls.py").read_text()
    certifier = (root / "scripts/certify_postgres_rls.py").read_text()
    for source in (migration, initial):
        assert "organization_id IS NULL AND owner_user_id" in source
        assert "organization_id IS NOT NULL AND organization_id IN" in source
    assert "UPDATE provider_requests SET endpoint = NULL" in migration
    assert "removed organization workspace creator retained tenant access" in certifier
    assert "RIVEXIS_RLS_WORKER_DATABASE_URL" in certifier


def test_login_rate_limiter_failure_fails_closed_without_backend_secret(client, monkeypatch):
    import rivexis_api.main as main
    bearer_signup(client, "limiter-failure@example.com")
    def broken(_email):
        raise RuntimeError("redis://user:super-secret@cache.internal/0")
    monkeypatch.setattr(main, "consume_login_attempt", broken)
    r = client.post('/api/v1/auth/login', json={"email": "limiter-failure@example.com", "password": "correct-horse-battery"})
    assert r.status_code == 503
    assert r.json()["detail"] == "Authentication rate limiter unavailable"
    assert "super-secret" not in r.text
