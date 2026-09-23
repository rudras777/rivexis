from __future__ import annotations

from dataclasses import dataclass
import os
import re
from typing import Any, Mapping

import httpx

BREVO_SEND_URL = "https://api.brevo.com/v3/smtp/email"
_IDEMPOTENCY_RE = re.compile(r"^[A-Za-z0-9._:-]{8,128}$")


class EmailConfigurationError(RuntimeError):
    """Raised before any network call when transactional email is not safely configured."""


class EmailDeliveryError(RuntimeError):
    """Raised when Brevo does not accept a transactional email request."""


@dataclass(frozen=True)
class EmailSettings:
    provider: str
    api_key: str
    sender_email: str
    sender_name: str
    verification_template_id: int | None
    password_reset_template_id: int | None
    timeout_seconds: float
    sandbox: bool

    @classmethod
    def from_env(cls) -> "EmailSettings":
        return cls(
            provider=os.getenv("RIVEXIS_EMAIL_PROVIDER", "disabled").strip().lower(),
            api_key=os.getenv("BREVO_API_KEY", "").strip(),
            sender_email=os.getenv("RIVEXIS_BREVO_SENDER_EMAIL", "").strip(),
            sender_name=os.getenv("RIVEXIS_BREVO_SENDER_NAME", "Rivexis").strip() or "Rivexis",
            verification_template_id=_positive_int_env("RIVEXIS_BREVO_VERIFICATION_TEMPLATE_ID"),
            password_reset_template_id=_positive_int_env("RIVEXIS_BREVO_PASSWORD_RESET_TEMPLATE_ID"),
            timeout_seconds=_positive_float_env("RIVEXIS_BREVO_TIMEOUT_SECONDS", 8.0),
            sandbox=_bool_env("RIVEXIS_BREVO_SANDBOX", False),
        )


@dataclass(frozen=True)
class EmailAcceptance:
    status: str
    provider: str
    provider_message_id: str | None
    sandbox: bool


def _bool_env(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def _positive_int_env(name: str) -> int | None:
    raw = os.getenv(name, "").strip()
    if not raw:
        return None
    try:
        value = int(raw)
    except ValueError as exc:
        raise EmailConfigurationError(f"{name} must be a positive integer") from exc
    if value < 1:
        raise EmailConfigurationError(f"{name} must be a positive integer")
    return value


def _positive_float_env(name: str, default: float) -> float:
    raw = os.getenv(name, str(default)).strip()
    try:
        value = float(raw)
    except ValueError as exc:
        raise EmailConfigurationError(f"{name} must be a positive number") from exc
    if not (0 < value <= 30):
        raise EmailConfigurationError(f"{name} must be greater than 0 and at most 30 seconds")
    return value


def _valid_email(value: str) -> bool:
    if not value or len(value) > 320 or value.count("@") != 1:
        return False
    local, domain = value.rsplit("@", 1)
    return bool(local and domain and "." in domain and not any(ch.isspace() for ch in value))


def validate_email_configuration(cfg: EmailSettings | None = None) -> dict[str, object]:
    current = cfg or EmailSettings.from_env()
    if current.provider == "disabled":
        return {
            "provider": "disabled",
            "enabled": False,
            "configured": False,
            "sandbox": current.sandbox,
        }
    if current.provider != "brevo":
        raise EmailConfigurationError("RIVEXIS_EMAIL_PROVIDER must be disabled or brevo")
    missing: list[str] = []
    if not current.api_key:
        missing.append("BREVO_API_KEY")
    if not _valid_email(current.sender_email):
        missing.append("RIVEXIS_BREVO_SENDER_EMAIL")
    if missing:
        raise EmailConfigurationError("Brevo transactional email is not configured: " + ", ".join(missing))
    return {
        "provider": "brevo",
        "enabled": True,
        "configured": True,
        "sandbox": current.sandbox,
        "verification_template_configured": bool(current.verification_template_id),
        "password_reset_template_configured": bool(current.password_reset_template_id),
    }


def _validate_idempotency_key(value: str) -> str:
    key = value.strip()
    if not _IDEMPOTENCY_RE.fullmatch(key):
        raise ValueError("Email idempotency key must be 8-128 URL-safe identifier characters")
    return key


def _template_id(kind: str, cfg: EmailSettings) -> int:
    mapping = {
        "verification": cfg.verification_template_id,
        "password_reset": cfg.password_reset_template_id,
    }
    if kind not in mapping:
        raise ValueError("Unsupported transactional email template kind")
    value = mapping[kind]
    if not value:
        env_name = (
            "RIVEXIS_BREVO_VERIFICATION_TEMPLATE_ID"
            if kind == "verification"
            else "RIVEXIS_BREVO_PASSWORD_RESET_TEMPLATE_ID"
        )
        raise EmailConfigurationError(f"{env_name} is required before this email flow can send")
    return value


def send_template_email(
    *,
    recipient: str,
    kind: str,
    params: Mapping[str, Any],
    idempotency_key: str,
    cfg: EmailSettings | None = None,
    client: httpx.Client | None = None,
) -> EmailAcceptance:
    """Submit one templated message to Brevo without claiming downstream delivery.

    The caller owns flow-level rate limiting and must reuse the same idempotency key
    when retrying the same logical message. No params (OTP/reset token) are logged or
    included in exceptions from this module.
    """
    current = cfg or EmailSettings.from_env()
    status = validate_email_configuration(current)
    if not status["enabled"]:
        raise EmailConfigurationError("Transactional email provider is disabled")
    if not _valid_email(recipient.strip()):
        raise ValueError("Recipient email is invalid")
    template_id = _template_id(kind, current)
    key = _validate_idempotency_key(idempotency_key)

    provider_headers: dict[str, str] = {"idempotencyKey": key}
    if current.sandbox:
        # Brevo sandbox drop validates the request but intentionally sends no email.
        provider_headers["X-Sib-Sandbox"] = "drop"

    body = {
        "sender": {"email": current.sender_email, "name": current.sender_name},
        "to": [{"email": recipient.strip()}],
        "templateId": template_id,
        "params": dict(params),
        "headers": provider_headers,
        "tags": [f"rivexis-{kind.replace('_', '-')}"]
    }
    request_headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "api-key": current.api_key,
    }

    owns_client = client is None
    http = client or httpx.Client(timeout=current.timeout_seconds)
    try:
        response = http.post(BREVO_SEND_URL, headers=request_headers, json=body)
    except httpx.HTTPError as exc:
        raise EmailDeliveryError("Brevo transactional email request failed before provider acceptance") from exc
    finally:
        if owns_client:
            http.close()

    if response.status_code < 200 or response.status_code >= 300:
        # Provider response bodies can contain request context. Do not reflect them into
        # app errors because auth params may contain OTPs/reset URLs.
        raise EmailDeliveryError(f"Brevo rejected transactional email request with HTTP {response.status_code}")

    message_id: str | None = None
    try:
        parsed = response.json()
        candidate = parsed.get("messageId") if isinstance(parsed, dict) else None
        if isinstance(candidate, str) and candidate.strip():
            message_id = candidate.strip()[:512]
    except (ValueError, TypeError):
        message_id = None

    return EmailAcceptance(
        status="sandbox_accepted" if current.sandbox else "accepted",
        provider="brevo",
        provider_message_id=message_id,
        sandbox=current.sandbox,
    )
