#!/usr/bin/env python3
"""Verify the migrated PostgreSQL schema contract used by CI.

This intentionally keeps SQL out of nested shell quoting so schema failures are
reported as database assertions rather than Bash parser errors.
"""

from __future__ import annotations

import sys

from sqlalchemy import text

from rivexis_api.services.db import engine

EXPECTED_ALEMBIC_HEAD = "0012_postgres_performance_hardening"
EXPECTED_APPLICATION_TABLES = 55


def _scalar(connection, sql: str):
    return connection.execute(text(sql)).scalar_one()


def _assert_equal(label: str, actual, expected) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def main() -> int:
    if engine.dialect.name != "postgresql":
        print(
            "PostgreSQL migrated-schema verification: FAIL - DATABASE_URL is not PostgreSQL",
            file=sys.stderr,
        )
        return 1

    try:
        with engine.connect() as connection:
            _assert_equal(
                "Alembic head",
                _scalar(connection, "SELECT version_num FROM alembic_version"),
                EXPECTED_ALEMBIC_HEAD,
            )
            _assert_equal(
                "application table count",
                _scalar(
                    connection,
                    """
                    SELECT count(*)
                    FROM pg_tables
                    WHERE schemaname = 'public'
                      AND tablename <> 'alembic_version'
                    """,
                ),
                EXPECTED_APPLICATION_TABLES,
            )
            _assert_equal(
                "foreign keys without a valid covering index",
                _scalar(
                    connection,
                    """
                    SELECT count(*)
                    FROM pg_constraint AS c
                    WHERE c.contype = 'f'
                      AND c.connamespace = 'public'::regnamespace
                      AND NOT EXISTS (
                          SELECT 1
                          FROM pg_index AS i
                          WHERE i.indrelid = c.conrelid
                            AND i.indisvalid
                            AND i.indnkeyatts >= cardinality(c.conkey)
                            AND NOT EXISTS (
                                SELECT 1
                                FROM generate_subscripts(c.conkey, 1) AS s
                                WHERE i.indkey[s - 1] <> c.conkey[s]
                            )
                      )
                    """,
                ),
                0,
            )
            _assert_equal(
                "redundant indexes retained",
                _scalar(
                    connection,
                    """
                    SELECT count(*)
                    FROM pg_indexes
                    WHERE schemaname = 'public'
                      AND indexname IN ('ix_users_email', 'ix_workspaces_owner_user_id')
                    """,
                ),
                0,
            )
            _assert_equal(
                "RLS policies retaining per-row NULLIF(current_setting(...)) lookups",
                _scalar(
                    connection,
                    """
                    SELECT count(*)
                    FROM pg_policies
                    WHERE schemaname = 'public'
                      AND tablename IN ('workspaces', 'organizations', 'organization_members', 'profiles')
                      AND (
                          position('NULLIF(current_setting' in coalesce(qual, '')) > 0
                          OR position('NULLIF(current_setting' in coalesce(with_check, '')) > 0
                      )
                    """,
                ),
                0,
            )

        print(
            "PostgreSQL migrated-schema verification: PASS "
            f"(head={EXPECTED_ALEMBIC_HEAD}; tables={EXPECTED_APPLICATION_TABLES}; "
            "FK indexes covered; redundant indexes absent; RLS lookup rewrite present)"
        )
        return 0
    except Exception as exc:  # noqa: BLE001 - certification converts every failure into an explicit gate
        print(f"PostgreSQL migrated-schema verification: FAIL - {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
