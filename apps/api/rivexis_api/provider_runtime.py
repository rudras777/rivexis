from __future__ import annotations

import os
import threading
import time
from collections import defaultdict
from dataclasses import asdict, dataclass
from typing import Any, Callable, TypeVar
from urllib.parse import urlsplit

from rivexis_api.core.context import get_workspace_id
from rivexis_api.core.telemetry import child_span
from rivexis_api.runtime_backend import ControlPlane, MemoryControlPlane, PostgresControlPlane, RedisControlPlane

T = TypeVar("T")


def safe_provider_endpoint(provider_id: str, endpoint: str | None) -> str:
    """Return a provenance label that cannot contain provider credentials.

    Provider URLs frequently embed credentials in paths (Alchemy/QuickNode), query
    parameters, or userinfo. Runtime telemetry is visible to authenticated workspace
    users, so raw URLs must never be persisted or returned. Non-URL labels such as
    ``eth_call`` are retained because they cannot carry URI credentials.
    """
    raw = str(endpoint or "").strip()
    if not raw:
        return ""
    if "://" not in raw:
        return raw[:160]
    try:
        parsed = urlsplit(raw)
    except ValueError:
        return f"{provider_id}:external"
    scheme = (parsed.scheme or "external").lower()
    host = (parsed.hostname or "").lower()
    # Do not expose endpoint-specific hostnames for RPC providers; some vendors put
    # tenant identifiers in the hostname as well as secrets in the path.
    if provider_id in {"alchemy", "quicknode", "direct_rpc"}:
        return f"{provider_id}:json-rpc"
    if not host:
        return f"{provider_id}:external"
    # Keep only the public origin for ordinary REST providers. Userinfo, path, query
    # and fragment are intentionally dropped.
    port = f":{parsed.port}" if parsed.port else ""
    return f"{scheme}://{host}{port}"[:200]


class RuntimeControlError(RuntimeError):
    def __init__(self, message: str, *, provider_id: str, code: str, retryable: bool = True):
        super().__init__(message)
        self.provider_id = provider_id
        self.code = code
        self.retryable = retryable


@dataclass
class Telemetry:
    logical_calls: int = 0
    attempts: int = 0
    successes: int = 0
    failures: int = 0
    retries: int = 0
    cache_hits: int = 0
    rate_limited: int = 0
    circuit_rejections: int = 0
    total_latency_ms: float = 0.0
    estimated_cost_usd: float = 0.0
    last_error_code: str | None = None
    last_success_at: float | None = None
    last_failure_at: float | None = None


_lock = threading.RLock()
_telemetry: dict[tuple[str, str], Telemetry] = defaultdict(Telemetry)
_cache: dict[tuple[str, str, str, str], tuple[float, Any]] = {}
_singleflight_locks: dict[tuple[str, str, str, str], threading.Lock] = {}
_memory_backend = MemoryControlPlane()
_backend_override: ControlPlane | None = None
_redis_backend: RedisControlPlane | None = None
_postgres_backend: PostgresControlPlane | None = None


def _scope() -> str:
    return get_workspace_id() or "GLOBAL"


def _env_int(name: str, default: int) -> int:
    try:
        return max(0, int(os.getenv(name, str(default))))
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    try:
        return max(0.0, float(os.getenv(name, str(default))))
    except ValueError:
        return default


def _provider_limit(provider_id: str) -> int:
    specific = f"RIVEXIS_PROVIDER_{provider_id.upper()}_CALLS_PER_MINUTE"
    return _env_int(specific, _env_int("RIVEXIS_PROVIDER_CALLS_PER_MINUTE", 120))


def _cost_per_attempt(provider_id: str) -> float:
    specific = f"RIVEXIS_PROVIDER_{provider_id.upper()}_ESTIMATED_COST_USD_PER_ATTEMPT"
    return _env_float(specific, _env_float("RIVEXIS_PROVIDER_ESTIMATED_COST_USD_PER_ATTEMPT", 0.0))


def _control_plane() -> ControlPlane:
    global _postgres_backend, _redis_backend
    if _backend_override is not None:
        return _backend_override
    configured = os.getenv("RIVEXIS_PROVIDER_CONTROL_BACKEND", "memory").strip().lower()
    if configured == "postgres":
        if _postgres_backend is None:
            _postgres_backend = PostgresControlPlane.from_env()
        return _postgres_backend
    if configured != "redis":
        return _memory_backend
    if _redis_backend is None:
        _redis_backend = RedisControlPlane.from_env()
    return _redis_backend


def set_control_plane_for_tests(backend: ControlPlane | None) -> None:
    global _backend_override
    _backend_override = backend


