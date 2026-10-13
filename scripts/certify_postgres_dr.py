#!/usr/bin/env python3
"""Destructive PostgreSQL backup/restore drill for an explicitly disposable restore target."""
from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from backup_restore_guard import require_disposable_restore, run_postgres_tool

SRC = os.getenv('RIVEXIS_BACKUP_SOURCE_DATABASE_URL', '').strip()
DST = os.getenv('RIVEXIS_BACKUP_RESTORE_DATABASE_URL', '').strip()
ALLOW = os.getenv('RIVEXIS_BACKUP_RESTORE_ALLOW_APPLY', 'false').lower() in {'1', 'true', 'yes', 'on'}
MAX_RTO = float(os.getenv('RIVEXIS_BACKUP_MAX_RTO_SECONDS', '900'))

if not SRC or not DST:
    print('SKIP PostgreSQL DR certification: source/restore URLs are not configured')
    raise SystemExit(0)
if not ALLOW:
    print('SKIP PostgreSQL DR certification: destructive restore requires RIVEXIS_BACKUP_RESTORE_ALLOW_APPLY=true')
    raise SystemExit(0)
require_disposable_restore(SRC, DST)
for tool in ('pg_dump', 'pg_restore', 'psql'):
    if not shutil.which(tool):
        raise SystemExit(f'PostgreSQL DR certification: FAIL - {tool} is required')

with tempfile.TemporaryDirectory(prefix='rivexis-pg-dr-') as tmp:
    dump = Path(tmp) / 'rivexis.dump'
    started = time.perf_counter()
    verify_sql = "SELECT count(*) FROM information_schema.tables WHERE table_schema=current_schema() AND table_type='BASE TABLE' AND table_name <> 'alembic_version';"
    source_tables = int(run_postgres_tool('psql', ['-Atc', verify_sql], SRC).stdout.strip())
    if source_tables <= 0:
        raise SystemExit('PostgreSQL DR drill: FAIL - source has no application tables')
    t0 = time.perf_counter()
    run_postgres_tool('pg_dump', ['--format=custom', '--no-owner', '--file', str(dump)], SRC)
    dump_seconds = time.perf_counter() - t0
    t0 = time.perf_counter()
    run_postgres_tool('pg_restore', ['--clean', '--if-exists', '--no-owner', str(dump)], DST)
    restore_seconds = time.perf_counter() - t0
    p = run_postgres_tool('psql', ['-Atc', verify_sql], DST)
    table_count = int(p.stdout.strip())
    total = time.perf_counter() - started
    if table_count != source_tables:
        raise SystemExit(f'PostgreSQL DR drill: FAIL - restored table count {table_count}, source {source_tables}')
    if total > MAX_RTO:
        raise SystemExit(f'PostgreSQL DR certification: FAIL - RTO {total:.2f}s exceeds {MAX_RTO:.2f}s')
    digest = hashlib.sha256(dump.read_bytes()).hexdigest()
    print(
        'Local PostgreSQL procedural drill: PASS '
        f'({table_count} source/restored tables; dump={dump_seconds:.2f}s; restore={restore_seconds:.2f}s; '
        f'RTO={total:.2f}s <= {MAX_RTO:.2f}s; sha256={digest})'
    )
