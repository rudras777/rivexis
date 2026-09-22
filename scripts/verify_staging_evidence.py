#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))
from rivexis_api.certification import source_tree_fingerprint  # noqa: E402
from rivexis_api.certification_execution import (  # noqa: E402
    DEFAULT_MANIFEST_NAME,
    CertificationExecutionError,
    report_plan_for_profile,
    verify_execution_manifest,
)
from rivexis_api.release_certification import CertificationBundleError, validate_staging_report  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("report", nargs="?")
    parser.add_argument("--manifest", default=str(ROOT / DEFAULT_MANIFEST_NAME))
    parser.add_argument("--profile", default="local")
    args = parser.parse_args()
    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        raise SystemExit(f"Certification evidence verification: FAIL - missing execution manifest {manifest_path}")
    try:
        manifest = verify_execution_manifest(json.loads(manifest_path.read_text()), root=ROOT)
        expected_manifest_path = (ROOT / manifest["manifest_path"]).resolve()
        if manifest_path.resolve() != expected_manifest_path:
            raise CertificationExecutionError(
                f"execution manifest must be loaded from canonical path {expected_manifest_path}"
            )
        planned = report_plan_for_profile(manifest, args.profile)
    except (CertificationExecutionError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Certification evidence verification: FAIL - {exc}") from exc
    report = Path(args.report) if args.report else ROOT / planned["path"]
    if not report.exists():
        raise SystemExit(f"Certification evidence verification: FAIL - missing {report}")
    payload = json.loads(report.read_text())
    try:
        validated = validate_staging_report(payload, execution_manifest=manifest)
    except CertificationBundleError as exc:
        raise SystemExit(f"Certification evidence verification: FAIL - {exc}") from exc
    expected = validated.get("source_tree", {}).get("sha256")
    actual, count = source_tree_fingerprint(ROOT)
    if expected != actual:
        raise SystemExit(
            f"Certification evidence verification: FAIL - source tree changed (report={expected}, current={actual})"
        )
    print(
        "Certification evidence verification: PASS "
        f"(profile={validated['runner']['profile']}; execution_id={validated['execution']['id']}; "
        f"source files={count}; evidence_sha256={validated['evidence_sha256']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