def _persist_event(
    *,
    workspace_id: str,
    provider_id: str,
    operation: str,
    endpoint: str,
    status: str,
    latency_ms: float,
    attempts: int,
    retries: int,
    estimated_cost_usd: float,
    error_class: str | None = None,
    cache_hit: bool = False,
) -> None:
    if workspace_id == "GLOBAL":
        return
    try:
        from rivexis_api.services.store import record_provider_request_event
        record_provider_request_event(
            workspace_id=workspace_id,
            provider_key=provider_id,
            operation=operation,
            endpoint=endpoint,
            status=status,
            latency_ms=latency_ms,
            attempts=attempts,
            retries=retries,
            estimated_cost_usd=estimated_cost_usd,
            error_class=error_class,
            cache_hit=cache_hit,
        )
    except Exception:
        # Provider availability must not depend on observability persistence. Production
        # deployments should alert on telemetry-write failures through the logging pipeline.
        return


def execute(
    provider_id: str,
    operation: str,
    fn: Callable[[], T],
    *,
    endpoint: str = "",
    cache_key: str | None = None,
    cache_ttl_seconds: float = 0.0,
) -> T:
    """Execute one logical provider request under cache, dedupe, budget, retry and circuit controls.

    Cache values remain process-local because the runtime accepts arbitrary Python results.
    Concurrent cacheable requests for the same workspace/provider/operation/key are coalesced
    by a per-key lock; followers re-check the cache after the leader completes. Rate budgets
    and circuit state can be distributed with PostgreSQL or Redis by setting
    RIVEXIS_PROVIDER_CONTROL_BACKEND=postgres or redis. Every workspace-scoped logical call
    is separately persisted to provider_requests for operational/cost history.
    """
    endpoint = safe_provider_endpoint(provider_id, endpoint)
    if cache_key and cache_ttl_seconds > 0:
        flight_key = (_scope(), provider_id, operation, cache_key)
        with _lock:
            flight_lock = _singleflight_locks.setdefault(flight_key, threading.Lock())
        with flight_lock:
            return _execute_impl(
                provider_id, operation, fn, endpoint=endpoint, cache_key=cache_key,
                cache_ttl_seconds=cache_ttl_seconds,
            )
    return _execute_impl(
        provider_id, operation, fn, endpoint=endpoint, cache_key=cache_key,
        cache_ttl_seconds=cache_ttl_seconds,
    )


