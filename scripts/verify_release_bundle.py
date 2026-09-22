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
    verify_execution_manifest,
)
from rivexis_api.release_certification import verify_release_bundle  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("report", nargs="?", default=str(ROOT / "release-certification-bundle.json"))
    parser.add_argument("--manifest", default=str(ROOT / DEFAULT_MANIFEST_NAME))
    parser.add_argument("--require-complete", action="store_true")
    args = parser.parse_args()
    path = Path(args.report)
    manifest_path = Path(args.manifest)
    if not path.exists():
        raise SystemExit(f"Release bundle verification: FAIL - missing {path}")
    if not manifest_path.exists():
        raise SystemExit(f"Release bundle verification: FAIL - missing execution manifest {manifest_path}")
    try:
        manifest = verify_execution_manifest(json.loads(manifest_path.read_text()), root=ROOT)
        expected_manifest_path = (ROOT / manifest["manifest_path"]).resolve()
        if manifest_path.resolve() != expected_manifest_path:
            raise CertificationExecutionError(
                f"execution manifest must be loaded from canonical path {expected_manifest_path}"
            )
    except (CertificationExecutionError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Release bundle verification: FAIL - {exc}") from exc
    payload = json.loads(path.read_text())
    if not verify_release_bundle(
        payload,
        require_complete=args.require_complete,
        execution_manifest=manifest,
    ):
        raise SystemExit(
            "Release bundle verification: FAIL - invalid seal/execution/profile contract or incomplete required gates"
        )
    expected = str(payload.get("source_tree", {}).get("sha256") or "")
    actual, count = source_tree_fingerprint(ROOT)
    if expected != actual:
        raise SystemExit(
            f"Release bundle verification: FAIL - source tree changed (bundle={expected}, current={actual})"
        )
    completeness = "complete" if payload.get("certified") else "integrity-only"
    execution = payload["execution"]
    print(
        f"Release bundle verification: PASS ({completeness}; "
        f"profiles={len(execution['observed_profiles'])}/{len(execution['required_profiles'])}; "
        f"source files={count}; evidence_sha256={payload['evidence_sha256']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
