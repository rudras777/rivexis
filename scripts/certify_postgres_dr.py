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
if SRC == DST:
    raise SystemExit('PostgreSQL DR certification: FAIL - restore target must differ from source')
if not SRC.startswith('postgresql') or not DST.startswith('postgresql'):
    raise SystemExit('PostgreSQL DR certification: FAIL - PostgreSQL URLs required')
for tool in ('pg_dump', 'pg_restore', 'psql'):
    if not shutil.which(tool):
        raise SystemExit(f'PostgreSQL DR certification: FAIL - {tool} is required')

with tempfile.TemporaryDirectory(prefix='rivexis-pg-dr-') as tmp:
    dump = Path(tmp) / 'rivexis.dump'
    started = time.perf_counter()
    t0 = time.perf_counter()
    subprocess.run(['pg_dump', '--format=custom', '--no-owner', '--file', str(dump), SRC], check=True)
    dump_seconds = time.perf_counter() - t0
    t0 = time.perf_counter()
    subprocess.run(['pg_restore', '--clean', '--if-exists', '--no-owner', '--dbname', DST, str(dump)], check=True)
    restore_seconds = time.perf_counter() - t0
    verify_sql = "SELECT count(*) FROM information_schema.tables WHERE table_schema=current_schema() AND table_type='BASE TABLE' AND table_name <> 'alembic_version';"
    p = subprocess.run(['psql', DST, '-Atc', verify_sql], check=True, text=True, capture_output=True)
    table_count = int(p.stdout.strip())
    total = time.perf_counter() - started
    if table_count != 55:
        raise SystemExit(f'PostgreSQL DR certification: FAIL - restored table count {table_count}, expected 55')
    if total > MAX_RTO:
        raise SystemExit(f'PostgreSQL DR certification: FAIL - RTO {total:.2f}s exceeds {MAX_RTO:.2f}s')
    digest = hashlib.sha256(dump.read_bytes()).hexdigest()
    print(
        'PostgreSQL DR certification: PASS '
        f'(53 logical + 2 runtime tables; dump={dump_seconds:.2f}s; restore={restore_seconds:.2f}s; '
        f'RTO={total:.2f}s <= {MAX_RTO:.2f}s; sha256={digest})'
    )
