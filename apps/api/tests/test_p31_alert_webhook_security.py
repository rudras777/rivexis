from __future__ import annotations

import json

import httpx
import pytest

import rivexis_api.services.alert_delivery as delivery
from rivexis_api.services.alert_delivery import (
    DeliveryConfigurationError,
    WebhookDeliveryError,
    delivery_failure_code,
    process_due_alerts,
    send_webhook,
    validate_alert_webhook_configuration,
)


def provision(client, email="p30-alerts@example.com"):
    signup = client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": "correct-horse-battery", "role": "Analyst"},
    )
    headers = {"Authorization": "Bearer " + signup.json()["access_token"]}
    ws = client.post("/api/v1/workspaces", headers=headers, json={"name": "SOC", "role": "Analyst"}).json()
    mon = client.post(
        "/api/v1/monitors",
        headers=headers,
        json={
            "workspace_id": ws["id"],
            "entity": "0x1111111111111111111111111111111111111111",
            "chain": "ethereum",
            "rules": ["threat"],
        },
    ).json()
    return headers, ws, mon


def ingress(client, ws, mon, event_id="hn-p30-1"):
    body = {
        "workspace_id": ws["id"],
        "monitor_id": mon["id"],
        "event_type": "threat",
        "severity": "critical",
        "affected_entity": mon["entity"],
        "confidence": 99,
        "provider_payload": {"source_event_id": event_id, "evidence": "tenant-private-evidence"},
    }
    return client.post(
        "/api/v1/integrations/hypernative/events",
        json=body,
        headers={"X-Rivexis-Webhook-Secret": "ingress-secret"},
    )


def test_production_webhook_requires_https(monkeypatch) -> None:
    monkeypatch.setenv("RIVEXIS_ENV", "production")
    monkeypatch.setenv("RIVEXIS_ALERT_WEBHOOK_URL", "http://receiver.invalid/alerts")
    monkeypatch.setenv("RIVEXIS_ALERT_WEBHOOK_SECRET", "secret")
    with pytest.raises(DeliveryConfigurationError, match="production_webhook_requires_https"):
        validate_alert_webhook_configuration()


def test_production_webhook_requires_hmac_secret(monkeypatch) -> None:
    monkeypatch.setenv("RIVEXIS_ENV", "production")
    monkeypatch.setenv("RIVEXIS_ALERT_WEBHOOK_URL", "https://receiver.invalid/alerts")
    monkeypatch.delenv("RIVEXIS_ALERT_WEBHOOK_SECRET", raising=False)
    with pytest.raises(DeliveryConfigurationError, match="production_webhook_requires_hmac_secret"):
        validate_alert_webhook_configuration()


def test_webhook_url_rejects_embedded_credentials_and_fragments(monkeypatch) -> None:
    monkeypatch.setenv("RIVEXIS_ENV", "development")
    monkeypatch.setenv("RIVEXIS_ALERT_WEBHOOK_URL", "https://user:password@receiver.invalid/alerts")
    with pytest.raises(DeliveryConfigurationError, match="webhook_url_userinfo_forbidden"):
        validate_alert_webhook_configuration()
    monkeypatch.setenv("RIVEXIS_ALERT_WEBHOOK_URL", "https://receiver.invalid/alerts#secret-fragment")
    with pytest.raises(DeliveryConfigurationError, match="webhook_url_fragment_forbidden"):
        validate_alert_webhook_configuration()
    monkeypatch.setenv("RIVEXIS_ALERT_WEBHOOK_URL", "https://receiver.invalid/alerts?token=secret")
    with pytest.raises(DeliveryConfigurationError, match="webhook_url_query_forbidden"):
        validate_alert_webhook_configuration()


def test_development_can_use_local_unsigned_http_for_explicit_testing(monkeypatch) -> None:
    monkeypatch.setenv("RIVEXIS_ENV", "development")
    monkeypatch.setenv("RIVEXIS_ALERT_WEBHOOK_URL", "http://127.0.0.1:9999/alerts")
    monkeypatch.delenv("RIVEXIS_ALERT_WEBHOOK_SECRET", raising=False)
    cfg = validate_alert_webhook_configuration()
    assert cfg["url"].startswith("http://127.0.0.1")


def test_production_misconfiguration_does_not_consume_pending_alert(client, monkeypatch) -> None:
    monkeypatch.setenv("HYPERNATIVE_WEBHOOK_SECRET", "ingress-secret")
    monkeypatch.setenv("RIVEXIS_ENV", "development")
    monkeypatch.setenv("RIVEXIS_ALERT_WEBHOOK_URL", "https://receiver.invalid/alerts")
    monkeypatch.delenv("RIVEXIS_ALERT_WEBHOOK_SECRET", raising=False)
    headers, ws, mon = provision(client)
    accepted = ingress(client, ws, mon)
    assert accepted.status_code == 202
    monkeypatch.setenv("RIVEXIS_ENV", "production")
    result = process_due_alerts(ws["id"])
    assert result["processed"] == 0
    assert result["reason"] == "production_webhook_requires_hmac_secret"
    rows = client.get("/api/v1/alerts", headers=headers, params={"workspace_id": ws["id"]}).json()["items"]
    row = next(item for item in rows if item["id"] == accepted.json()["alert_id"])
    assert row["delivery_status"] == "pending"
    assert row["delivery_attempts"] == 0


