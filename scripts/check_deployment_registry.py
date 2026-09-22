#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"apps"/"api"))

from rivexis_api.services.deployment_registry import list_protocol_deployments, REGISTRY_VERSION

rows = list_protocol_deployments()
assert rows, "deployment registry is empty"
seen = set()
for row in rows:
    key = (row["adapter"], int(row["chain_id"]), row.get("market"))
    assert key not in seen, f"duplicate registry key: {key}"
    seen.add(key)
    assert row["registry_version"] == REGISTRY_VERSION
    assert row["source_kind"].startswith("official_")
    assert str(row["source_ref"]).startswith("https://")
    assert row["contracts"], f"no contracts: {key}"
    for name, address in row["contracts"].items():
        if address is None:
            continue
        assert isinstance(address, str) and address.startswith("0x") and len(address) == 42, f"bad address {key}:{name}={address}"
        int(address[2:], 16)
print(f"Deployment registry invariant: PASS ({len(rows)} records; version={REGISTRY_VERSION})")
