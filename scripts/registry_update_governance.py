#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))

from rivexis_api.services.registry_governance import (  # noqa:E402
    approve_update_plan, load_json, prepare_update_plan, registry_fingerprint,
    registry_payload, verify_approved_plan, write_json,
)


def main() -> int:
    p = argparse.ArgumentParser(description="Rivexis protocol deployment registry review gate")
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("fingerprint")
    plan = sub.add_parser("plan"); plan.add_argument("--proposed", required=True); plan.add_argument("--out", required=True)
    approve = sub.add_parser("approve"); approve.add_argument("--plan", required=True); approve.add_argument("--reviewer", required=True); approve.add_argument("--approval-id", required=True); approve.add_argument("--out", required=True)
    verify = sub.add_parser("verify"); verify.add_argument("--plan", required=True)
    export = sub.add_parser("export"); export.add_argument("--out", required=True)
    args = p.parse_args()
    if args.command == "fingerprint":
        print(json.dumps({"registry_version": registry_payload()["registry_version"], "fingerprint": registry_fingerprint()}, indent=2)); return 0
    if args.command == "export":
        write_json(args.out, registry_payload()); return 0
    if args.command == "plan":
        out = prepare_update_plan(load_json(args.proposed)); write_json(args.out, out); print(json.dumps(out["diff"], indent=2)); return 0
    if args.command == "approve":
        out = approve_update_plan(load_json(args.plan), reviewer=args.reviewer, approval_id=args.approval_id); write_json(args.out, out); return 0
    if args.command == "verify":
        verify_approved_plan(load_json(args.plan)); print("APPROVED registry update plan verified"); return 0
    return 2

if __name__ == "__main__":
    raise SystemExit(main())
