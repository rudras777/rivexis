#!/usr/bin/env python3
"""Adversarial PostgreSQL RLS certification for Rivexis.

This is intentionally NOT part of SQLite unit tests. Point it at a migrated PostgreSQL
staging database using two URLs:
  RIVEXIS_RLS_ADMIN_DATABASE_URL  - migration/table owner or fixture-capable role
  RIVEXIS_RLS_APP_DATABASE_URL    - the non-superuser/non-BYPASSRLS role used by the API
  RIVEXIS_RLS_WORKER_DATABASE_URL - dedicated non-superuser BYPASSRLS alert-delivery role

The script refuses to certify application/worker identities with direct or transitive privilege-escalation paths. It creates isolated
fixtures with the admin connection, then proves that the application role can see/write
only the actor's permitted tenant data under FORCE ROW LEVEL SECURITY.
"""
from __future__ import annotations

import os
import sys
from uuid import uuid4

from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError

from rivexis_api.services.postgres_identity import inspect_postgres_role_security_state, validate_standalone_service_role

ADMIN_URL = os.getenv("RIVEXIS_RLS_ADMIN_DATABASE_URL", "")
APP_URL = os.getenv("RIVEXIS_RLS_APP_DATABASE_URL", "")
WORKER_URL = os.getenv("RIVEXIS_RLS_WORKER_DATABASE_URL", "")


def fail(message: str) -> None:
    print(f"RLS certification: FAIL - {message}", file=sys.stderr)
    raise SystemExit(1)


def set_context(conn, user_id: str, *, organization_id: str = "", organization_role: str = "") -> None:
    conn.execute(text("SELECT set_config('rivexis.user_id', :v, true)"), {"v": user_id})
    conn.execute(text("SELECT set_config('rivexis.workspace_id', '', true)"))
    conn.execute(text("SELECT set_config('rivexis.organization_id', :v, true)"), {"v": organization_id})
    conn.execute(text("SELECT set_config('rivexis.organization_role', :v, true)"), {"v": organization_role})


