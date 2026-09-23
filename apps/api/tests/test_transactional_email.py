from __future__ import annotations

from dataclasses import replace

import httpx
import pytest

from rivexis_api.services.transactional_email import (
    EmailConfigurationError,
    EmailDeliveryError,
    EmailSettings,
    send_template_email,
    validate_email_configuration,
)


class FakeResponse:
    def __init__(self, status_code: int, payload=None):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload


class FakeClient:
    def __init__(self, response=None, exc: Exception | None = None):
        self.response = response
        self.exc = exc
        self.calls = []

    def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        if self.exc:
            raise self.exc
        return self.response


def cfg(**changes):
    base = EmailSettings(
        provider="brevo",
        api_key="test-api-key-not-a-secret",
        sender_email="security@rivexis.example",
        sender_name="Rivexis",
        verification_template_id=1,
        password_reset_template_id=2,
        timeout_seconds=8.0,
        sandbox=False,
    )
    return replace(base, **changes)


def test_disabled_provider_is_fail_closed_without_network_call():
    client = FakeClient(FakeResponse(201, {"messageId": "never"}))
    with pytest.raises(EmailConfigurationError, match="disabled"):
        send_template_email(
            recipient="user@example.com",
            kind="verification",
            params={"code": "123456"},
            idempotency_key="verify-12345678",
            cfg=cfg(provider="disabled"),
            client=client,
        )
    assert client.calls == []


def test_missing_brevo_key_is_rejected_before_network_call():
    client = FakeClient(FakeResponse(201, {"messageId": "never"}))
    with pytest.raises(EmailConfigurationError, match="BREVO_API_KEY"):
        send_template_email(
            recipient="user@example.com",
            kind="verification",
            params={"code": "123456"},
            idempotency_key="verify-12345678",
            cfg=cfg(api_key=""),
            client=client,
        )
    assert client.calls == []


def test_missing_flow_template_is_rejected_before_network_call():
    client = FakeClient(FakeResponse(201, {"messageId": "never"}))
    with pytest.raises(EmailConfigurationError, match="VERIFICATION_TEMPLATE_ID"):
        send_template_email(
            recipient="user@example.com",
            kind="verification",
            params={"code": "123456"},
            idempotency_key="verify-12345678",
            cfg=cfg(verification_template_id=None),
            client=client,
        )
    assert client.calls == []


def test_provider_acceptance_is_not_mislabeled_as_delivery():
    client = FakeClient(FakeResponse(201, {"messageId": "<provider-message-id>"}))
    result = send_template_email(
        recipient="user@example.com",
        kind="password_reset",
        params={"reset_url": "https://example.com/reset?token=secret-value", "expiry_minutes": 15},
        idempotency_key="reset-12345678",
        cfg=cfg(),
        client=client,
    )
    assert result.status == "accepted"
    assert result.status != "delivered"
    assert result.provider_message_id == "<provider-message-id>"
    assert result.sandbox is False
    assert len(client.calls) == 1
    _, request = client.calls[0]
    assert request["json"]["headers"]["idempotencyKey"] == "reset-12345678"
    assert request["json"]["templateId"] == 2
    assert request["headers"]["api-key"] == "test-api-key-not-a-secret"


def test_sandbox_request_is_explicitly_marked_and_dropped_by_brevo_contract():
    client = FakeClient(FakeResponse(201, {"messageId": "<sandbox-message-id>"}))
    result = send_template_email(
        recipient="user@example.com",
        kind="verification",
        params={"code": "123456", "expiry_minutes": 10},
        idempotency_key="verify-sandbox-1",
        cfg=cfg(sandbox=True),
        client=client,
    )
    assert result.status == "sandbox_accepted"
    assert result.sandbox is True
    _, request = client.calls[0]
    assert request["json"]["headers"]["X-Sib-Sandbox"] == "drop"


def test_provider_rejection_does_not_echo_sensitive_params():
    secret_code = "654321"
    client = FakeClient(FakeResponse(400, {"message": f"bad request {secret_code}"}))
    with pytest.raises(EmailDeliveryError) as caught:
        send_template_email(
            recipient="user@example.com",
            kind="verification",
            params={"code": secret_code},
            idempotency_key="verify-87654321",
            cfg=cfg(),
            client=client,
        )
    assert secret_code not in str(caught.value)
    assert "HTTP 400" in str(caught.value)


def test_network_failure_does_not_echo_request_content():
    secret = "https://example.com/reset?token=do-not-leak"
    request = httpx.Request("POST", "https://api.brevo.com/v3/smtp/email")
    client = FakeClient(exc=httpx.ConnectError("connection failed", request=request))
    with pytest.raises(EmailDeliveryError) as caught:
        send_template_email(
            recipient="user@example.com",
            kind="password_reset",
            params={"reset_url": secret},
            idempotency_key="reset-87654321",
            cfg=cfg(),
            client=client,
        )
    assert secret not in str(caught.value)


def test_malformed_success_body_remains_only_accepted():
    client = FakeClient(FakeResponse(201, ValueError("not json")))
    result = send_template_email(
        recipient="user@example.com",
        kind="verification",
        params={"code": "123456"},
        idempotency_key="verify-abcdef12",
        cfg=cfg(),
        client=client,
    )
    assert result.status == "accepted"
    assert result.provider_message_id is None


def test_invalid_recipient_and_idempotency_key_are_rejected_locally():
    client = FakeClient(FakeResponse(201, {"messageId": "never"}))
    with pytest.raises(ValueError, match="Recipient"):
        send_template_email(
            recipient="not-an-email",
            kind="verification",
            params={},
            idempotency_key="verify-12345678",
            cfg=cfg(),
            client=client,
        )
    with pytest.raises(ValueError, match="idempotency"):
        send_template_email(
            recipient="user@example.com",
            kind="verification",
            params={},
            idempotency_key="short",
            cfg=cfg(),
            client=client,
        )
    assert client.calls == []


def test_configuration_status_never_returns_api_key():
    status = validate_email_configuration(cfg())
    assert status["provider"] == "brevo"
    assert status["configured"] is True
    assert "api_key" not in status
    assert "sender_email" not in status
