#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))
from rivexis_api.release_signing import verify_release_attestation  # noqa: E402


def _parse_mapping(values: list[str]) -> dict[str, Path]:
    parsed: dict[str, Path] = {}
    for value in values:
        if "=" not in value:
            raise SystemExit("Release attestation verification: FAIL - --public-key must use KEY_ID=PATH")
        key_id, raw_path = value.split("=", 1)
        key_id, raw_path = key_id.strip(), raw_path.strip()
        if not key_id or not raw_path or key_id in parsed:
            raise SystemExit(f"Release attestation verification: FAIL - invalid or duplicate --public-key: {value!r}")
        parsed[key_id] = Path(raw_path)
    return parsed


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify a Rivexis P37 detached multi-party Ed25519 release attestation.")
    parser.add_argument("attestation")
    parser.add_argument("artifact")
    parser.add_argument("--public-key", action="append", required=True, metavar="KEY_ID=PUBLIC_KEY_PEM")
    parser.add_argument("--trust-policy", required=True)
    parser.add_argument("--expect-key-id", action="append", default=[])
    parser.add_argument("--policy-id")
    parser.add_argument("--bundle", default=str(ROOT / "release-certification-bundle.json"))
    parser.add_argument("--manifest", default=str(ROOT / "certification-execution-manifest.json"))
    args = parser.parse_args()
    try:
        payload = json.loads(Path(args.attestation).read_text())
        bundle = json.loads(Path(args.bundle).read_text())
        manifest = json.loads(Path(args.manifest).read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Release attestation verification: FAIL - invalid input: {exc}") from exc
    ok = verify_release_attestation(
        payload,
        Path(args.artifact),
        _parse_mapping(args.public_key),
        Path(args.trust_policy),
        bundle=bundle,
        manifest=manifest,
        expected_key_ids=set(args.expect_key_id) if args.expect_key_id else None,
        expected_policy_id=args.policy_id,
        root=ROOT,
    )
    if not ok:
        raise SystemExit("Release attestation verification: FAIL")
    signer_ids = ",".join(item["key_id"] for item in payload["signatures"])
    print(
        "Release attestation verification: PASS "
        f"(artifact_sha256={payload['signing_request']['artifact']['sha256']}; signers={signer_ids}; "
        f"policy_id={payload['signing_request']['trust']['policy_id']}; "
        f"quorum={len(payload['signatures'])}/{payload['signing_request']['authorization']['minimum_signatures']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
