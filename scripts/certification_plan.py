#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))
from rivexis_api.certification_profiles import certification_plan  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Print the P37 certification runner/gate plan without secret values.")
    parser.add_argument("--output", help="optional JSON output path")
    args = parser.parse_args()
    payload = certification_plan()
    rendered = json.dumps(payload, indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(rendered)
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
