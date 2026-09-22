#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))
from rivexis_api.release_signing import ReleaseSigningError, sign_release_request  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Independently sign one Rivexis P37 release request with one external Ed25519 key.")
    parser.add_argument("request")
    parser.add_argument("artifact")
    parser.add_argument("--key-id", required=True)
    parser.add_argument("--private-key", required=True, help="single signer private key PEM; must remain outside repository")
    parser.add_argument("--trust-policy", required=True)
    parser.add_argument("--bundle", default=str(ROOT / "release-certification-bundle.json"))
    parser.add_argument("--manifest", default=str(ROOT / "certification-execution-manifest.json"))
    parser.add_argument("--output", required=True, help="detached signature envelope JSON; keep outside repository")
    args = parser.parse_args()
    try:
        request = json.loads(Path(args.request).read_text())
        bundle = json.loads(Path(args.bundle).read_text())
        manifest = json.loads(Path(args.manifest).read_text())
        envelope = sign_release_request(
            ROOT,
            request,
            Path(args.artifact),
            bundle,
            manifest,
            key_id=args.key_id,
            private_key_path=Path(args.private_key),
            trust_policy_path=Path(args.trust_policy),
        )
    except (OSError, json.JSONDecodeError, ReleaseSigningError) as exc:
        raise SystemExit(f"Detached release signature: FAIL - {exc}") from exc
    output = Path(args.output).expanduser().resolve()
    try:
        output.relative_to(ROOT.resolve())
    except ValueError:
        pass
    else:
        raise SystemExit("Detached release signature: FAIL - output must remain outside the Rivexis repository")
    output.write_text(json.dumps(envelope, indent=2) + "\n")
    print(
        "Detached release signature: PASS "
        f"(key_id={envelope['key_id']}; request_sha256={envelope['request_sha256']}; "
        f"signed_payload_sha256={envelope['signed_payload_sha256']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
