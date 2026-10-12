"""Fail closed before either legacy PostgreSQL drill can clean a target."""
from __future__ import annotations

import os
import re
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
