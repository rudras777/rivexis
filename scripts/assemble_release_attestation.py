#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))
from rivexis_api.release_signing import ReleaseSigningError, assemble_release_attestation  # noqa: E402


def _parse_mapping(values: list[str]) -> dict[str, Path]:
    parsed: dict[str, Path] = {}
    for value in values:
        if "=" not in value:
            raise SystemExit("Release attestation assembly: FAIL - --public-key must use KEY_ID=PATH")
        key_id, raw_path = value.split("=", 1)
        key_id, raw_path = key_id.strip(), raw_path.strip()
        if not key_id or not raw_path or key_id in parsed:
            raise SystemExit(f"Release attestation assembly: FAIL - invalid or duplicate --public-key: {value!r}")
        parsed[key_id] = Path(raw_path)
    return parsed


def main() -> int:
    parser = argparse.ArgumentParser(description="Assemble a Rivexis P37 quorum attestation from independently produced detached signatures.")
    parser.add_argument("request")
    parser.add_argument("artifact")
    parser.add_argument("--signature", action="append", required=True, help="detached signer envelope JSON; repeat per signer")
    parser.add_argument("--public-key", action="append", required=True, metavar="KEY_ID=PUBLIC_KEY_PEM")
    parser.add_argument("--trust-policy", required=True)
    parser.add_argument("--bundle", default=str(ROOT / "release-certification-bundle.json"))
    parser.add_argument("--manifest", default=str(ROOT / "certification-execution-manifest.json"))
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    try:
        request = json.loads(Path(args.request).read_text())
        bundle = json.loads(Path(args.bundle).read_text())
        manifest = json.loads(Path(args.manifest).read_text())
        signatures = [json.loads(Path(path).read_text()) for path in args.signature]
        attestation = assemble_release_attestation(
            ROOT,
            request,
            Path(args.artifact),
            bundle,
            manifest,
            signatures,
            _parse_mapping(args.public_key),
            Path(args.trust_policy),
        )
    except (OSError, json.JSONDecodeError, ReleaseSigningError) as exc:
        raise SystemExit(f"Release attestation assembly: FAIL - {exc}") from exc
    output = Path(args.output).expanduser().resolve()
    try:
        output.relative_to(ROOT.resolve())
    except ValueError:
        pass
    else:
        raise SystemExit("Release attestation assembly: FAIL - output must remain outside the Rivexis repository")
    output.write_text(json.dumps(attestation, indent=2) + "\n")
    signer_ids = ",".join(item["key_id"] for item in attestation["signatures"])
    print(f"Release attestation assembly: PASS (signers={signer_ids}; request_sha256={request['request_sha256']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
