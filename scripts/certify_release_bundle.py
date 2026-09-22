#!/usr/bin/env python3
"""Aggregate Rivexis P37 execution-manifest-bound staging evidence."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))
from rivexis_api.certification_execution import (  # noqa: E402
    DEFAULT_MANIFEST_NAME,
    CertificationExecutionError,
    verify_execution_manifest,
)
from rivexis_api.release_certification import CertificationBundleError, aggregate_staging_reports  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", action="append", default=[], help="sealed P37 staging report; repeatable")
    parser.add_argument("--manifest", default=str(ROOT / DEFAULT_MANIFEST_NAME))
    parser.add_argument(
        "--output",
        default=os.getenv("RIVEXIS_RELEASE_CERT_BUNDLE", str(ROOT / "release-certification-bundle.json")),
    )
    return parser.parse_args()


def env_reports() -> list[str]:
    raw = os.getenv("RIVEXIS_CERT_INPUT_REPORTS", "").strip()
    return [item.strip() for item in raw.split(";") if item.strip()] if raw else []


def main() -> int:
    args = parse_args()
    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        raise SystemExit(f"Release certification bundle: FAIL - missing execution manifest {manifest_path}")
    try:
        manifest = verify_execution_manifest(json.loads(manifest_path.read_text()), root=ROOT)
        expected_manifest_path = (ROOT / manifest["manifest_path"]).resolve()
        if manifest_path.resolve() != expected_manifest_path:
            raise CertificationExecutionError(
                f"execution manifest must be loaded from canonical path {expected_manifest_path}"
            )
    except (CertificationExecutionError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Release certification bundle: FAIL - {exc}") from exc

    paths = [Path(value) for value in [*args.report, *env_reports()]]
    if not paths:
        raise SystemExit("Release certification bundle: FAIL - provide --report or RIVEXIS_CERT_INPUT_REPORTS")
    reports = []
    for path in paths:
        if not path.exists():
            raise SystemExit(f"Release certification bundle: FAIL - missing input report {path}")
        reports.append(json.loads(path.read_text()))
    try:
        bundle = aggregate_staging_reports(reports, execution_manifest=manifest)
    except (CertificationBundleError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Release certification bundle: FAIL - {exc}") from exc
    output = Path(args.output)
    output.write_text(json.dumps(bundle, indent=2) + "\n")
    status = "PASS" if bundle["certified"] else "INCOMPLETE"
    execution = bundle["execution"]
    print(
        f"Release certification bundle: {status} "
        f"({bundle['counts']['PASS']} PASS, {bundle['counts']['FAIL']} FAIL, {bundle['counts']['SKIP']} SKIP; "
        f"profiles={len(execution['observed_profiles'])}/{len(execution['required_profiles'])}; "
        f"evidence_sha256={bundle['evidence_sha256']})"
    )
    return 0 if bundle["counts"]["FAIL"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
