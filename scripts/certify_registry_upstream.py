#!/usr/bin/env python3
from __future__ import annotations
import os, sys
from pathlib import Path
import httpx
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'apps'/'api'))
from rivexis_api.services.deployment_registry import list_protocol_deployments

def enabled() -> bool:
    return os.getenv('RIVEXIS_CERTIFY_REGISTRY_UPSTREAM','').lower() in {'1','true','yes','on'}

def main() -> int:
    if not enabled():
        print('Registry upstream certification SKIP: set RIVEXIS_CERTIFY_REGISTRY_UPSTREAM=1 in a network-enabled release environment')
        return 0
    token=os.getenv('GITHUB_TOKEN','').strip()
    headers={'Accept':'application/vnd.github+json','User-Agent':'rivexis-registry-certifier'}
    if token: headers['Authorization']=f'Bearer {token}'
    timeout=float(os.getenv('RIVEXIS_REGISTRY_CERT_TIMEOUT_SECONDS','15'))
    checked=0
    with httpx.Client(timeout=timeout,follow_redirects=True,headers=headers) as client:
        for row in list_protocol_deployments():
            att=row.get('source_attestation') or {}
            if att.get('attestation_status')=='PINNED_UPSTREAM_REVISION':
                for item in att.get('upstream_files') or []:
                    url=f"https://api.github.com/repos/{item['repository']}/contents/{item['path']}"
                    resp=client.get(url); resp.raise_for_status(); body=resp.json()
                    actual=str(body.get('sha') or '').lower(); expected=str(item['sha']).lower()
                    if actual!=expected:
                        raise RuntimeError(f"UPSTREAM_CHANGED {row['deployment_id']} {item['path']}: expected {expected}, got {actual}")
                    checked+=1
            else:
                resp=client.get(row['source_ref']); resp.raise_for_status(); text=resp.text.lower()
                missing=[v for v in (row.get('contracts') or {}).values() if isinstance(v,str) and v.lower() not in text]
                if missing:
                    raise RuntimeError(f"UPSTREAM_CONTENT_MISMATCH {row['deployment_id']}: {len(missing)} registered addresses absent from official documentation snapshot")
                checked+=1
    print(f'Registry upstream certification PASS: {checked} official-source checks')
    return 0
if __name__=='__main__': raise SystemExit(main())
