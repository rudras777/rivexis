from __future__ import annotations

import os
import re
import secrets
import threading
import time
from urllib.parse import urlsplit
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Iterator

from rivexis_api.version import API_VERSION

from rivexis_api.core.context import (get_span_id, get_trace_id, get_trace_sampled, reset_trace_context, reset_trace_sampled, set_trace_context, set_trace_sampled)

_TRACEPARENT_RE = re.compile(r"^00-([0-9a-f]{32})-([0-9a-f]{16})-([0-9a-f]{2})$")
_OTEL_PROVIDER = None
_OTEL_TRACER = None
_OTEL_CONFIG_KEY: tuple[str, ...] | None = None
_EXPORT_LOCK = threading.Lock()
_EXPORT_STATE: dict[str, Any] = {"attempts":0,"successes":0,"failures":0,"last_export_at":None,"last_error":None}


class TelemetryConfigurationError(RuntimeError):
    pass


@dataclass(frozen=True)
class TraceContext:
    trace_id: str
    parent_span_id: str | None
    span_id: str
    sampled: bool

    @property
    def traceparent(self) -> str:
        return f"00-{self.trace_id}-{self.span_id}-{'01' if self.sampled else '00'}"


@dataclass
class ActiveSpan:
    context: TraceContext
    _otel_span: Any | None = None

    def set_attribute(self, key: str, value: Any) -> None:
        if self._otel_span is not None and value is not None:
            self._otel_span.set_attribute(key, value)

    def set_status_code(self, status_code: int) -> None:
        self.set_attribute("http.response.status_code", int(status_code))
        if self._otel_span is not None and status_code >= 500:
            try:
                from opentelemetry.trace import Status, StatusCode
                self._otel_span.set_status(Status(StatusCode.ERROR))
            except Exception:
                pass

    def update_name(self, name: str) -> None:
        if self._otel_span is not None:
            try:
                self._otel_span.update_name(name)
            except Exception:
                pass


def _nonzero_hex(nbytes: int) -> str:
    while True:
        value = secrets.token_hex(nbytes)
        if int(value, 16) != 0:
            return value


def _parse_traceparent(value: str | None) -> tuple[str, str, bool] | None:
    incoming = (value or "").strip().lower()
    match = _TRACEPARENT_RE.fullmatch(incoming)
    if not match:
        return None
    trace_id, span_id, flags = match.groups()
    if int(trace_id, 16) == 0 or int(span_id, 16) == 0:
        return None
    return trace_id, span_id, bool(int(flags, 16) & 0x01)


def start_trace(incoming_traceparent: str | None) -> TraceContext:
    parsed = _parse_traceparent(incoming_traceparent)
    if parsed:
        trace_id, parent_span_id, sampled = parsed
        return TraceContext(trace_id=trace_id, parent_span_id=parent_span_id, span_id=_nonzero_hex(8), sampled=sampled)
    return TraceContext(trace_id=_nonzero_hex(16), parent_span_id=None, span_id=_nonzero_hex(8), sampled=True)


def otel_enabled() -> bool:
    return os.getenv("RIVEXIS_OTEL_ENABLED", "false").strip().lower() == "true"


def _otel_config_key() -> tuple[str, ...]:
    return (
        os.getenv("OTEL_SERVICE_NAME", "rivexis-api"),
        os.getenv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", ""),
        os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", ""),
        os.getenv("OTEL_EXPORTER_OTLP_TRACES_HEADERS", ""),
        os.getenv("OTEL_EXPORTER_OTLP_HEADERS", ""),
        os.getenv("OTEL_EXPORTER_OTLP_TRACES_TIMEOUT", ""),
        os.getenv("OTEL_EXPORTER_OTLP_TIMEOUT", ""),
        os.getenv("RIVEXIS_OTEL_SYNC_EXPORT", "false"),
    )


