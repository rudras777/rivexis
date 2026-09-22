from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

TRANSIENT_PARTS = {
    '.git', '.pytest_cache', '__pycache__', 'node_modules', '.next', 'test-results', 'playwright-report', 'certification-reports'
}
TRANSIENT_SUFFIXES = {'.pyc', '.pyo', '.db', '.sqlite', '.sqlite3'}
TRANSIENT_NAMES = {'REPOSITORY_MANIFEST.txt', 'staging-certification.json', 'release-certification-bundle.json', 'certification-execution-manifest.json'}
RUNNER_GENERATED_ROOT_FILES = {'package-lock.json'}


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode('utf-8'))


def source_tree_fingerprint(root: Path) -> tuple[str, int]:
    """Return a deterministic source-tree fingerprint without generated/transient artifacts."""
    rows: list[str] = []
    count = 0
    for path in sorted(p for p in root.rglob('*') if p.is_file()):
        rel = path.relative_to(root)
        if any(part in TRANSIENT_PARTS for part in rel.parts):
            continue
        if path.name in TRANSIENT_NAMES or path.suffix.lower() in TRANSIENT_SUFFIXES:
            continue
        if rel.as_posix() in RUNNER_GENERATED_ROOT_FILES:
            continue
        rows.append(f"{rel.as_posix()}\0{sha256_bytes(path.read_bytes())}")
        count += 1
    return sha256_text('\n'.join(rows) + '\n'), count


def seal_evidence(payload: dict[str, Any]) -> dict[str, Any]:
    body = dict(payload)
    body.pop('evidence_sha256', None)
    sealed = dict(body)
    sealed['evidence_sha256'] = sha256_text(canonical_json(body))
    return sealed


def verify_evidence(payload: dict[str, Any]) -> bool:
    expected = str(payload.get('evidence_sha256') or '')
    if not expected:
        return False
    body = dict(payload)
    body.pop('evidence_sha256', None)
    return expected == sha256_text(canonical_json(body))


def safe_env_presence(names: list[str]) -> dict[str, bool]:
    """Expose only whether a certification prerequisite exists, never its value."""
    return {name: bool(os.getenv(name, '').strip()) for name in names}
