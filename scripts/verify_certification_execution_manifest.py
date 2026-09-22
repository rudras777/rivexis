#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))
from rivexis_api.certification_execution import (  # noqa: E402
    DEFAULT_MANIFEST_NAME,
    CertificationExecutionError,
    verify_execution_manifest,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify the sealed Rivexis P37 certification execution manifest.")
    parser.add_argument("manifest", nargs="?", default=str(ROOT / DEFAULT_MANIFEST_NAME))
    args = parser.parse_args()
    path = Path(args.manifest)
    if not path.exists():
        raise SystemExit(f"Certification execution manifest verification: FAIL - missing {path}")
    try:
        manifest = verify_execution_manifest(json.loads(path.read_text()), root=ROOT)
        expected_manifest_path = (ROOT / manifest["manifest_path"]).resolve()
        if path.resolve() != expected_manifest_path:
            raise CertificationExecutionError(
                f"execution manifest must be loaded from canonical path {expected_manifest_path}"
            )
    except (CertificationExecutionError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Certification execution manifest verification: FAIL - {exc}") from exc
    print(
        "Certification execution manifest verification: PASS "
        f"(profiles={len(manifest['required_profiles'])}; gates={len(manifest['required_gates'])}; "
        f"execution_id={manifest['execution_id']}; evidence_sha256={manifest['evidence_sha256']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