def _resolved_trace_endpoint() -> str | None:
    specific = os.getenv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", "").strip()
    if specific:
        return specific
    base = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "").strip()
    if not base:
        return None
    return base.rstrip("/") + "/v1/traces"


class _TrackingExporter:
    def __init__(self, delegate: Any):
        self.delegate = delegate

    def export(self, spans):
        with _EXPORT_LOCK:
            _EXPORT_STATE["attempts"] += 1
        try:
            result = self.delegate.export(spans)
            success_name = getattr(result, "name", str(result)).upper()
            ok = "SUCCESS" in success_name
            with _EXPORT_LOCK:
                _EXPORT_STATE["successes" if ok else "failures"] += 1
                _EXPORT_STATE["last_export_at"] = time.time()
                _EXPORT_STATE["last_error"] = None if ok else success_name
            return result
        except Exception as exc:
            with _EXPORT_LOCK:
                _EXPORT_STATE["failures"] += 1
                _EXPORT_STATE["last_export_at"] = time.time()
                _EXPORT_STATE["last_error"] = type(exc).__name__
            raise

    def shutdown(self, *args, **kwargs):
        return self.delegate.shutdown(*args, **kwargs)

    def force_flush(self, *args, **kwargs):
        method = getattr(self.delegate, "force_flush", None)
        return method(*args, **kwargs) if method else True


def telemetry_export_status() -> dict[str, Any]:
    endpoint = _resolved_trace_endpoint()
    with _EXPORT_LOCK:
        state = dict(_EXPORT_STATE)
    return {
        "enabled": otel_enabled(),
        "initialized": _OTEL_PROVIDER is not None,
        "service_name": os.getenv("OTEL_SERVICE_NAME", "rivexis-api"),
        "protocol": os.getenv("OTEL_EXPORTER_OTLP_TRACES_PROTOCOL", os.getenv("OTEL_EXPORTER_OTLP_PROTOCOL", "http/protobuf")),
        "endpoint_configured": bool(endpoint),
        "sync_export": os.getenv("RIVEXIS_OTEL_SYNC_EXPORT", "false").strip().lower() == "true",
        **state,
    }


def _production_environment() -> bool:
    return os.getenv("RIVEXIS_ENV", os.getenv("RIVEXIS_ENVIRONMENT", os.getenv("ENVIRONMENT", "development"))).strip().lower() in {"production", "prod"}


def validate_otlp_endpoint(endpoint: str | None) -> str:
    """Validate OTLP/HTTP transport without exposing endpoint credentials.

    Production permits plaintext HTTP only to a loopback collector/sidecar. Remote
    collectors must use HTTPS because OTLP spans and exporter headers can contain
    operationally sensitive metadata/authentication material. URL userinfo, query and
    fragment components are forbidden to keep collector credentials out of URI surfaces.
    """
    raw = str(endpoint or "").strip()
    if not raw:
        raise TelemetryConfigurationError("OTLP trace endpoint is not configured")
    try:
        parsed = urlsplit(raw)
    except ValueError as exc:
        raise TelemetryConfigurationError("OTLP trace endpoint is invalid") from exc
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise TelemetryConfigurationError("OTLP trace endpoint must use http or https")
    if parsed.username is not None or parsed.password is not None or parsed.query or parsed.fragment:
        raise TelemetryConfigurationError("OTLP trace endpoint must not contain userinfo, query, or fragment components")
    loopback = parsed.hostname.lower() in {"127.0.0.1", "localhost", "::1"}
    if _production_environment() and parsed.scheme != "https" and not loopback:
        raise TelemetryConfigurationError("Production OTLP export requires HTTPS unless the collector is loopback-local")
    return raw


def _record_exception_class(span: Any, exc: BaseException) -> None:
    """Record only a stable exception class, never message/stacktrace text.

    OpenTelemetry ``record_exception`` serializes the exception message and stack trace.
    Those can contain tenant inputs, SQL fragments or secret-bearing provider URLs.
    Rivexis therefore exports only the exception type and an ERROR status.
    """
    try:
        from opentelemetry.trace import Status, StatusCode
        span.set_attribute("exception.type", type(exc).__name__)
        span.set_status(Status(StatusCode.ERROR))
    except Exception:
        pass


