#!/usr/bin/env python3
"""Certify PostgreSQL provider budgets and circuit state across worker instances."""

from __future__ import annotations

import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

from rivexis_api.postgres_control import clear_budget, consume_budget
from rivexis_api.runtime_backend import PostgresControlPlane
from rivexis_api.services.db import SessionLocal, engine
from sqlalchemy import text


def main() -> int:
    if engine.dialect.name != "postgresql":
        print("PostgreSQL distributed controls certification: FAIL - DATABASE_URL is not PostgreSQL", file=sys.stderr)
        return 1

    workers = max(2, int(os.getenv("RIVEXIS_POSTGRES_CONTROL_CERT_WORKERS", "8")))
    limit = max(2, int(os.getenv("RIVEXIS_POSTGRES_CONTROL_CERT_BUDGET", "40")))
    attempts = max(limit + 1, int(os.getenv("RIVEXIS_POSTGRES_CONTROL_CERT_ATTEMPTS", str(limit * 2))))
    nonce = uuid4().hex
    scope = f"cert-{nonce}"
    provider = "cert-provider"
    budget = f"rivexis:provider-control:{scope}:{provider}"
    auth_global = f"rivexis:auth-global:cert:{nonce}"
    auth_account = f"rivexis:auth-login:cert:{nonce}"
    now = time.time()
    planes = [PostgresControlPlane() for _ in range(workers)]

    try:
        def provider_consume(index: int) -> bool:
            return planes[index % workers].consume_budget(scope, provider, now, limit)

        with ThreadPoolExecutor(max_workers=workers) as pool:
            accepted = sum(1 for ok in pool.map(provider_consume, range(attempts)) if ok)
        if accepted != limit:
            raise AssertionError(f"shared provider budget accepted {accepted}, expected {limit}")

        auth_limit = max(2, min(limit, 20))
        with ThreadPoolExecutor(max_workers=workers) as pool:
            global_accepted = sum(
                1 for ok in pool.map(lambda _index: consume_budget(auth_global, now, auth_limit), range(attempts)) if ok
            )
        if global_accepted != auth_limit:
            raise AssertionError(f"shared global auth budget accepted {global_accepted}, expected {auth_limit}")
        with ThreadPoolExecutor(max_workers=workers) as pool:
            account_accepted = sum(
                1 for ok in pool.map(lambda _index: consume_budget(auth_account, now, auth_limit), range(attempts)) if ok
            )
        if account_accepted != auth_limit:
            raise AssertionError(f"shared account auth budget accepted {account_accepted}, expected {auth_limit}")

        planes[0].failure(scope, provider, now, threshold=2, cooldown=30)
        opened = planes[1].failure(scope, provider, now + 0.01, threshold=2, cooldown=30)
        if opened.opened_until <= now:
            raise AssertionError("shared provider circuit did not open")
        planes[-1].success(scope, provider)
        if planes[0].circuit(scope, provider, now + 0.02).consecutive_failures != 0:
            raise AssertionError("shared provider circuit did not reset")

        print(
            "PostgreSQL distributed controls certification: PASS "
            f"(workers={workers}; attempts={attempts}; provider accepted={accepted}/{limit}; "
            "shared global/account auth budgets; shared provider circuit)"
        )
        return 0
    except Exception as exc:  # noqa: BLE001 - certification must turn any backend failure into FAIL
        print(f"PostgreSQL distributed controls certification: FAIL - {exc}", file=sys.stderr)
        return 1
    finally:
        for key in (budget, auth_global, auth_account):
            try:
                clear_budget(key)
            except Exception as exc:  # noqa: BLE001 - best-effort cleanup after a reported result
                print(f"PostgreSQL control certification cleanup warning: {exc.__class__.__name__}", file=sys.stderr)
        try:
            with SessionLocal.begin() as session:
                session.execute(
                    text("DELETE FROM runtime_provider_circuits WHERE scope = :scope AND provider_id = :provider"),
                    {"scope": scope, "provider": provider},
                )
        except Exception as exc:  # noqa: BLE001 - best-effort cleanup after a reported result
            print(f"PostgreSQL circuit cleanup warning: {exc.__class__.__name__}", file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
