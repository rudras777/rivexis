#!/usr/bin/env python3
"""Certify shared Redis provider controls across independently constructed workers.

The certification exercises an atomic shared sliding-window budget under concurrency and
shared circuit state. It reports latency without imposing an arbitrary SLO unless
RIVEXIS_REDIS_MAX_P95_MS is explicitly configured.
"""
from __future__ import annotations

import os
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

from rivexis_api.runtime_backend import RedisControlPlane
from rivexis_api.services.auth_rate_limit import _REDIS_SCRIPT as AUTH_LOGIN_BUDGET_SCRIPT


def percentile(values: list[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int(round((len(ordered) - 1) * fraction))))
    return ordered[index]


def main() -> None:
    url = os.getenv('REDIS_URL', '').strip()
    required = os.getenv('RIVEXIS_REQUIRE_REDIS_CERTIFICATION', 'false').lower() in {'1', 'true', 'yes', 'on'}
    if not url:
        if required:
            print('Redis certification: FAIL - REDIS_URL is required', file=sys.stderr)
            raise SystemExit(1)
        print('SKIP Redis multi-replica certification: set REDIS_URL (or RIVEXIS_REQUIRE_REDIS_CERTIFICATION=true to require it)')
        return

    workers = max(2, int(os.getenv('RIVEXIS_REDIS_CERT_WORKERS', '8')))
    limit = max(2, int(os.getenv('RIVEXIS_REDIS_CERT_BUDGET', '40')))
    attempts = max(limit + 1, int(os.getenv('RIVEXIS_REDIS_CERT_ATTEMPTS', str(limit * 2))))
    p95_limit_raw = os.getenv('RIVEXIS_REDIS_MAX_P95_MS', '').strip()
    p95_limit = float(p95_limit_raw) if p95_limit_raw else None

    try:
        planes = [RedisControlPlane.from_env() for _ in range(workers)]
        for plane in planes:
            plane.client.ping()
    except Exception as exc:
        print(f'Redis certification: FAIL - {exc}', file=sys.stderr)
        raise SystemExit(1)

    scope = f'cert-{uuid4()}'
    provider = 'cert-provider'
    budget_key = planes[0]._key('budget', scope, provider)
    circuit_key = planes[0]._key('circuit', scope, provider)
    auth_key = f'rivexis:auth-login:cert-{uuid4().hex}'
    global_auth_key = f'rivexis:auth-global:cert-{uuid4().hex}'
    now = time.time()
    latencies_ms: list[float] = []

    def consume(i: int) -> bool:
        plane = planes[i % workers]
        t0 = time.perf_counter()
        try:
            return plane.consume_budget(scope, provider, now, limit)
        finally:
            latencies_ms.append((time.perf_counter() - t0) * 1000)

    try:
        # All attempts intentionally share the exact timestamp. Correctness therefore
        # depends on collision-safe member IDs plus the atomic Lua budget operation.
        with ThreadPoolExecutor(max_workers=workers) as pool:
            accepted = sum(1 for ok in pool.map(consume, range(attempts)) if ok)
        if accepted != limit:
            raise AssertionError(f'shared budget accepted {accepted} requests, expected exactly {limit}')
        cardinality = int(planes[0].client.zcard(budget_key))
        if cardinality != limit:
            raise AssertionError(f'budget cardinality {cardinality}, expected {limit}')

        # P34 production authentication requires a Redis-backed shared login-attempt
        # budget. Exercise the same atomic Lua contract through independent clients so
        # the redis-distributed gate proves auth throttling cannot be bypassed by
        # switching API replicas.
        auth_limit = max(2, min(limit, 20))
        auth_attempts = auth_limit + workers
        def auth_consume(i: int) -> bool:
            client = planes[i % workers].client
            result = client.eval(
                AUTH_LOGIN_BUDGET_SCRIPT, 1, auth_key, now - 60.0, now,
                f'{now:.6f}:cert-auth-worker-{i}', auth_limit,
            )
            return bool(int(result))
        with ThreadPoolExecutor(max_workers=workers) as pool:
            auth_accepted = sum(1 for ok in pool.map(auth_consume, range(auth_attempts)) if ok)
        if auth_accepted != auth_limit:
            raise AssertionError(f'shared auth budget accepted {auth_accepted}, expected exactly {auth_limit}')
        if int(planes[0].client.zcard(auth_key)) != auth_limit:
            raise AssertionError('shared auth budget cardinality does not match accepted attempts')

        # P35 adds a cluster-wide authentication budget so rotating random account
        # identifiers cannot bypass the scrypt CPU-abuse boundary. Exercise the same
        # atomic Redis sliding-window contract across independent clients.
        global_auth_limit = max(2, min(auth_limit, 10))
        global_auth_attempts = global_auth_limit + workers
        def global_auth_consume(i: int) -> bool:
            client = planes[i % workers].client
            result = client.eval(
                AUTH_LOGIN_BUDGET_SCRIPT, 1, global_auth_key, now - 60.0, now,
                f'{now:.6f}:cert-global-auth-worker-{i}', global_auth_limit,
            )
            return bool(int(result))
        with ThreadPoolExecutor(max_workers=workers) as pool:
            global_auth_accepted = sum(1 for ok in pool.map(global_auth_consume, range(global_auth_attempts)) if ok)
        if global_auth_accepted != global_auth_limit:
            raise AssertionError(f'shared global auth budget accepted {global_auth_accepted}, expected exactly {global_auth_limit}')
        if int(planes[0].client.zcard(global_auth_key)) != global_auth_limit:
            raise AssertionError('shared global auth budget cardinality does not match accepted attempts')

        planes[0].failure(scope, provider, now, threshold=2, cooldown=30)
        planes[1].failure(scope, provider, now + 0.01, threshold=2, cooldown=30)
        state = planes[-1].circuit(scope, provider, now + 0.02)
        if state.opened_until <= now:
            raise AssertionError('circuit did not open across workers')
        planes[-1].success(scope, provider)
        if planes[0].circuit(scope, provider, now + 0.03).consecutive_failures != 0:
            raise AssertionError('circuit success reset was not shared across workers')

        p50 = statistics.median(latencies_ms) if latencies_ms else 0.0
        p95 = percentile(latencies_ms, 0.95)
        if p95_limit is not None and p95 > p95_limit:
            raise AssertionError(f'budget p95 {p95:.2f}ms exceeds configured {p95_limit:.2f}ms')
        threshold = f'; configured_p95<={p95_limit:.2f}ms' if p95_limit is not None else ''
        print(
            'Redis certification: PASS '
            f'(workers={workers}; attempts={attempts}; accepted={accepted}/{limit}; '
            f'budget p50={p50:.2f}ms p95={p95:.2f}ms; shared provider circuit; shared auth login budget; shared global auth budget{threshold})'
        )
    except Exception as exc:
        print(f'Redis certification: FAIL - {exc}', file=sys.stderr)
        raise SystemExit(1)
    finally:
        try:
            planes[0].client.delete(budget_key, circuit_key, auth_key, global_auth_key)
        except Exception:
            pass


if __name__ == '__main__':
    main()