def init_telemetry(*, force: bool = False):
    """Initialize an optional OTLP/HTTP trace exporter.

    Rivexis does not silently enable network telemetry. Set RIVEXIS_OTEL_ENABLED=true
    and an OTLP endpoint to export spans. The exporter uses the official OpenTelemetry
    Python SDK and OTLP/HTTP protobuf exporter when available.
    """
    global _OTEL_PROVIDER, _OTEL_TRACER, _OTEL_CONFIG_KEY
    if not otel_enabled():
        return None
    key = _otel_config_key()
    if _OTEL_PROVIDER is not None and not force and _OTEL_CONFIG_KEY == key:
        return _OTEL_TRACER
    if force:
        shutdown_telemetry()
    endpoint = _resolved_trace_endpoint()
    if not endpoint:
        raise TelemetryConfigurationError(
            "RIVEXIS_OTEL_ENABLED=true requires OTEL_EXPORTER_OTLP_TRACES_ENDPOINT or OTEL_EXPORTER_OTLP_ENDPOINT"
        )
    endpoint = validate_otlp_endpoint(endpoint)
    try:
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor, SimpleSpanProcessor
    except Exception as exc:
        raise TelemetryConfigurationError(
            "OTLP export is enabled but OpenTelemetry SDK/exporter packages are not installed; install the observability extra"
        ) from exc

    exporter = _TrackingExporter(OTLPSpanExporter(endpoint=endpoint))
    provider = TracerProvider(
        resource=Resource.create(
            {
                "service.name": os.getenv("OTEL_SERVICE_NAME", "rivexis-api"),
                "service.version": os.getenv("RIVEXIS_RELEASE_VERSION", API_VERSION),
                "deployment.environment.name": os.getenv("RIVEXIS_ENVIRONMENT", os.getenv("ENVIRONMENT", "development")),
            }
        )
    )
    processor = (
        SimpleSpanProcessor(exporter)
        if os.getenv("RIVEXIS_OTEL_SYNC_EXPORT", "false").strip().lower() == "true"
        else BatchSpanProcessor(exporter)
    )
    provider.add_span_processor(processor)
    _OTEL_PROVIDER = provider
    _OTEL_TRACER = provider.get_tracer("rivexis-api", os.getenv("RIVEXIS_RELEASE_VERSION", API_VERSION))
    _OTEL_CONFIG_KEY = key
    return _OTEL_TRACER


def shutdown_telemetry() -> None:
    global _OTEL_PROVIDER, _OTEL_TRACER, _OTEL_CONFIG_KEY
    provider = _OTEL_PROVIDER
    _OTEL_PROVIDER = None
    _OTEL_TRACER = None
    _OTEL_CONFIG_KEY = None
    if provider is not None:
        try:
            provider.shutdown()
        except Exception:
            pass


def _otel_parent_context(trace_id: str, span_id: str, sampled: bool, *, remote: bool):
    from opentelemetry import trace as ot_trace
    from opentelemetry.trace import NonRecordingSpan, SpanContext, TraceFlags
    from opentelemetry.trace import set_span_in_context

    flags = TraceFlags(TraceFlags.SAMPLED if sampled else TraceFlags.DEFAULT)
    parent = SpanContext(
        trace_id=int(trace_id, 16),
        span_id=int(span_id, 16),
        is_remote=remote,
        trace_flags=flags,
        trace_state=ot_trace.DEFAULT_TRACE_STATE,
    )
    return set_span_in_context(NonRecordingSpan(parent))