def _execute_impl(
    provider_id: str,
    operation: str,
    fn: Callable[[], T],
    *,
    endpoint: str = "",
    cache_key: str | None = None,
    cache_ttl_seconds: float = 0.0,
) -> T:
    scope = _scope()
    key = (scope, provider_id)
    backend = _control_plane()
    now = time.time()
    with _lock:
        stat = _telemetry[key]
        stat.logical_calls += 1
        if cache_key and cache_ttl_seconds > 0:
            ckey = (scope, provider_id, operation, cache_key)
            item = _cache.get(ckey)
            mono = time.monotonic()
            if item and item[0] > mono:
                stat.cache_hits += 1
                _persist_event(
                    workspace_id=scope, provider_id=provider_id, operation=operation, endpoint=endpoint,
                    status="CACHE_HIT", latency_ms=0.0, attempts=0, retries=0,
                    estimated_cost_usd=0.0, cache_hit=True,
                )
                return item[1]
            if item:
                _cache.pop(ckey, None)
        circuit = backend.circuit(scope, provider_id, now)
        if circuit.opened_until > now:
            stat.circuit_rejections += 1
            _persist_event(
                workspace_id=scope, provider_id=provider_id, operation=operation, endpoint=endpoint,
                status="CIRCUIT_OPEN", latency_ms=0.0, attempts=0, retries=0,
                estimated_cost_usd=0.0, error_class="CIRCUIT_OPEN",
            )
            raise RuntimeControlError(
                f"Circuit open for provider {provider_id}", provider_id=provider_id, code="CIRCUIT_OPEN", retryable=True
            )

    max_retries = _env_int("RIVEXIS_PROVIDER_MAX_RETRIES", 2)
    base = _env_float("RIVEXIS_PROVIDER_RETRY_BASE_SECONDS", 0.05)
    cap = _env_float("RIVEXIS_PROVIDER_RETRY_MAX_SECONDS", 0.5)
    threshold = max(1, _env_int("RIVEXIS_PROVIDER_CIRCUIT_FAILURE_THRESHOLD", 4))
    cooldown = _env_float("RIVEXIS_PROVIDER_CIRCUIT_COOLDOWN_SECONDS", 30.0)
    cost_per_attempt = _cost_per_attempt(provider_id)
    logical_started = time.perf_counter()
    attempts_used = 0
    retries_used = 0

    for attempt in range(max_retries + 1):
        started = time.perf_counter()
        now = time.time()
        if not backend.consume_budget(scope, provider_id, now, _provider_limit(provider_id)):
            with _lock:
                _telemetry[key].rate_limited += 1
            _persist_event(
                workspace_id=scope, provider_id=provider_id, operation=operation, endpoint=endpoint,
                status="LOCAL_RATE_LIMIT", latency_ms=(time.perf_counter()-logical_started)*1000,
                attempts=attempts_used, retries=retries_used,
                estimated_cost_usd=attempts_used*cost_per_attempt, error_class="LOCAL_RATE_LIMIT",
            )
            raise RuntimeControlError(
                f"Provider request budget exceeded for {provider_id}", provider_id=provider_id, code="LOCAL_RATE_LIMIT", retryable=True
            )
        attempts_used += 1
        with _lock:
            _telemetry[key].attempts += 1
        try:
            with child_span(
                f"provider.{provider_id}.{operation.lower()}",
                kind="client",
                attributes={
                    "rivexis.provider.id": provider_id,
                    "rivexis.provider.operation": operation,
                    "rivexis.provider.attempt": attempt + 1,
                    # Never export the raw provider URL. RPC credentials frequently live
                    # in host/path/query components and OTLP is an external sink.
                    "server.address": safe_provider_endpoint(provider_id, endpoint),
                },
            ) as provider_span:
                value = fn()
                provider_span.set_attribute("rivexis.provider.result", "success")
        except Exception as exc:  # ProviderError is intentionally duck-typed to avoid a cycle.
            latency = (time.perf_counter() - started) * 1000
            code = str(getattr(exc, "code", "PROVIDER_ERROR"))
            retryable = bool(getattr(exc, "retryable", False))
            with _lock:
                _telemetry[key].total_latency_ms += latency
                _telemetry[key].estimated_cost_usd += cost_per_attempt
                if retryable and attempt < max_retries:
                    _telemetry[key].retries += 1
                    retries_used += 1
                else:
                    stat = _telemetry[key]
                    stat.failures += 1
                    stat.last_error_code = code
                    stat.last_failure_at = time.time()
                    backend.failure(scope, provider_id, time.time(), threshold, cooldown)
            if retryable and attempt < max_retries:
                delay = min(cap, base * (2 ** attempt))
                if delay:
                    time.sleep(delay)
                continue
            _persist_event(
                workspace_id=scope, provider_id=provider_id, operation=operation, endpoint=endpoint,
                status="FAILED", latency_ms=(time.perf_counter()-logical_started)*1000,
                attempts=attempts_used, retries=retries_used,
                estimated_cost_usd=attempts_used*cost_per_attempt, error_class=code,
            )
            raise
        else:
            latency = (time.perf_counter() - started) * 1000
            with _lock:
                stat = _telemetry[key]
                stat.total_latency_ms += latency
                stat.estimated_cost_usd += cost_per_attempt
                stat.successes += 1
                stat.last_success_at = time.time()
                backend.success(scope, provider_id)
                if cache_key and cache_ttl_seconds > 0:
                    _cache[(scope, provider_id, operation, cache_key)] = (time.monotonic() + cache_ttl_seconds, value)
            _persist_event(
                workspace_id=scope, provider_id=provider_id, operation=operation, endpoint=endpoint,
                status="SUCCESS", latency_ms=(time.perf_counter()-logical_started)*1000,
                attempts=attempts_used, retries=retries_used,
                estimated_cost_usd=attempts_used*cost_per_attempt,
            )
            return value
    raise AssertionError("unreachable")


def snapshot(workspace_id: str | None = None) -> dict[str, Any]:
    scope = workspace_id or _scope()
    backend = _control_plane()
    out: dict[str, Any] = {"scope": scope, "control_backend": backend.name, "providers": {}}
    with _lock:
        providers = sorted(pid for (s, pid) in _telemetry if s == scope)
        for provider_id in providers:
            stat = _telemetry[(scope, provider_id)]
            circuit = backend.circuit(scope, provider_id, time.time())
            data = asdict(stat)
            data["average_attempt_latency_ms"] = round(stat.total_latency_ms / stat.attempts, 2) if stat.attempts else None
            data["circuit"] = {
                "state": "OPEN" if circuit.opened_until > time.time() else "CLOSED",
                "consecutive_failures": circuit.consecutive_failures,
                "opens_for_seconds": max(0.0, round(circuit.opened_until - time.time(), 3)),
            }
            data["calls_per_minute_budget"] = _provider_limit(provider_id)
            data["estimated_cost_per_attempt_usd"] = _cost_per_attempt(provider_id)
            out["providers"][provider_id] = data
    return out


def reset_runtime_state() -> None:
    global _postgres_backend, _redis_backend
    with _lock:
        _telemetry.clear()
        _cache.clear()
        _singleflight_locks.clear()
    _memory_backend.reset()
    if _backend_override is not None:
        _backend_override.reset()
    _redis_backend = None
    _postgres_backend = None
