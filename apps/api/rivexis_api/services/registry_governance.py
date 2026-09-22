from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rivexis_api.services.deployment_registry import REGISTRY_VERSION, list_protocol_deployments


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def registry_payload() -> dict[str, Any]:
    records = list_protocol_deployments()
    for row in records:
        row.pop("registry_version", None)
        row.pop("verified_on", None)
    records.sort(key=lambda r: (str(r.get("adapter")), int(r.get("chain_id", 0)), str(r.get("market") or ""), str(r.get("deployment_id"))))
    return {"registry_version": REGISTRY_VERSION, "records": records}


def registry_fingerprint(payload: dict[str, Any] | None = None) -> str:
    payload = deepcopy(payload or registry_payload())
    return hashlib.sha256(_canonical(payload).encode()).hexdigest()


def normalize_proposed(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict) or not isinstance(payload.get("records"), list):
        raise ValueError("Proposed registry must contain a records array")
    version = str(payload.get("registry_version") or "").strip()
    if not version:
        raise ValueError("Proposed registry requires registry_version")
    records = deepcopy(payload["records"])
    keys: set[tuple[str, int, str, str]] = set()
    for row in records:
        if not isinstance(row, dict):
            raise ValueError("Every proposed registry record must be an object")
        key = (str(row.get("adapter") or ""), int(row.get("chain_id") or 0), str(row.get("market") or ""), str(row.get("deployment_id") or ""))
        if not key[0] or not key[1] or not key[3]:
            raise ValueError("Every proposed registry record requires adapter, chain_id and deployment_id")
        if key in keys:
            raise ValueError(f"Duplicate proposed deployment key: {key}")
        keys.add(key)
        if not row.get("source_ref"):
            raise ValueError(f"Proposed deployment {key} has no official source_ref")
    records.sort(key=lambda r: (str(r.get("adapter")), int(r.get("chain_id", 0)), str(r.get("market") or ""), str(r.get("deployment_id"))))
    return {"registry_version": version, "records": records}


def _key(row: dict[str, Any]) -> tuple[str, int, str, str]:
    return (str(row.get("adapter")), int(row.get("chain_id", 0)), str(row.get("market") or ""), str(row.get("deployment_id")))


def build_registry_diff(proposed: dict[str, Any]) -> dict[str, Any]:
    current = registry_payload()
    proposed = normalize_proposed(proposed)
    cur = {_key(r): r for r in current["records"]}
    nxt = {_key(r): r for r in proposed["records"]}
    added = [nxt[k] for k in sorted(nxt.keys() - cur.keys())]
    removed = [cur[k] for k in sorted(cur.keys() - nxt.keys())]
    changed = []
    for k in sorted(cur.keys() & nxt.keys()):
        if _canonical(cur[k]) != _canonical(nxt[k]):
            fields = sorted({*cur[k].keys(), *nxt[k].keys()})
            field_changes = {f: {"from": cur[k].get(f), "to": nxt[k].get(f)} for f in fields if cur[k].get(f) != nxt[k].get(f)}
            changed.append({"key": list(k), "field_changes": field_changes})
    return {
        "base_version": current["registry_version"],
        "base_fingerprint": registry_fingerprint(current),
        "proposed_version": proposed["registry_version"],
        "proposed_fingerprint": registry_fingerprint(proposed),
        "changed": bool(added or removed or changed or proposed["registry_version"] != current["registry_version"]),
        "added": added,
        "removed": removed,
        "modified": changed,
    }


def prepare_update_plan(proposed: dict[str, Any]) -> dict[str, Any]:
    proposed = normalize_proposed(proposed)
    diff = build_registry_diff(proposed)
    if diff["changed"] and proposed["registry_version"] == REGISTRY_VERSION:
        raise ValueError("Registry content changed but registry_version was not bumped")
    return {
        "schema": "rivexis-registry-update-plan/v1",
        "status": "PENDING_APPROVAL" if diff["changed"] else "NO_CHANGE",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "diff": diff,
        "proposed": proposed,
        "approval": None,
    }


def approve_update_plan(plan: dict[str, Any], *, reviewer: str, approval_id: str) -> dict[str, Any]:
    if plan.get("schema") != "rivexis-registry-update-plan/v1":
        raise ValueError("Unsupported registry update plan schema")
    if plan.get("status") != "PENDING_APPROVAL":
        raise ValueError("Only PENDING_APPROVAL plans can be approved")
    reviewer = reviewer.strip()
    approval_id = approval_id.strip()
    if not reviewer or not approval_id:
        raise ValueError("reviewer and approval_id are required")
    # Recalculate against the current bundled registry so stale plans cannot be approved.
    fresh = build_registry_diff(plan["proposed"])
    prior = plan.get("diff") or {}
    if fresh.get("base_fingerprint") != prior.get("base_fingerprint") or fresh.get("proposed_fingerprint") != prior.get("proposed_fingerprint"):
        raise ValueError("Registry update plan is stale or has been modified")
    out = deepcopy(plan)
    out["status"] = "APPROVED"
    out["approval"] = {
        "reviewer": reviewer,
        "approval_id": approval_id,
        "approved_at": datetime.now(timezone.utc).isoformat(),
        "base_fingerprint": fresh["base_fingerprint"],
        "proposed_fingerprint": fresh["proposed_fingerprint"],
    }
    return out


def verify_approved_plan(plan: dict[str, Any]) -> bool:
    if plan.get("status") != "APPROVED" or not isinstance(plan.get("approval"), dict):
        raise ValueError("Registry update plan is not explicitly approved")
    fresh = build_registry_diff(plan["proposed"])
    approval = plan["approval"]
    if approval.get("base_fingerprint") != fresh["base_fingerprint"]:
        raise ValueError("Approved plan base fingerprint no longer matches the bundled registry")
    if approval.get("proposed_fingerprint") != fresh["proposed_fingerprint"]:
        raise ValueError("Approved plan proposed fingerprint does not match proposed registry")
    if not approval.get("reviewer") or not approval.get("approval_id"):
        raise ValueError("Approved plan lacks reviewer or approval_id")
    return True


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text())


def write_json(path: str | Path, value: dict[str, Any]) -> None:
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
