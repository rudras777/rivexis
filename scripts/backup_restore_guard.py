"""Fail closed before either legacy PostgreSQL drill can clean a target."""
from __future__ import annotations

import os
import re
import subprocess
from urllib.parse import parse_qsl, unquote, urlsplit


def require_disposable_restore(source: str, target: str) -> None:
    def identity(value: str):
        try:
            uri = urlsplit(value)
            if uri.scheme not in {'postgres', 'postgresql'} or uri.fragment:
                raise ValueError
            host = (uri.hostname or '').lower()
            port = uri.port or 5432
            database = unquote(uri.path.removeprefix('/'))
            if not host or not re.fullmatch(r'[A-Za-z0-9_.-]+', database):
                raise ValueError
            # Connection-routing overrides can invalidate a hostname safety check.
            options = parse_qsl(uri.query, keep_blank_values=True)
            if any(key != 'sslmode' for key, _ in options):
                raise ValueError
            if len(options) > 1 or any(mode not in {
                'disable', 'allow', 'prefer', 'require', 'verify-ca', 'verify-full'
            } for _, mode in options):
                raise ValueError
            return host, port, database
        except ValueError:
            raise SystemExit('Restore denied: explicit PostgreSQL URL with no routing overrides required') from None

    src = identity(source)
    dst = identity(target)
    local = {'localhost', '127.0.0.1', '::1'}
    canonical_src = ('loopback' if src[0] in local else src[0], src[1], src[2])
    canonical_dst = ('loopback' if dst[0] in local else dst[0], dst[1], dst[2])
    if canonical_src == canonical_dst:
        raise SystemExit('Restore denied: source and target identify the same database')
    if dst[0] not in local or not dst[2].startswith('rivexis_restore_'):
        raise SystemExit('Restore denied: target must be a local disposable rivexis_restore_* database')
    if any(os.environ.get(key) for key in ('PGHOSTADDR', 'PGSERVICE', 'PGSERVICEFILE', 'PGOPTIONS')):
        raise SystemExit('Restore denied: inherited PostgreSQL routing overrides must be removed')


def run_postgres_tool(tool: str, arguments: list[str], connection: str):
    """Keep connection credentials out of argv and redact tool failures.

    Call only after require_disposable_restore validates both connections.
    Credentials still exist in the child environment; this is not a secret vault.
    """
    uri = urlsplit(connection)
    env = os.environ.copy()
    for key in ('PGHOST', 'PGPORT', 'PGDATABASE', 'PGUSER', 'PGPASSWORD',
                'RIVEXIS_BACKUP_SOURCE_DATABASE_URL', 'RIVEXIS_BACKUP_RESTORE_DATABASE_URL'):
        env.pop(key, None)
    env.update(PGHOST=uri.hostname or '', PGPORT=str(uri.port or 5432),
               PGDATABASE=unquote(uri.path.removeprefix('/')))
    if uri.username is not None:
        env['PGUSER'] = unquote(uri.username)
    if uri.password is not None:
        env['PGPASSWORD'] = unquote(uri.password)
    for key, value in parse_qsl(uri.query):
        if key == 'sslmode':
            env['PGSSLMODE'] = value
    command = [tool, '--no-password', *arguments]
    if tool == 'pg_restore':
        # pg_restore otherwise prints SQL rather than connecting to a database.
        command.extend(['--dbname', env['PGDATABASE']])
    try:
        return subprocess.run(command, env=env, check=True, text=True, capture_output=True, timeout=900)
    except (subprocess.SubprocessError, OSError, ValueError):
        raise SystemExit(f'PostgreSQL drill failed: {tool}; connection details and output withheld') from None
