#!/usr/bin/env python3
"""Restrict the dedicated alert-worker PostgreSQL role to the minimum required DML.

The migration/admin connection runs this after Alembic. The worker role is intentionally
BYPASSRLS because it must discover due alerts across all workspaces, but it receives DML
rights only on the alerts table. API/runtime credentials never receive BYPASSRLS.
"""
from __future__ import annotations

import os
import re
import sys
from sqlalchemy import create_engine, text

URL = os.getenv("RIVEXIS_MIGRATION_DATABASE_URL", "").strip()
ROLE = os.getenv("RIVEXIS_ALERT_WORKER_ROLE", "").strip()
ROLE_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def fail(message: str) -> None:
    print(f"Alert-worker role configuration: FAIL - {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    if not ROLE:
        print("Alert-worker role configuration: SKIP - RIVEXIS_ALERT_WORKER_ROLE is not set")
        return
    if not URL or not URL.startswith("postgresql"):
        fail("RIVEXIS_MIGRATION_DATABASE_URL must be a PostgreSQL URL")
    if not ROLE_RE.fullmatch(ROLE):
        fail("RIVEXIS_ALERT_WORKER_ROLE must be a simple PostgreSQL role identifier")

    engine = create_engine(URL, future=True)
    try:
        with engine.begin() as conn:
            row = conn.execute(
                text("""
                    SELECT rolname, rolsuper, rolbypassrls, rolcreatedb, rolcreaterole,
                           rolreplication, rolinherit, rolcanlogin
                    FROM pg_roles WHERE rolname=:role
                """),
                {"role": ROLE},
            ).mappings().first()
            if not row:
                fail(f"role {ROLE!r} does not exist")
            if bool(row["rolsuper"]):
                fail("alert-worker role must not be SUPERUSER")
            if not bool(row["rolbypassrls"]):
                fail("alert-worker role must have BYPASSRLS because it performs cross-workspace queue delivery")
            if bool(row["rolcreatedb"]) or bool(row["rolcreaterole"]) or bool(row["rolreplication"]):
                fail("alert-worker role must not have CREATEDB, CREATEROLE or REPLICATION authority")
            if bool(row["rolinherit"]):
                fail("alert-worker role must be NOINHERIT")
            if not bool(row["rolcanlogin"]):
                fail("alert-worker role must be LOGIN")
            memberships = list(conn.execute(text("""
                SELECT r.rolname
                FROM pg_roles r
                WHERE r.rolname <> :role
                  AND pg_has_role(:role, r.oid, 'MEMBER')
                ORDER BY r.rolname
            """), {"role": ROLE}).scalars())
            if memberships:
                fail(f"alert-worker role must not have parent-role membership / SET ROLE paths: {memberships}")
            if bool(conn.execute(
                text("SELECT has_database_privilege(:role, current_database(), 'CREATE')"),
                {"role": ROLE},
            ).scalar()):
                fail("alert-worker role must not have database CREATE privilege")
            if bool(conn.execute(
                text("SELECT has_schema_privilege(:role, current_schema(), 'CREATE')"),
                {"role": ROLE},
            ).scalar()):
                fail("alert-worker role must not have schema CREATE privilege")
            owned = list(conn.execute(text("""
                SELECT c.relname
                FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
                WHERE n.nspname=current_schema()
                  AND c.relkind IN ('r','p','v','m','S','f')
                  AND c.relowner=(SELECT oid FROM pg_roles WHERE rolname=:role)
                ORDER BY c.relname
            """), {"role": ROLE}).scalars())
            if owned:
                fail(f"alert-worker role must not own application relations: {owned}")

            quoted = '"' + ROLE.replace('"', '""') + '"'
            conn.exec_driver_sql(f"REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM {quoted}")
            conn.exec_driver_sql(f"REVOKE ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public FROM {quoted}")
            conn.exec_driver_sql(f"GRANT SELECT, UPDATE ON TABLE alerts TO {quoted}")
        print(f"Alert-worker role configuration: PASS - {ROLE} has SELECT/UPDATE on alerts only")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
