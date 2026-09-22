from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from sqlalchemy import text


@dataclass
class StoredCircuitState:
    consecutive_failures: int = 0
    opened_until: float = 0.0


def _session_factory():
    # Keep database initialization lazy so local/unit-test imports can continue to use
    # SQLite without touching the PostgreSQL-only control tables.
    from rivexis_api.services.db import SessionLocal

    return SessionLocal


def _require_postgres(session: Any) -> None:
    if session.get_bind().dialect.name != "postgresql":
        raise RuntimeError("PostgreSQL distributed controls require a PostgreSQL DATABASE_URL")


def _lock(session: Any, key: str) -> None:
    # hashtextextended can collide, but a collision only serializes unrelated buckets;
    # it cannot weaken a budget or corrupt state.
    session.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"), {"key": key})


def consume_budget(bucket: str, now: float, limit: int) -> bool:
    if limit == 0:
        return False
    sessions = _session_factory()
    with sessions.begin() as session:
        _require_postgres(session)
        _lock(session, "budget:" + bucket)
        session.execute(
            text("DELETE FROM runtime_rate_events WHERE bucket = :bucket AND occurred_at <= :cutoff"),
            {"bucket": bucket, "cutoff": now - 60.0},
        )
        count = int(
            session.execute(
                text("SELECT count(*) FROM runtime_rate_events WHERE bucket = :bucket"),
                {"bucket": bucket},
            ).scalar_one()
        )
        if count >= limit:
            return False
        session.execute(
            text(
                "INSERT INTO runtime_rate_events (event_id, bucket, occurred_at) "
                "VALUES (:event_id, :bucket, :occurred_at)"
            ),
            {"event_id": uuid4().hex, "bucket": bucket, "occurred_at": now},
        )
        return True


def clear_budget(bucket: str) -> None:
    sessions = _session_factory()
    with sessions.begin() as session:
        _require_postgres(session)
        _lock(session, "budget:" + bucket)
        session.execute(text("DELETE FROM runtime_rate_events WHERE bucket = :bucket"), {"bucket": bucket})


def read_circuit(scope: str, provider_id: str, now: float) -> StoredCircuitState:
    key = f"{scope}:{provider_id}"
    sessions = _session_factory()
    with sessions.begin() as session:
        _require_postgres(session)
        _lock(session, "circuit:" + key)
        row = session.execute(
            text(
                "SELECT consecutive_failures, opened_until FROM runtime_provider_circuits "
                "WHERE scope = :scope AND provider_id = :provider_id"
            ),
            {"scope": scope, "provider_id": provider_id},
        ).one_or_none()
        if row is None:
            return StoredCircuitState()
        failures, opened_until = int(row[0]), float(row[1] or 0.0)
        if opened_until and opened_until <= now:
            session.execute(
                text("DELETE FROM runtime_provider_circuits WHERE scope = :scope AND provider_id = :provider_id"),
                {"scope": scope, "provider_id": provider_id},
            )
            return StoredCircuitState()
        return StoredCircuitState(failures, opened_until)


def record_success(scope: str, provider_id: str) -> None:
    sessions = _session_factory()
    with sessions.begin() as session:
        _require_postgres(session)
        session.execute(
            text("DELETE FROM runtime_provider_circuits WHERE scope = :scope AND provider_id = :provider_id"),
            {"scope": scope, "provider_id": provider_id},
        )


def record_failure(
    scope: str, provider_id: str, now: float, threshold: int, cooldown: float
) -> StoredCircuitState:
    key = f"{scope}:{provider_id}"
    sessions = _session_factory()
    with sessions.begin() as session:
        _require_postgres(session)
        _lock(session, "circuit:" + key)
        current = session.execute(
            text(
                "SELECT consecutive_failures FROM runtime_provider_circuits "
                "WHERE scope = :scope AND provider_id = :provider_id"
            ),
            {"scope": scope, "provider_id": provider_id},
        ).scalar_one_or_none()
        failures = int(current or 0) + 1
        opened_until = now + cooldown if failures >= threshold else 0.0
        session.execute(
            text(
                "INSERT INTO runtime_provider_circuits "
                "(scope, provider_id, consecutive_failures, opened_until, updated_at) "
                "VALUES (:scope, :provider_id, :failures, :opened_until, :updated_at) "
                "ON CONFLICT (scope, provider_id) DO UPDATE SET "
                "consecutive_failures = EXCLUDED.consecutive_failures, "
                "opened_until = EXCLUDED.opened_until, updated_at = EXCLUDED.updated_at"
            ),
            {
                "scope": scope,
                "provider_id": provider_id,
                "failures": failures,
                "opened_until": opened_until,
                "updated_at": now,
            },
        )
        return StoredCircuitState(failures, opened_until)
