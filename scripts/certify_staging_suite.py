#!/usr/bin/env python3
"""Tamper-evident, execution-manifest-bound staging certification orchestrator for Rivexis P37.

Each report is bound to a sealed P37 execution manifest and to one authorized runner profile.
The manifest fixes the source fingerprint, required production profiles, canonical report paths,
gate assignments, prerequisite names and destructive-gate metadata. No credential values are
stored in either the manifest or staging evidence.
"""
from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))
from rivexis_api.certification import (  # noqa: E402
    safe_env_presence,
    seal_evidence,
    sha256_text,
    source_tree_fingerprint,
)
from rivexis_api.certification_execution import (  # noqa: E402
    DEFAULT_MANIFEST_NAME,
    CertificationExecutionError,
    report_plan_for_profile,
    verify_execution_manifest,
)
from rivexis_api.version import RELEASE_CODENAME  # noqa: E402
from rivexis_api.certification_profiles import (  # noqa: E402
    GATE_SPECS,
    PROFILE_GATES,
    classify_gate_process_result,
    gate_enabled,
    normalize_profile,
)

STRICT = os.getenv("RIVEXIS_REQUIRE_STAGING_CERTIFICATION", "false").lower() in {"1", "true", "yes", "on"}
try:
    PROFILE = normalize_profile(os.getenv("RIVEXIS_CERT_RUNNER_PROFILE", "local"))
except ValueError as exc:
    raise SystemExit(f"Staging certification: FAIL - {exc}") from exc
RUNNER_ID = os.getenv("RIVEXIS_CERT_RUNNER_ID", "").strip()[:160] or None
MANIFEST_PATH = Path(os.getenv("RIVEXIS_CERT_EXECUTION_MANIFEST", str(ROOT / DEFAULT_MANIFEST_NAME)))

if not MANIFEST_PATH.exists():
    raise SystemExit(f"Staging certification: FAIL - missing execution manifest {MANIFEST_PATH}")
try:
    MANIFEST = verify_execution_manifest(json.loads(MANIFEST_PATH.read_text()), root=ROOT)
    expected_manifest_path = (ROOT / MANIFEST["manifest_path"]).resolve()
    if MANIFEST_PATH.resolve() != expected_manifest_path:
        raise CertificationExecutionError(
            f"execution manifest must be loaded from canonical path {expected_manifest_path}"
        )
    PLAN = report_plan_for_profile(MANIFEST, PROFILE)
except (CertificationExecutionError, json.JSONDecodeError) as exc:
    raise SystemExit(f"Staging certification: FAIL - {exc}") from exc

EXPECTED_REPORT = ROOT / PLAN["path"]
REPORT = Path(os.getenv("RIVEXIS_STAGING_CERT_REPORT", str(EXPECTED_REPORT)))
try:
    if REPORT.resolve() != EXPECTED_REPORT.resolve():
        raise SystemExit(
            "Staging certification: FAIL - report path does not match execution manifest "
            f"for profile {PROFILE}: expected {EXPECTED_REPORT}, got {REPORT}"
        )
except FileNotFoundError:
    pass
REPORT.parent.mkdir(parents=True, exist_ok=True)


def version(cmd: list[str]) -> str | None:
    try:
        p = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=5)
        if p.returncode == 0:
            return (p.stdout or p.stderr).strip().splitlines()[0][:200]
    except Exception:
        pass
    return None


results = []
for name, spec in GATE_SPECS.items():
    cmd = list(spec["command"])
    prereq_names = list(spec["prerequisites"])
    prereqs = safe_env_presence(prereq_names)
    if name not in PROFILE_GATES[PROFILE]:
        detail = f"gate not assigned to runner profile {PROFILE}"
        results.append(
            {
                "name": name,
                "status": "SKIP",
                "duration_ms": 0,
                "command": cmd,
                "prerequisites": prereqs,
                "detail": detail,
                "output_sha256": sha256_text(detail),
            }
        )
        continue
    if not gate_enabled(name, dict(os.environ)):
        detail = "runner profile allows gate but staging prerequisite is not configured"
        results.append(
            {
                "name": name,
                "status": "SKIP",
                "duration_ms": 0,
                "command": cmd,
                "prerequisites": prereqs,
                "detail": detail,
                "output_sha256": sha256_text(detail),
            }
        )
        continue
    started = time.perf_counter()
    proc = subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        capture_output=True,
        env={**os.environ, "PYTHONPATH": str(ROOT / "apps" / "api")},
    )
    duration_ms = round((time.perf_counter() - started) * 1000)
    output = (proc.stdout + proc.stderr).strip()
    status = classify_gate_process_result(proc.returncode, output)
    results.append(
        {
            "name": name,
            "status": status,
            "duration_ms": duration_ms,
            "command": cmd,
            "prerequisites": prereqs,
            "detail": output[-4000:],
            "output_sha256": sha256_text(output),
        }
    )

source_sha, source_count = source_tree_fingerprint(ROOT)
payload = {
    "schema_version": 3,
    "release": RELEASE_CODENAME,
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "strict": STRICT,
    "execution": {
        "id": MANIFEST["execution_id"],
        "manifest_evidence_sha256": MANIFEST["evidence_sha256"],
    },
    "runner": {"profile": PROFILE, "id": RUNNER_ID},
    "runtime": {
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "node": version(["node", "--version"]),
        "npm": version(["npm", "--version"]),
        "ruff": version(["ruff", "--version"]) if shutil.which("ruff") else None,
        "pip_audit": version(["pip-audit", "--version"]) if shutil.which("pip-audit") else None,
    },
    "source_tree": {"sha256": source_sha, "file_count": source_count},
    "results": results,
    "counts": {s: sum(1 for r in results if r["status"] == s) for s in ["PASS", "FAIL", "SKIP"]},
}
summary = seal_evidence(payload)
REPORT.write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps(summary, indent=2))
if summary["counts"]["FAIL"] or (STRICT and summary["counts"]["SKIP"]):
    raise SystemExit(1)
