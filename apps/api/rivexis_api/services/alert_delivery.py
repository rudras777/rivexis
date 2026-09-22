from __future__ import annotations
import hashlib
import hmac
import json
import os
import time
from typing import Any
from urllib.parse import urlsplit

import httpx

from rivexis_api.core.telemetry import child_span, trace_headers
from rivexis_api.services.store import due_alerts, mark_alert_delivery


class DeliveryNotConfigured(RuntimeError):
    pass


class DeliveryConfigurationError(DeliveryNotConfigured):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


class WebhookDeliveryError(RuntimeError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def delivery_log_summary(results: list[dict[str, Any]]):
    """Return metadata-only alert-delivery counters safe for shared stdout logs.

    Never include workspace/alert identifiers, payloads, webhook bodies, delivery
    metadata, URLs, database-derived values, or free-form exception messages.
    """
    summary = {
        "workspace_count": len(results),
        "processed": 0,
        "skipped": 0,
        "delivered": 0,
        "retry": 0,
        "dead_letter": 0,
        "configuration_degraded": False,
    }
    for result in results:
        summary["processed"] += max(0, int(result.get("processed", 0) or 0))
        summary["skipped"] += max(0, int(result.get("skipped", 0) or 0))
        if result.get("reason"):
            summary["configuration_degraded"] = True
        for item in result.get("items", []) or []:
            outcome = str(item.get("result", "")).strip()
            if outcome in {"delivered", "retry", "dead_letter"}:
                summary[outcome] += 1
    return summary


def delivery_error_type(exc: BaseException) -> str:
    """Return only the stable exception class for shared operational logs."""
    return type(exc).__name__


def delivery_failure_code(exc: BaseException) -> str:
    """Return a stable persistence-safe failure code without endpoint/error text."""
    if isinstance(exc, (DeliveryConfigurationError, WebhookDeliveryError)):
        return exc.code
    if isinstance(exc, DeliveryNotConfigured):
        return "delivery_not_configured"
    if isinstance(exc, httpx.TimeoutException):
        return "webhook_timeout"
    if isinstance(exc, httpx.HTTPError):
        return "webhook_transport_error"
    name = type(exc).__name__
    safe = "".join(ch for ch in name if ch.isalnum() or ch == "_")[:80] or "Exception"
    return f"delivery_error_{safe}"


def _settings():
    return {
        "url": os.getenv("RIVEXIS_ALERT_WEBHOOK_URL", "").strip(),
        "secret": os.getenv("RIVEXIS_ALERT_WEBHOOK_SECRET", "").strip(),
        "scope": os.getenv("RIVEXIS_ALERT_WEBHOOK_SCOPE", "").strip().lower(),
        "max_attempts": int(os.getenv("RIVEXIS_ALERT_MAX_ATTEMPTS", "5")),
        "retry_base_seconds": int(os.getenv("RIVEXIS_ALERT_RETRY_BASE_SECONDS", "30")),
        "timeout": float(os.getenv("RIVEXIS_ALERT_WEBHOOK_TIMEOUT_SECONDS", "8")),
        "environment": os.getenv("RIVEXIS_ENV", "development").strip().lower(),
    }


def validate_alert_webhook_configuration(cfg: dict[str, Any] | None = None) -> dict[str, Any]:
    """Fail closed on unsafe outbound alert webhook configuration.

    Development may use unsigned HTTP receivers for local testing. Production-like
    environments require TLS, HMAC authentication, and an explicit `internal_gateway`
    scope because this single environment-level sink receives alerts across workspaces.
    It must therefore be a Rivexis-controlled multi-tenant delivery boundary, not a
    customer-specific endpoint. URL userinfo/fragments are forbidden in every environment
    so secrets cannot be embedded in a target URI or accidentally propagated in
    transport diagnostics.
    """
    cfg = dict(cfg or _settings())
    url = str(cfg.get("url") or "").strip()
    if not url:
        return cfg
    try:
        target = urlsplit(url)
    except ValueError as exc:
        raise DeliveryConfigurationError("webhook_url_invalid") from exc
    if target.scheme not in {"http", "https"} or not target.hostname:
        raise DeliveryConfigurationError("webhook_url_invalid")
    if target.username is not None or target.password is not None:
        raise DeliveryConfigurationError("webhook_url_userinfo_forbidden")
    if target.fragment:
        raise DeliveryConfigurationError("webhook_url_fragment_forbidden")
    if target.query:
        raise DeliveryConfigurationError("webhook_url_query_forbidden")
    production = str(cfg.get("environment") or "").lower() in {"production", "prod"}
    if production and target.scheme != "https":
        raise DeliveryConfigurationError("production_webhook_requires_https")
    if production and not str(cfg.get("secret") or ""):
        raise DeliveryConfigurationError("production_webhook_requires_hmac_secret")
    if production and str(cfg.get("scope") or "").strip().lower() != "internal_gateway":
        raise DeliveryConfigurationError("production_webhook_requires_internal_gateway_scope")
    return cfg


def _outbound_alert(alert: dict[str, Any]) -> dict[str, Any]:
    """Exclude local delivery diagnostics from outbound retry payloads."""
    return {key: value for key, value in alert.items() if key != "last_delivery_error"}


def send_webhook(alert: dict[str, Any]):
    cfg = validate_alert_webhook_configuration()
    if not cfg["url"]:
        raise DeliveryNotConfigured("delivery_not_configured")
    body = json.dumps(
        {"event": "rivexis.alert", "alert": _outbound_alert(alert)},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode()
    started = time.perf_counter()
    try:
        with child_span(
            "rivexis.alert.webhook",
            kind="producer",
            # Shared OTLP exports must not carry tenant alert identifiers.
            attributes={"messaging.system": "webhook", "rivexis.delivery.kind": "alert"},
        ):
            # Headers are created inside the child span so the receiver gets the child traceparent.
            timestamp = str(int(time.time()))
            headers = {
                **trace_headers(), "Content-Type": "application/json", "X-Rivexis-Alert-Id": alert["id"],
                "X-Rivexis-Timestamp": timestamp, "X-Rivexis-Signature-Version": "v1",
            }
            if cfg["secret"]:
                signed = timestamp.encode() + b"." + body
                headers["X-Rivexis-Signature"] = "sha256=" + hmac.new(cfg["secret"].encode(), signed, hashlib.sha256).hexdigest()
            with httpx.Client(timeout=cfg["timeout"], follow_redirects=False) as client:
                response = client.post(cfg["url"], content=body, headers=headers)
    except httpx.TimeoutException as exc:
        raise WebhookDeliveryError("webhook_timeout") from exc
    except httpx.HTTPError as exc:
        raise WebhookDeliveryError("webhook_transport_error") from exc
    latency = (time.perf_counter() - started) * 1000
    if response.status_code < 200 or response.status_code >= 300:
        raise WebhookDeliveryError(f"webhook_http_{response.status_code}")
    return {"status_code": response.status_code, "latency_ms": round(latency, 3)}


def process_due_alerts(workspace_id: str, limit: int = 50, sender=send_webhook):
    cfg = _settings()
    items = due_alerts(workspace_id, limit)
    if sender is send_webhook:
        if not cfg["url"]:
            return {
                "workspace_id": workspace_id,
                "processed": 0,
                "skipped": len(items),
                "reason": "delivery_not_configured",
                "items": [],
            }
        try:
            validate_alert_webhook_configuration(cfg)
        except DeliveryConfigurationError as exc:
            return {
                "workspace_id": workspace_id,
                "processed": 0,
                "skipped": len(items),
                "reason": exc.code,
                "items": [],
            }
    results = []
    for alert in items:
        try:
            meta = sender(alert)
            updated = mark_alert_delivery(
                alert["id"],
                success=True,
                max_attempts=cfg["max_attempts"],
                retry_base_seconds=cfg["retry_base_seconds"],
            )
            results.append({"id": alert["id"], "result": "delivered", "delivery": meta, "alert": updated})
        except DeliveryNotConfigured as exc:
            code = delivery_failure_code(exc)
            return {
                "workspace_id": workspace_id,
                "processed": len(results),
                "skipped": len(items) - len(results),
                "reason": code,
                "items": results,
            }
        except Exception as exc:
            code = delivery_failure_code(exc)
            updated = mark_alert_delivery(
                alert["id"],
                success=False,
                error=code,
                max_attempts=cfg["max_attempts"],
                retry_base_seconds=cfg["retry_base_seconds"],
            )
            results.append({"id": alert["id"], "result": updated["delivery_status"], "error": code, "alert": updated})
    return {"workspace_id": workspace_id, "processed": len(results), "skipped": 0, "items": results}
