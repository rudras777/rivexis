"""Actual PostgreSQL failure tests, restricted to explicitly disposable CI fixtures."""
import os
import tempfile
from pathlib import Path
from urllib.parse import urlsplit
from unittest.mock import patch

from backup_restore_guard import require_disposable_restore, run_postgres_tool

source = os.environ['RIVEXIS_BACKUP_SOURCE_DATABASE_URL']
target = os.environ['RIVEXIS_BACKUP_RESTORE_DATABASE_URL']
require_disposable_restore(source, target)
if (os.environ.get('RIVEXIS_BACKUP_RESTORE_ALLOW_APPLY') != 'true'
        or urlsplit(source).hostname not in {'localhost', '127.0.0.1', '::1'}
        or urlsplit(source).path != '/rivexis_ci'):
    raise SystemExit('Atomicity verification denied: explicit local rivexis_ci source required')

schema = 'rivexis_dr_atomic_fixture'
def sql(connection, statement):
    return run_postgres_tool('psql', ['-Atc', statement], connection).stdout.strip()

def must_fail(action):
    try:
        action()
    except SystemExit:
        return
    raise AssertionError('Expected PostgreSQL failure was not propagated')

try:
    for connection, values in ((source, (11, 22)), (target, (101, 202))):
        sql(connection, f'CREATE SCHEMA {schema}; CREATE TABLE {schema}.a_conflict(id int); '
            f'CREATE TABLE {schema}.z_rollback(id int); '
            f'INSERT INTO {schema}.a_conflict VALUES ({values[0]}); '
            f'INSERT INTO {schema}.z_rollback VALUES ({values[1]});')
    # This extra target dependency prevents cleanup of a_conflict after the
    # reverse-order cleanup of z_rollback. Atomic restore must retain both.
    sql(target, f'CREATE VIEW {schema}.target_dependency AS SELECT * FROM {schema}.a_conflict')
    with tempfile.TemporaryDirectory(prefix='rivexis-atomic-dr-') as directory:
        archive = Path(directory) / 'fixture.dump'
        run_postgres_tool('pg_dump', ['--format=custom', '--no-owner', '--schema', schema,
                                     '--file', str(archive)], source)
        must_fail(lambda: run_postgres_tool('pg_restore',
            ['--clean', '--if-exists', '--no-owner', str(archive)], target))
        assert sql(target, f'SELECT id FROM {schema}.a_conflict') == '101'
        assert sql(target, f'SELECT id FROM {schema}.z_rollback') == '202'
        assert sql(target, f'SELECT id FROM {schema}.target_dependency') == '101'
        must_fail(lambda: sql(target, 'SELECT 1/0; SELECT 17'))
        startup = Path(directory) / 'psqlrc'
        startup.write_text('\\echo UNEXPECTED_STARTUP\n\\quit 23\n', encoding='utf-8')
        with patch.dict(os.environ, {'PSQLRC': str(startup)}):
            assert sql(target, 'SELECT 17') == '17'
    print('Actual PostgreSQL recovery failure checks: PASS '
          '(rollback preserves both rows and dependency; SQL errors stop; startup file ignored)')
finally:
    # Only the named fixture schema in the two validated local CI databases.
    for connection in (source, target):
        sql(connection, f'DROP SCHEMA IF EXISTS {schema} CASCADE')
