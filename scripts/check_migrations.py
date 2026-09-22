from __future__ import annotations

import os
import re
import sqlite3
import subprocess
import tempfile
from contextlib import closing
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API = ROOT / "apps" / "api"
SCHEMA = ROOT / "infrastructure" / "db" / "schema.sql"
expected = set(re.findall(r"^CREATE TABLE\s+([a-zA-Z0-9_]+)", SCHEMA.read_text(), re.M))
assert len(expected) == 53, f"Expected 53 blueprint tables, found {len(expected)}"

with tempfile.TemporaryDirectory(prefix="rivexis-migration-") as tmp:
    db_path = Path(tmp) / "migration.db"
    env = os.environ.copy()
    env["DATABASE_URL"] = f"sqlite:///{db_path}"
    env["PYTHONPATH"] = str(API)
    subprocess.run(["alembic", "upgrade", "head"], cwd=API, env=env, check=True, capture_output=True, text=True)
    with closing(sqlite3.connect(db_path)) as con:
        actual = {
            row[0]
            for row in con.execute(
                "select name from sqlite_master where type='table' and name not like 'sqlite_%' and name!='alembic_version'"
            )
        }
    assert actual == expected, f"Migration/schema mismatch missing={sorted(expected-actual)} extra={sorted(actual-expected)}"
    subprocess.run(["alembic", "downgrade", "base"], cwd=API, env=env, check=True, capture_output=True, text=True)
    with closing(sqlite3.connect(db_path)) as con:
        remaining = {
            row[0]
            for row in con.execute(
                "select name from sqlite_master where type='table' and name not like 'sqlite_%' and name!='alembic_version'"
            )
        }
    assert not remaining, f"Downgrade left tables: {sorted(remaining)}"

print("Alembic/schema parity: PASS (53/53 blueprint tables; clean downgrade)")