def test_persisted_delivery_failure_is_stable_code_not_exception_text(client, monkeypatch) -> None:
    monkeypatch.setenv("HYPERNATIVE_WEBHOOK_SECRET", "ingress-secret")
    monkeypatch.setenv("RIVEXIS_ALERT_WEBHOOK_URL", "https://receiver.invalid/alerts")
    headers, ws, mon = provision(client, "p30-error@example.com")
    accepted = ingress(client, ws, mon, "hn-p30-error")
    secret_message = "https://token-secret@receiver.invalid tenant-db-password"
    result = process_due_alerts(ws["id"], sender=lambda _alert: (_ for _ in ()).throw(RuntimeError(secret_message)))
    assert result["items"][0]["error"] == "delivery_error_RuntimeError"
    rows = client.get("/api/v1/alerts", headers=headers, params={"workspace_id": ws["id"]}).json()["items"]
    row = next(item for item in rows if item["id"] == accepted.json()["alert_id"])
    assert row["last_delivery_error"] == "delivery_error_RuntimeError"
    assert "token-secret" not in row["last_delivery_error"]
    assert "password" not in row["last_delivery_error"]


def test_send_webhook_signs_canonical_body_and_excludes_prior_delivery_error(monkeypatch) -> None:
    monkeypatch.setenv("RIVEXIS_ENV", "production")
    monkeypatch.setenv("RIVEXIS_ALERT_WEBHOOK_URL", "https://receiver.invalid/alerts")
    monkeypatch.setenv("RIVEXIS_ALERT_WEBHOOK_SECRET", "production-hmac-secret")
    monkeypatch.setenv("RIVEXIS_ALERT_WEBHOOK_SCOPE", "internal_gateway")
    captured: dict[str, object] = {}

    class FakeResponse:
        status_code = 204

    class FakeClient:
        def __init__(self, *args, **kwargs):
            captured["client_kwargs"] = kwargs

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def post(self, url, *, content, headers):
            captured["url"] = url
            captured["content"] = content
            captured["headers"] = headers
            return FakeResponse()

    monkeypatch.setattr(delivery.httpx, "Client", FakeClient)
    result = send_webhook(
        {
            "id": "alert-1",
            "workspace_id": "workspace-1",
            "payload": {"evidence": "tenant evidence"},
            "last_delivery_error": "https://secret-token@old-receiver.invalid",
        }
    )
    assert result["status_code"] == 204
    body = json.loads(captured["content"])
    assert "last_delivery_error" not in body["alert"]
    assert body["alert"]["payload"]["evidence"] == "tenant evidence"
    headers = captured["headers"]
    assert str(headers["X-Rivexis-Signature"]).startswith("sha256=")
    assert str(headers["X-Rivexis-Timestamp"]).isdigit()
    assert headers["X-Rivexis-Signature-Version"] == "v1"
    import hashlib, hmac
    expected = "sha256=" + hmac.new(
        b"production-hmac-secret",
        str(headers["X-Rivexis-Timestamp"]).encode() + b"." + captured["content"],
        hashlib.sha256,
    ).hexdigest()
    assert headers["X-Rivexis-Signature"] == expected
    assert "secret-token" not in captured["content"].decode()


def test_transport_exceptions_are_reduced_to_non_secret_codes(monkeypatch) -> None:
    monkeypatch.setenv("RIVEXIS_ENV", "production")
    monkeypatch.setenv("RIVEXIS_ALERT_WEBHOOK_URL", "https://receiver.invalid/alerts")
    monkeypatch.setenv("RIVEXIS_ALERT_WEBHOOK_SECRET", "production-hmac-secret")
    monkeypatch.setenv("RIVEXIS_ALERT_WEBHOOK_SCOPE", "internal_gateway")

    class FailingClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def post(self, url, *, content, headers):
            request = httpx.Request("POST", url)
            raise httpx.ConnectError("failed for token=do-not-store", request=request)

    monkeypatch.setattr(delivery.httpx, "Client", FailingClient)
    with pytest.raises(WebhookDeliveryError, match="webhook_transport_error") as excinfo:
        send_webhook({"id": "alert-1", "payload": {"secret": "tenant"}})
    assert delivery_failure_code(excinfo.value) == "webhook_transport_error"
    assert "do-not-store" not in str(excinfo.value)
