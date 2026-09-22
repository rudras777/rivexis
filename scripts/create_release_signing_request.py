#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))
from rivexis_api.release_signing import ReleaseSigningError, build_release_signing_request  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a Rivexis P37 source-bound detached release signing request.")
    parser.add_argument("artifact", help="final immutable release artifact; must be outside the source repository")
    parser.add_argument("--trust-policy", required=True, help="external organizational release trust policy JSON")
    parser.add_argument("--bundle", default=str(ROOT / "release-certification-bundle.json"))
    parser.add_argument("--manifest", default=str(ROOT / "certification-execution-manifest.json"))
    parser.add_argument("--output", required=True, help="signing request JSON; keep outside the source repository")
    args = parser.parse_args()
    try:
        bundle = json.loads(Path(args.bundle).read_text())
        manifest = json.loads(Path(args.manifest).read_text())
        request = build_release_signing_request(ROOT, Path(args.artifact), bundle, manifest, Path(args.trust_policy))
    except (OSError, json.JSONDecodeError, ReleaseSigningError) as exc:
        raise SystemExit(f"Release signing request: FAIL - {exc}") from exc
    output = Path(args.output).expanduser().resolve()
    try:
        output.relative_to(ROOT.resolve())
    except ValueError:
        pass
    else:
        raise SystemExit("Release signing request: FAIL - output must remain outside the Rivexis repository")
    output.write_text(json.dumps(request, indent=2) + "\n")
    print(f"Release signing request: PASS (request_sha256={request['request_sha256']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
