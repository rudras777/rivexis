#!/usr/bin/env python3
"""Run dependency-resolved quality/security gates when their prerequisites exist.

This script never turns a missing tool or lockfile into a false PASS. Set
RIVEXIS_REQUIRE_DEPENDENCY_CERTIFICATION=true to make every missing prerequisite fatal.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
STRICT=os.getenv('RIVEXIS_REQUIRE_DEPENDENCY_CERTIFICATION','false').lower() in {'1','true','yes','on'}
results=[]

def run(name,cmd,cwd=ROOT,prereq=True,skip_reason='prerequisite unavailable'):
    if not prereq:
        results.append({'name':name,'status':'SKIP','detail':skip_reason});return
    proc=subprocess.run(cmd,cwd=cwd,text=True,capture_output=True)
    detail=(proc.stdout+proc.stderr).strip()[-2000:]
    results.append({'name':name,'status':'PASS' if proc.returncode==0 else 'FAIL','detail':detail})

ruff=shutil.which('ruff')
pip_audit=shutil.which('pip-audit')
run('ruff',[ruff,'check','rivexis_api','tests'] if ruff else [],cwd=ROOT/'apps'/'api',prereq=bool(ruff),skip_reason='ruff is not installed')
run('pip-audit',[pip_audit] if pip_audit else [],cwd=ROOT/'apps'/'api',prereq=bool(pip_audit),skip_reason='pip-audit is not installed')
lock_path=ROOT/'package-lock.json'
lock=lock_path.exists()
lock_sha256=hashlib.sha256(lock_path.read_bytes()).hexdigest() if lock else None
lockfile_version=None
lock_manifest_consistent=False
lock_valid=False
if lock:
    try:
        lock_payload=json.loads(lock_path.read_text())
        lockfile_version=int(lock_payload.get('lockfileVersion') or 0)
        source_root=json.loads((ROOT/'package.json').read_text())
        source_web=json.loads((ROOT/'apps'/'web'/'package.json').read_text())
        packages=lock_payload.get('packages') if isinstance(lock_payload.get('packages'),dict) else {}
        lock_root=packages.get('') if isinstance(packages.get(''),dict) else {}
        lock_web=packages.get('apps/web') if isinstance(packages.get('apps/web'),dict) else {}
        lock_manifest_consistent=(
            str(lock_payload.get('name') or '') == str(source_root.get('name') or '') == 'rivexis'
            and lock_root.get('workspaces') == source_root.get('workspaces')
            and str(lock_web.get('name') or '') == str(source_web.get('name') or '')
            and str(lock_web.get('version') or '') == str(source_web.get('version') or '')
            and lock_web.get('dependencies') == source_web.get('dependencies')
            and lock_web.get('devDependencies') == source_web.get('devDependencies')
        )
        lock_valid=lockfile_version >= 2 and lock_manifest_consistent
        if not lock_valid:
            results.append({'name':'npm-lockfile','status':'FAIL','detail':'package-lock.json must use lockfileVersion >= 2 and match the exact root/workspace package manifests'})
    except Exception as exc:
        results.append({'name':'npm-lockfile','status':'FAIL','detail':f'invalid package-lock.json: {exc.__class__.__name__}'})
node_modules=(ROOT/'node_modules').is_dir()
frontend_ready=lock and lock_valid and node_modules
run('npm-typecheck',['npm','run','typecheck:web'],prereq=frontend_ready,skip_reason='valid package-lock.json and/or node_modules absent')
run('next-build',['npm','run','build:web'],prereq=frontend_ready,skip_reason='valid package-lock.json and/or node_modules absent')
run('npm-audit',['npm','audit','--audit-level=high'],prereq=frontend_ready,skip_reason='valid package-lock.json and/or node_modules absent')
playwright_bin=(ROOT/'node_modules'/'.bin'/'playwright')
playwright_ready=frontend_ready and playwright_bin.exists()
run('playwright-e2e',['npm','run','test:e2e'],prereq=playwright_ready,skip_reason='Playwright dependencies/browser runtime unavailable')

failed=[r for r in results if r['status']=='FAIL']
skipped=[r for r in results if r['status']=='SKIP']
overall='FAIL' if failed else ('SKIP' if skipped else 'PASS')
print(f"{overall} dependency certification: {len(results)-len(skipped)-len(failed)} passed, {len(skipped)} skipped, {len(failed)} failed")
print(json.dumps({
    'strict':STRICT,
    'overall':overall,
    'lockfile_sha256':lock_sha256,
    'lockfile_version':lockfile_version,
    'lock_manifest_consistent':lock_manifest_consistent,
    'node_modules_present':node_modules,
    'results':results,
},indent=2))
if failed or (STRICT and skipped):
    raise SystemExit(1)