def _kind(value: str):
    from opentelemetry.trace import SpanKind
    return {
        "server": SpanKind.SERVER,
        "client": SpanKind.CLIENT,
        "producer": SpanKind.PRODUCER,
        "consumer": SpanKind.CONSUMER,
    }.get(value.lower(), SpanKind.INTERNAL)


@contextmanager
def request_span(
    name: str,
    *,
    incoming_traceparent: str | None = None,
    attributes: dict[str, Any] | None = None,
) -> Iterator[ActiveSpan]:
    parsed = _parse_traceparent(incoming_traceparent)
    if otel_enabled():
        tracer = init_telemetry()
        parent_context = None
        parent_span_id = None
        if parsed:
            trace_id, parent_span_id, sampled = parsed
            parent_context = _otel_parent_context(trace_id, parent_span_id, sampled, remote=True)
        span = tracer.start_span(name, context=parent_context, kind=_kind("server"), attributes=attributes or {})
        sc = span.get_span_context()
        ctx = TraceContext(
            trace_id=f"{sc.trace_id:032x}",
            parent_span_id=parent_span_id,
            span_id=f"{sc.span_id:016x}",
            sampled=bool(int(sc.trace_flags) & 0x01),
        )
        token = set_trace_context(ctx.trace_id, ctx.span_id)
        sampled_token = set_trace_sampled(ctx.sampled)
        active = ActiveSpan(ctx, span)
        try:
            yield active
        except BaseException as exc:
            _record_exception_class(span, exc)
            raise
        finally:
            reset_trace_sampled(sampled_token)
            reset_trace_context(token)
            span.end()
        return

    ctx = start_trace(incoming_traceparent)
    token = set_trace_context(ctx.trace_id, ctx.span_id)
    sampled_token = set_trace_sampled(ctx.sampled)
    try:
        yield ActiveSpan(ctx, None)
    finally:
        reset_trace_sampled(sampled_token)
        reset_trace_context(token)


@contextmanager
def child_span(name: str, *, kind: str = "internal", attributes: dict[str, Any] | None = None) -> Iterator[ActiveSpan]:
    trace_id = get_trace_id()
    parent_span_id = get_span_id()
    parent_sampled = get_trace_sampled()
    if not trace_id or not parent_span_id:
        with request_span(name, attributes=attributes) as active:
            yield active
        return

    if otel_enabled():
        tracer = init_telemetry()
        parent_context = _otel_parent_context(trace_id, parent_span_id, parent_sampled, remote=False)
        span = tracer.start_span(name, context=parent_context, kind=_kind(kind), attributes=attributes or {})
        sc = span.get_span_context()
        ctx = TraceContext(
            trace_id=f"{sc.trace_id:032x}",
            parent_span_id=parent_span_id,
            span_id=f"{sc.span_id:016x}",
            sampled=bool(int(sc.trace_flags) & 0x01),
        )
        token = set_trace_context(ctx.trace_id, ctx.span_id)
        sampled_token = set_trace_sampled(ctx.sampled)
        active = ActiveSpan(ctx, span)
        try:
            yield active
        except BaseException as exc:
            _record_exception_class(span, exc)
            raise
        finally:
            reset_trace_sampled(sampled_token)
            reset_trace_context(token)
            span.end()
        return

    ctx = TraceContext(trace_id=trace_id, parent_span_id=parent_span_id, span_id=_nonzero_hex(8), sampled=parent_sampled)
    token = set_trace_context(ctx.trace_id, ctx.span_id)
    sampled_token = set_trace_sampled(ctx.sampled)
    try:
        yield ActiveSpan(ctx, None)
    finally:
        reset_trace_sampled(sampled_token)
        reset_trace_context(token)


def trace_headers() -> dict[str, str]:
    trace_id = get_trace_id()
    span_id = get_span_id()
    if not trace_id or not span_id:
        return {}
    return {"traceparent": f"00-{trace_id}-{span_id}-{'01' if get_trace_sampled() else '00'}", "X-Rivexis-Trace-ID": trace_id}
