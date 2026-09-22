#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))
from rivexis_api.release_lineage import verify_release_against_lineage  # noqa: E402


def _parse_mapping(values: list[str]) -> dict[str, Path]:
    parsed: dict[str, Path] = {}
    for value in values:
        if "=" not in value:
            raise SystemExit("Release lineage verification: FAIL - --public-key must use KEY_ID=PATH")
        key_id, raw_path = value.split("=", 1)
        key_id, raw_path = key_id.strip(), raw_path.strip()
        if not key_id or not raw_path or key_id in parsed:
            raise SystemExit(f"Release lineage verification: FAIL - invalid or duplicate --public-key: {value!r}")
        parsed[key_id] = Path(raw_path)
    return parsed


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify a Rivexis P37 release against a trusted anti-rollback lineage head.")
    parser.add_argument("checkpoint")
    parser.add_argument("attestation")
    parser.add_argument("artifact")
    parser.add_argument("--channel", required=True)
    parser.add_argument("--expected-head-sha256", required=True)
    parser.add_argument("--minimum-release-number", type=int)
    parser.add_argument("--public-key", action="append", required=True, metavar="KEY_ID=PUBLIC_KEY_PEM")
    parser.add_argument("--trust-policy", required=True)
    parser.add_argument("--bundle", default=str(ROOT / "release-certification-bundle.json"))
    parser.add_argument("--manifest", default=str(ROOT / "certification-execution-manifest.json"))
    args = parser.parse_args()
    try:
        checkpoint = json.loads(Path(args.checkpoint).read_text())
        attestation = json.loads(Path(args.attestation).read_text())
        bundle = json.loads(Path(args.bundle).read_text())
        manifest = json.loads(Path(args.manifest).read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Release lineage verification: FAIL - invalid input: {exc}") from exc
    ok = verify_release_against_lineage(
        root=ROOT,
        checkpoint=checkpoint,
        expected_head_sha256=args.expected_head_sha256,
        channel=args.channel,
        attestation=attestation,
        artifact_path=Path(args.artifact),
        trusted_public_keys=_parse_mapping(args.public_key),
        trust_policy_path=Path(args.trust_policy),
        bundle=bundle,
        manifest=manifest,
        minimum_release_number=args.minimum_release_number,
    )
    if not ok:
        raise SystemExit("Release lineage verification: FAIL")
    print(
        "Release lineage verification: PASS "
        f"(channel={checkpoint['channel']}; release={checkpoint['release']}; sequence={checkpoint['sequence']}; "
        f"head_sha256={checkpoint['checkpoint_sha256']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
