from __future__ import annotations

import os
import re
import sqlite3
import subprocess
import sys
import tempfile
from contextlib import closing
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = ROOT / "apps" / "api"
SCHEMA = ROOT / "infrastructure" / "db" / "schema.sql"
SUPABASE_INFRA = ROOT / "infrastructure" / "supabase"
expected = set(re.findall(r"^CREATE TABLE\s+([a-zA-Z0-9_]+)", SCHEMA.read_text(), re.MULTILINE))
assert len(expected) == 53, f"Expected 53 blueprint tables, found {len(expected)}"
runtime_tables = {"runtime_rate_events", "runtime_provider_circuits"}
security_tables = {"user_auth_state"}

with tempfile.TemporaryDirectory(prefix="rivexis-migration-") as tmp:
    db_path = Path(tmp) / "migration.db"
    env = os.environ.copy()
    env["DATABASE_URL"] = f"sqlite:///{db_path}"
    env["PYTHONPATH"] = str(API)
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=API,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    with closing(sqlite3.connect(db_path)) as con:
        actual = {
            row[0]
            for row in con.execute(
                "select name from sqlite_master where type='table' and name not like 'sqlite_%' and name!='alembic_version'"
            )
        }
    physical_expected = expected | runtime_tables | security_tables
    assert actual == physical_expected, (
        f"Migration/schema mismatch missing={sorted(physical_expected-actual)} "
        f"extra={sorted(actual-physical_expected)}"
    )
    subprocess.run(
        [sys.executable, "-m", "alembic", "downgrade", "base"],
        cwd=API,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    with closing(sqlite3.connect(db_path)) as con:
        remaining = {
            row[0]
            for row in con.execute(
                "select name from sqlite_master where type='table' and name not like 'sqlite_%' and name!='alembic_version'"
            )
        }
    assert not remaining, f"Downgrade left tables: {sorted(remaining)}"

required_supabase_sources = {
    "001_lock_down_public_defaults.sql",
    "002_remove_residual_public_grants.sql",
    "003_create_app_role.sql",
    "004_grant_operational_tables.sql",
    "005_create_migrator_role.sql",
    "006_create_edge_runtime_bridge.sql",
    "007_saved_analysis_actions.sql",
    "008_organization_membership_actions.sql",
    "009_fix_membership_claim_visibility.sql",
    "010_edge_decision_reports.sql",
    "011_edge_alert_lifecycle.sql",
    "012_edge_monitor_alert_creation.sql",
    "013_edge_alert_delivery_scheduler.sql",
    "014_alert_dispatcher_extensions_usage.sql",
    "015_alert_dispatcher_object_grants.sql",
    "016_restrict_alert_requeue.sql",
    "017_alert_dispatch_org_owner_recipient.sql",
    "018_edge_org_workspace_create.sql",
    "019_fix_org_workspace_membership_rls_context.sql",
    "020_alert_dispatch_org_workspace_grants.sql",
    "021_lock_org_workspace_rpc_execution.sql",
    "022_explicit_deny_alert_delivery_runtime_rls.sql",
    "023_remove_unused_app_delete_privileges.sql",
}
actual_supabase_sources = {path.name for path in SUPABASE_INFRA.glob("*.sql")}
missing_supabase_sources = required_supabase_sources - actual_supabase_sources
assert not missing_supabase_sources, (
    "Supabase infrastructure source set is incomplete: "
    f"missing={sorted(missing_supabase_sources)}"
)

for path in SUPABASE_INFRA.glob("*.sql"):
    text = path.read_text()
    assert not re.search(r"(?i)\bpassword\s+'", text), (
        f"Unsafe literal role password found in {path.relative_to(ROOT)}"
    )
    assert "SCRAM-SHA-256$" not in text, (
        f"SCRAM credential material found in {path.relative_to(ROOT)}"
    )

migrator_bootstrap = (SUPABASE_INFRA / "005_create_migrator_role.sql").read_text().lower()
assert "create role rivexis_migrator" in migrator_bootstrap
assert "nologin" in migrator_bootstrap
assert "nobypassrls" in migrator_bootstrap

requeue_hardening = (SUPABASE_INFRA / "016_restrict_alert_requeue.sql").read_text().lower()
assert "delivery_status in ('retry','dead_letter')" in requeue_hardening
assert "only failed alert deliveries can be requeued" in requeue_hardening
assert "delivery_status='pending'" in requeue_hardening

org_alert_recipient = (SUPABASE_INFRA / "017_alert_dispatch_org_owner_recipient.sql").read_text().lower()
assert "from public.organization_members om" in org_alert_recipient
assert "om.role='owner'" in org_alert_recipient
assert "order by om.created_at,om.user_id" in org_alert_recipient
assert "coalesce(w.owner_user_id,org_owner.user_id)" in org_alert_recipient
assert "grant create on schema public to rivexis_alert_dispatcher" in org_alert_recipient
assert "revoke create on schema public from rivexis_alert_dispatcher" in org_alert_recipient

org_workspace = (SUPABASE_INFRA / "019_fix_org_workspace_membership_rls_context.sql").read_text().lower()
assert "rivexis_edge_create_organization_workspace" in org_workspace
assert "v_member_role not in ('owner','admin','analyst')" in org_workspace
assert "'access_role',v_member_role" in org_workspace
assert "grant execute on function public.rivexis_edge_create_organization_workspace(text,jsonb) to service_role" in org_workspace
assert "revoke all on function public.rivexis_edge_create_organization_workspace(text,jsonb) from authenticated" in org_workspace
user_context_index = org_workspace.index("perform set_config('rivexis.user_id',p_actor_user_id,true)")
membership_lookup_index = org_workspace.index("select om.role into v_member_role")
assert user_context_index < membership_lookup_index, (
    "Organization workspace membership lookup must run after the actor RLS context is established"
)

dispatch_org_grants = (SUPABASE_INFRA / "020_alert_dispatch_org_workspace_grants.sql").read_text().lower()
assert "set local role rivexis_migrator" in dispatch_org_grants
assert "grant select(organization_id)" in dispatch_org_grants
assert "on table public.workspaces" in dispatch_org_grants
assert "grant select(organization_id,user_id,role,created_at)" in dispatch_org_grants
assert "on table public.organization_members" in dispatch_org_grants
assert "to rivexis_alert_dispatcher" in dispatch_org_grants

org_workspace_rpc_lock = (SUPABASE_INFRA / "021_lock_org_workspace_rpc_execution.sql").read_text().lower()
assert "set local role rivexis_migrator" in org_workspace_rpc_lock
assert "revoke all on function public.rivexis_edge_create_organization_workspace(text,jsonb) from public" in org_workspace_rpc_lock
assert "revoke all on function public.rivexis_edge_create_organization_workspace(text,jsonb) from anon" in org_workspace_rpc_lock
assert "revoke all on function public.rivexis_edge_create_organization_workspace(text,jsonb) from authenticated" in org_workspace_rpc_lock
assert "grant execute on function public.rivexis_edge_create_organization_workspace(text,jsonb) to service_role" in org_workspace_rpc_lock

alert_runtime_deny = (SUPABASE_INFRA / "022_explicit_deny_alert_delivery_runtime_rls.sql").read_text().lower()
assert "alert_delivery_runtime_deny_public" in alert_runtime_deny
assert "on public.alert_delivery_runtime" in alert_runtime_deny
assert "to public" in alert_runtime_deny
assert "using (false)" in alert_runtime_deny
assert "with check (false)" in alert_runtime_deny

app_delete_reduction = (SUPABASE_INFRA / "023_remove_unused_app_delete_privileges.sql").read_text().lower()
assert "set local role rivexis_migrator" in app_delete_reduction
assert "revoke delete on table public.users from rivexis_app" in app_delete_reduction
assert "revoke delete on table public.data_sources from rivexis_app" in app_delete_reduction

print(
    "Alembic/schema parity: PASS "
    "(53/53 blueprint tables + 2 runtime-control tables + auth security state; clean downgrade); "
    "Supabase infrastructure sources: PASS (001-023 present; credential-free bootstrap; "
    "delivered alerts cannot be manually requeued; organization alerts resolve to an OWNER recipient; "
    "organization workspace creation is membership-bound and service-role-only; "
    "organization-aware dispatcher lookup grants are least-privilege and owner-applied; "
    "organization workspace SECURITY DEFINER execution is locked to service_role; "
    "alert delivery runtime has an explicit deny-all ordinary-role RLS policy; "
    "unused destructive app privileges are revoked from global identity/provider metadata tables)"
)
