from __future__ import annotations

from rivexis_api.services import auth_email
from rivexis_api.services.auth_rate_limit import reset_auth_rate_limit_for_tests
from rivexis_api.services.transactional_email import EmailAcceptance, EmailDeliveryError


def _accepted(**kwargs):
    return EmailAcceptance(
        status="accepted",
        provider="brevo",
        provider_message_id="test-message",
        sandbox=False,
    )


def test_default_policy_preserves_immediate_signup_and_marks_user_verified(client, monkeypatch):
    reset_auth_rate_limit_for_tests()
    monkeypatch.delenv("RIVEXIS_EMAIL_VERIFICATION_REQUIRED", raising=False)

    signup = client.post(
        "/api/v1/auth/signup",
        json={"email": "legacy-compatible@example.com", "password": "correct-horse-battery", "role": "Analyst"},
    )

    assert signup.status_code == 200
    body = signup.json()
    assert body["verification_required"] is False
    assert body["access_token"]

    me = client.get(
        "/api/v1/me",
        headers={"Authorization": f"Bearer {body['access_token']}"},
    )
    assert me.status_code == 200
    assert me.json()["email_verified"] is True


def test_required_verification_blocks_session_until_single_use_token_is_confirmed(client, monkeypatch):
    reset_auth_rate_limit_for_tests()
    monkeypatch.setenv("RIVEXIS_EMAIL_VERIFICATION_REQUIRED", "true")
    captured: dict[str, str] = {}

    def fake_send(**kwargs):
        captured["token"] = kwargs["params"]["verification_token"]
        return _accepted()

    monkeypatch.setattr(auth_email, "send_template_email", fake_send)

    signup = client.post(
        "/api/v1/auth/signup",
        json={"email": "verify-me@example.com", "password": "correct-horse-battery", "role": "Analyst"},
    )
    assert signup.status_code == 200
    body = signup.json()
    assert body["verification_required"] is True
    assert "access_token" not in body
    assert captured["token"]

    blocked = client.post(
        "/api/v1/auth/login",
        json={"email": "verify-me@example.com", "password": "correct-horse-battery"},
    )
    assert blocked.status_code == 403
    assert blocked.json()["detail"] == "Email verification required"

    confirmed = client.post(
        "/api/v1/auth/email-verification/confirm",
        json={"token": captured["token"]},
    )
    assert confirmed.status_code == 200
    assert confirmed.json()["status"] == "verified"

    replay = client.post(
        "/api/v1/auth/email-verification/confirm",
        json={"token": captured["token"]},
    )
    assert replay.status_code == 400

    login = client.post(
        "/api/v1/auth/login",
        json={"email": "verify-me@example.com", "password": "correct-horse-battery"},
    )
    assert login.status_code == 200
    assert login.json()["access_token"]


def test_verification_request_is_enumeration_safe_even_when_delivery_fails(client, monkeypatch):
    reset_auth_rate_limit_for_tests()
    monkeypatch.setenv("RIVEXIS_EMAIL_VERIFICATION_REQUIRED", "true")
    monkeypatch.setattr(auth_email, "send_template_email", _accepted)

    signup = client.post(
        "/api/v1/auth/signup",
        json={"email": "request-existing@example.com", "password": "correct-horse-battery", "role": "Analyst"},
    )
    assert signup.status_code == 200

    def fail_send(**kwargs):
        raise EmailDeliveryError("provider unavailable")

    monkeypatch.setattr(auth_email, "send_template_email", fail_send)
    existing = client.post(
        "/api/v1/auth/email-verification/request",
        json={"email": "request-existing@example.com"},
    )
    missing = client.post(
        "/api/v1/auth/email-verification/request",
        json={"email": "not-registered@example.com"},
    )
    assert existing.status_code == 202
    assert missing.status_code == 202
    assert existing.json() == missing.json() == {"status": "accepted"}


def test_password_reset_is_single_use_and_revokes_existing_bearer_sessions(client, monkeypatch):
    reset_auth_rate_limit_for_tests()
    monkeypatch.delenv("RIVEXIS_EMAIL_VERIFICATION_REQUIRED", raising=False)

    signup = client.post(
        "/api/v1/auth/signup",
        json={"email": "reset-me@example.com", "password": "old-password-123", "role": "Analyst"},
    )
    assert signup.status_code == 200
    old_token = signup.json()["access_token"]
    old_headers = {"Authorization": f"Bearer {old_token}"}
    assert client.get("/api/v1/me", headers=old_headers).status_code == 200

    captured: dict[str, str] = {}

    def fake_send(**kwargs):
        captured["token"] = kwargs["params"]["reset_token"]
        return _accepted()

    monkeypatch.setattr(auth_email, "send_template_email", fake_send)

    requested = client.post(
        "/api/v1/auth/password-reset/request",
        json={"email": "reset-me@example.com"},
    )
    assert requested.status_code == 202
    assert requested.json() == {"status": "accepted"}
    assert captured["token"]

    confirmed = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": captured["token"], "password": "new-password-456"},
    )
    assert confirmed.status_code == 200
    assert confirmed.json() == {"status": "password_reset", "sessions_revoked": True}

    assert client.get("/api/v1/me", headers=old_headers).status_code == 401

    replay = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"token": captured["token"], "password": "another-password-789"},
    )
    assert replay.status_code == 400

    old_login = client.post(
        "/api/v1/auth/login",
        json={"email": "reset-me@example.com", "password": "old-password-123"},
    )
    assert old_login.status_code == 401

    new_login = client.post(
        "/api/v1/auth/login",
        json={"email": "reset-me@example.com", "password": "new-password-456"},
    )
    assert new_login.status_code == 200


def test_password_reset_request_does_not_disclose_account_existence(client, monkeypatch):
    reset_auth_rate_limit_for_tests()
    monkeypatch.setattr(auth_email, "send_template_email", _accepted)

    signup = client.post(
        "/api/v1/auth/signup",
        json={"email": "reset-existing@example.com", "password": "correct-horse-battery", "role": "Analyst"},
    )
    assert signup.status_code == 200

    existing = client.post(
        "/api/v1/auth/password-reset/request",
        json={"email": "reset-existing@example.com"},
    )
    missing = client.post(
        "/api/v1/auth/password-reset/request",
        json={"email": "reset-missing@example.com"},
    )
    assert existing.status_code == 202
    assert missing.status_code == 202
    assert existing.json() == missing.json() == {"status": "accepted"}