def main() -> None:
    if not ADMIN_URL or not APP_URL or not WORKER_URL:
        fail("set RIVEXIS_RLS_ADMIN_DATABASE_URL, RIVEXIS_RLS_APP_DATABASE_URL and RIVEXIS_RLS_WORKER_DATABASE_URL")
    if not ADMIN_URL.startswith("postgresql") or not APP_URL.startswith("postgresql") or not WORKER_URL.startswith("postgresql"):
        fail("certification requires PostgreSQL URLs")

    admin = create_engine(ADMIN_URL, future=True)
    app = create_engine(APP_URL, future=True)
    worker = create_engine(WORKER_URL, future=True)
    ids = {k: str(uuid4()) for k in ("u1", "u2", "org", "w1", "w2", "ow", "a1", "a2", "oa", "p1", "p2", "alert")}
    suffix = uuid4().hex[:10]

    try:
        with app.connect() as conn:
            try:
                app_state = inspect_postgres_role_security_state(conn)
                validate_standalone_service_role(
                    app_state, label="application runtime", require_bypassrls=False
                )
            except RuntimeError as exc:
                fail(str(exc))

        with worker.connect() as conn:
            try:
                worker_state = inspect_postgres_role_security_state(conn)
                validate_standalone_service_role(
                    worker_state, label="alert worker", require_bypassrls=True
                )
            except RuntimeError as exc:
                fail(str(exc))
            grants = conn.execute(text("""
                SELECT table_name,
                       has_table_privilege(current_user, quote_ident(table_schema)||'.'||quote_ident(table_name), 'SELECT') AS can_select,
                       has_table_privilege(current_user, quote_ident(table_schema)||'.'||quote_ident(table_name), 'INSERT') AS can_insert,
                       has_table_privilege(current_user, quote_ident(table_schema)||'.'||quote_ident(table_name), 'UPDATE') AS can_update,
                       has_table_privilege(current_user, quote_ident(table_schema)||'.'||quote_ident(table_name), 'DELETE') AS can_delete
                FROM information_schema.tables
                WHERE table_schema=current_schema() AND table_type='BASE TABLE'
            """)).mappings().all()
            for grant in grants:
                dml=(bool(grant["can_select"]),bool(grant["can_insert"]),bool(grant["can_update"]),bool(grant["can_delete"]))
                if grant["table_name"] == "alerts":
                    if dml != (True,False,True,False):
                        fail(f"alert-worker alerts privileges are not exactly SELECT+UPDATE: {dml}")
                elif any(dml):
                    fail(f"alert-worker role has unexpected DML on {grant["table_name"]}: {dml}")

        with admin.begin() as conn:
            # Ensure the target policies really exist and are forced.
            required = {"workspaces", "analyses", "provider_requests", "organization_members"}
            rows = conn.execute(text("""
                SELECT c.relname, c.relrowsecurity, c.relforcerowsecurity
                FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
                WHERE n.nspname=current_schema() AND c.relname = ANY(:names)
            """), {"names": list(required)}).all()
            status = {r.relname: (r.relrowsecurity, r.relforcerowsecurity) for r in rows}
            for table in required:
                if status.get(table) != (True, True):
                    fail(f"{table} does not have ENABLE+FORCE RLS")
            policy_tables = set(conn.execute(text("SELECT tablename FROM pg_policies WHERE schemaname=current_schema() AND policyname='rivexis_tenant_isolation'")).scalars())
            missing = required - policy_tables
            if missing:
                fail(f"missing tenant policy on {sorted(missing)}")

            conn.execute(text("INSERT INTO users (id,email,password_hash,role,created_at) VALUES (:id,:e,'x','Individual',now())"), {"id": ids["u1"], "e": f"rls-a-{suffix}@example.invalid"})
            conn.execute(text("INSERT INTO users (id,email,password_hash,role,created_at) VALUES (:id,:e,'x','Individual',now())"), {"id": ids["u2"], "e": f"rls-b-{suffix}@example.invalid"})
            conn.execute(text("INSERT INTO organizations (id,name,created_at) VALUES (:id,:n,now())"), {"id": ids["org"], "n": f"RLS {suffix}"})
            conn.execute(text("INSERT INTO organization_members (organization_id,user_id,role,created_at) VALUES (:o,:u,'OWNER',now())"), {"o": ids["org"], "u": ids["u1"]})
            conn.execute(text("INSERT INTO organization_members (organization_id,user_id,role,created_at) VALUES (:o,:u,'VIEWER',now())"), {"o": ids["org"], "u": ids["u2"]})
            conn.execute(text("INSERT INTO workspaces (id,owner_user_id,name,role,created_at) VALUES (:id,:u,'A','Individual',now())"), {"id": ids["w1"], "u": ids["u1"]})
            conn.execute(text("INSERT INTO workspaces (id,owner_user_id,name,role,created_at) VALUES (:id,:u,'B','Individual',now())"), {"id": ids["w2"], "u": ids["u2"]})
            # Organization workspace deliberately records u2 as creator. P34 requires
            # authorization to follow current organization membership, not this creator field.
            conn.execute(text("INSERT INTO workspaces (id,owner_user_id,organization_id,name,role,created_at) VALUES (:id,:u,:o,'Org','Analyst',now())"), {"id": ids["ow"], "u": ids["u2"], "o": ids["org"]})
            conn.execute(text("INSERT INTO analyses (id,engine_id,payload,demo,owner_user_id,workspace_id,created_at) VALUES (:id,'B1','{}',false,:u,:w,now())"), {"id": ids["a1"], "u": ids["u1"], "w": ids["w1"]})
            conn.execute(text("INSERT INTO analyses (id,engine_id,payload,demo,owner_user_id,workspace_id,created_at) VALUES (:id,'B1','{}',false,:u,:w,now())"), {"id": ids["a2"], "u": ids["u2"], "w": ids["w2"]})
            conn.execute(text("INSERT INTO analyses (id,engine_id,payload,demo,owner_user_id,workspace_id,created_at) VALUES (:id,'B1','{}',false,:u,:w,now())"), {"id": ids["oa"], "u": ids["u2"], "w": ids["ow"]})
            conn.execute(text("INSERT INTO provider_requests (id,workspace_id,provider_key,operation,status,created_at) VALUES (:id,:w,'fixture','read','SUCCESS',now())"), {"id": ids["p1"], "w": ids["w1"]})
            conn.execute(text("INSERT INTO provider_requests (id,workspace_id,provider_key,operation,status,created_at) VALUES (:id,:w,'fixture','read','SUCCESS',now())"), {"id": ids["p2"], "w": ids["w2"]})

            conn.execute(text("INSERT INTO alerts (id,workspace_id,severity,status,payload,created_at,updated_at,delivery_status,delivery_attempts,occurrence_count,first_seen_at,last_seen_at) VALUES (:id,:w,'medium','open','{}',now(),now(),'pending',0,1,now(),now())"), {"id": ids["alert"], "w": ids["w2"]})

        # User 1 must not see user 2's tenant rows.
        with app.begin() as conn:
            set_context(conn, ids["u1"])
            analyses = set(conn.execute(text("SELECT id FROM analyses WHERE id IN (:a1,:a2)"), {"a1": ids["a1"], "a2": ids["a2"]}).scalars())
            if analyses != {ids["a1"]}:
                fail(f"cross-tenant analysis visibility: {analyses}")
            requests = set(conn.execute(text("SELECT id FROM provider_requests WHERE id IN (:p1,:p2)"), {"p1": ids["p1"], "p2": ids["p2"]}).scalars())
            if requests != {ids["p1"]}:
                fail(f"cross-tenant provider telemetry visibility: {requests}")
            own_memberships = set(conn.execute(text("SELECT user_id FROM organization_members WHERE organization_id=:o"), {"o": ids["org"]}).scalars())
            if own_memberships != {ids["u1"]}:
                fail(f"organization membership policy leaked rows without admin context: {own_memberships}")

        # An already-authorized owner/admin context may enumerate its organization.
        with app.begin() as conn:
            set_context(conn, ids["u1"], organization_id=ids["org"], organization_role="OWNER")
            members = set(conn.execute(text("SELECT user_id FROM organization_members WHERE organization_id=:o"), {"o": ids["org"]}).scalars())
            if members != {ids["u1"], ids["u2"]}:
                fail(f"authorized organization-admin context did not expose expected members: {members}")

        # Organization workspace access follows current membership, not creator lineage.
        # u1 is an organization member but did not create the workspace and must still see it.
        with app.begin() as conn:
            set_context(conn, ids["u1"])
            visible = set(conn.execute(text("SELECT id FROM workspaces WHERE id=:w"), {"w": ids["ow"]}).scalars())
            if visible != {ids["ow"]}:
                fail(f"organization member could not see organization workspace: {visible}")

        # u2 created the organization workspace, then loses organization membership.
        # Creator metadata must not preserve workspace/downstream tenant access.
        with admin.begin() as conn:
            conn.execute(text("DELETE FROM organization_members WHERE organization_id=:o AND user_id=:u"), {"o": ids["org"], "u": ids["u2"]})
        with app.begin() as conn:
            set_context(conn, ids["u2"])
            visible_ws = set(conn.execute(text("SELECT id FROM workspaces WHERE id=:w"), {"w": ids["ow"]}).scalars())
            visible_analysis = set(conn.execute(text("SELECT id FROM analyses WHERE id=:a"), {"a": ids["oa"]}).scalars())
            if visible_ws or visible_analysis:
                fail(f"removed organization workspace creator retained tenant access: workspaces={visible_ws} analyses={visible_analysis}")

        # Dedicated worker may enumerate/update delivery state without an end-user actor, but only on alerts.
        with worker.begin() as conn:
            visible = set(conn.execute(text("SELECT id FROM alerts WHERE id=:id"), {"id": ids["alert"]}).scalars())
            if visible != {ids["alert"]}:
                fail(f"alert-worker could not enumerate due cross-tenant alert: {visible}")
            conn.execute(text("UPDATE alerts SET delivery_attempts=delivery_attempts+1 WHERE id=:id"), {"id": ids["alert"]})

        # Cross-workspace write must be rejected by WITH CHECK.
        denied = False
        try:
            with app.begin() as conn:
                set_context(conn, ids["u1"])
                conn.execute(text("INSERT INTO analyses (id,engine_id,payload,demo,owner_user_id,workspace_id,created_at) VALUES (:id,'B1','{}',false,:u,:w,now())"), {"id": str(uuid4()), "u": ids["u1"], "w": ids["w2"]})
        except DBAPIError:
            denied = True
        if not denied:
            fail("cross-workspace INSERT was not rejected by RLS")

        print("RLS certification: PASS (standalone non-bypass app role; standalone least-privilege BYPASSRLS alert worker; no SET ROLE escalation paths; forced policies; cross-tenant isolation; membership-based organization workspace revocation; organization-admin context)")
    finally:
        # Fixture cleanup uses the admin connection and deliberately ignores app RLS.
        try:
            with admin.begin() as conn:
                conn.execute(text("DELETE FROM alerts WHERE id=:id"), {"id": ids["alert"]})
                conn.execute(text("DELETE FROM provider_requests WHERE id IN (:p1,:p2)"), {"p1": ids["p1"], "p2": ids["p2"]})
                conn.execute(text("DELETE FROM analyses WHERE id IN (:a1,:a2,:oa)"), {"a1": ids["a1"], "a2": ids["a2"], "oa": ids["oa"]})
                conn.execute(text("DELETE FROM workspaces WHERE id IN (:w1,:w2,:ow)"), {"w1": ids["w1"], "w2": ids["w2"], "ow": ids["ow"]})
                conn.execute(text("DELETE FROM organization_members WHERE organization_id=:o"), {"o": ids["org"]})
                conn.execute(text("DELETE FROM organizations WHERE id=:o"), {"o": ids["org"]})
                conn.execute(text("DELETE FROM users WHERE id IN (:u1,:u2)"), {"u1": ids["u1"], "u2": ids["u2"]})
        except Exception as exc:
            print(f"RLS certification cleanup warning: {exc}", file=sys.stderr)
        admin.dispose(); app.dispose(); worker.dispose()


if __name__ == "__main__":
    main()
