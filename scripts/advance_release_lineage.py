#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))
from rivexis_api.release_lineage import ReleaseLineageError, advance_release_lineage  # noqa: E402


def _parse_mapping(values: list[str]) -> dict[str, Path]:
    parsed: dict[str, Path] = {}
    for value in values:
        if "=" not in value:
            raise SystemExit("Release lineage advancement: FAIL - --public-key must use KEY_ID=PATH")
        key_id, raw_path = value.split("=", 1)
        key_id, raw_path = key_id.strip(), raw_path.strip()
        if not key_id or not raw_path or key_id in parsed:
            raise SystemExit(f"Release lineage advancement: FAIL - invalid or duplicate --public-key: {value!r}")
        parsed[key_id] = Path(raw_path)
    return parsed


def _external_output(path: str) -> Path:
    output = Path(path).expanduser().resolve()
    try:
        output.relative_to(ROOT.resolve())
    except ValueError:
        return output
    raise SystemExit("Release lineage advancement: FAIL - output must remain outside the Rivexis repository")


def main() -> int:
    parser = argparse.ArgumentParser(description="Advance the Rivexis P37 anti-rollback release lineage from a verified quorum attestation.")
    parser.add_argument("attestation")
    parser.add_argument("artifact")
    parser.add_argument("--channel", required=True)
    parser.add_argument("--public-key", action="append", required=True, metavar="KEY_ID=PUBLIC_KEY_PEM")
    parser.add_argument("--trust-policy", required=True)
    parser.add_argument("--bundle", default=str(ROOT / "release-certification-bundle.json"))
    parser.add_argument("--manifest", default=str(ROOT / "certification-execution-manifest.json"))
    parser.add_argument("--previous-checkpoint")
    parser.add_argument("--expected-previous-sha256")
    parser.add_argument("--allow-genesis", action="store_true")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    try:
        attestation = json.loads(Path(args.attestation).read_text())
        bundle = json.loads(Path(args.bundle).read_text())
        manifest = json.loads(Path(args.manifest).read_text())
        previous = json.loads(Path(args.previous_checkpoint).read_text()) if args.previous_checkpoint else None
        checkpoint = advance_release_lineage(
            root=ROOT,
            channel=args.channel,
            attestation=attestation,
            artifact_path=Path(args.artifact),
            trusted_public_keys=_parse_mapping(args.public_key),
            trust_policy_path=Path(args.trust_policy),
            bundle=bundle,
            manifest=manifest,
            previous_checkpoint=previous,
            expected_previous_sha256=args.expected_previous_sha256,
            allow_genesis=args.allow_genesis,
        )
    except (OSError, json.JSONDecodeError, ReleaseLineageError) as exc:
        raise SystemExit(f"Release lineage advancement: FAIL - {exc}") from exc
    output = _external_output(args.output)
    output.write_text(json.dumps(checkpoint, indent=2) + "\n")
    print(
        "Release lineage advancement: PASS "
        f"(channel={checkpoint['channel']}; release={checkpoint['release']}; sequence={checkpoint['sequence']}; "
        f"head_sha256={checkpoint['checkpoint_sha256']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
