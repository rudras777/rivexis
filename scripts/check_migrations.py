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

print(
    "Alembic/schema parity: PASS "
    "(53/53 blueprint tables + 2 runtime-control tables + auth security state; clean downgrade); "
    "Supabase infrastructure sources: PASS (001-015 present; migrator bootstrap is credential-free)"
)
