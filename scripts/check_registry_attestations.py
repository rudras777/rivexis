#!/usr/bin/env python3
from __future__ import annotations
import re, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'apps'/'api'))
from rivexis_api.services.deployment_registry import list_protocol_deployments
HEX40=re.compile(r'^[0-9a-f]{40}$')
rows=list_protocol_deployments()
errors=[]
for row in rows:
    att=row.get('source_attestation') or {}
    status=att.get('attestation_status')
    if status=='PINNED_UPSTREAM_REVISION':
        files=att.get('upstream_files') or []
        if not files: errors.append(f"{row['deployment_id']}: pinned attestation has no upstream_files")
        for item in files:
            sha=str(item.get('sha') or '').lower()
            if not HEX40.fullmatch(sha): errors.append(f"{row['deployment_id']}: invalid GitHub blob sha {sha!r}")
            if '/' not in str(item.get('repository') or ''): errors.append(f"{row['deployment_id']}: invalid repository locator")
            if not str(item.get('path') or ''): errors.append(f"{row['deployment_id']}: missing upstream path")
    elif status=='REVIEWED_CONTENT_SNAPSHOT':
        if not row.get('source_ref'): errors.append(f"{row['deployment_id']}: reviewed snapshot missing source_ref")
    else:
        errors.append(f"{row['deployment_id']}: unknown attestation status {status!r}")
if errors:
    print('\n'.join(errors),file=sys.stderr); raise SystemExit(1)
print(f"Registry attestation contract PASS: {len(rows)} deployment records; {sum((r.get('source_attestation') or {}).get('attestation_status')=='PINNED_UPSTREAM_REVISION' for r in rows)} pinned upstream revisions")
