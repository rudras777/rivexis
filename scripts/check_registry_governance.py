#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"apps"/"api"))

from copy import deepcopy

from rivexis_api.services.registry_governance import (
    approve_update_plan, prepare_update_plan, registry_fingerprint, registry_payload, verify_approved_plan,
)

current = registry_payload()
fingerprint = registry_fingerprint(current)
assert len(fingerprint) == 64 and int(fingerprint, 16) >= 0
assert prepare_update_plan(deepcopy(current))["status"] == "NO_CHANGE"
proposed = deepcopy(current)
proposed["registry_version"] = current["registry_version"] + "-self-test"
proposed["records"][0]["source"] = proposed["records"][0]["source"] + " (review-test)"
plan = prepare_update_plan(proposed)
assert plan["status"] == "PENDING_APPROVAL"
approved = approve_update_plan(plan, reviewer="rivexis-release-gate", approval_id="SELF-TEST")
assert verify_approved_plan(approved)
print(f"Registry governance gate: PASS (fingerprint={fingerprint})")
