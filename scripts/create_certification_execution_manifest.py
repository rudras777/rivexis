#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))
from rivexis_api.certification_execution import (  # noqa: E402
    DEFAULT_MANIFEST_NAME,
    build_execution_manifest,
)


def main() -> int:
    payload = build_execution_manifest(ROOT)
    output = ROOT / DEFAULT_MANIFEST_NAME
    output.write_text(json.dumps(payload, indent=2) + "\n")
    print(
        f"Certification execution manifest: PASS (execution_id={payload['execution_id']}; "
        f"source_files={payload['source_tree']['file_count']}; evidence_sha256={payload['evidence_sha256']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
