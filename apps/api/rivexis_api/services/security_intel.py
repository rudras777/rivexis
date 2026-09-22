from __future__ import annotations

from typing import Any


def normalize_blockaid(body: Any) -> dict[str, Any]:
    """Normalize documented security/simulation fields without assuming absent=benign."""
    if not isinstance(body, dict):
        return {"status": "MALFORMED", "verdict": None, "features": [], "transaction_actions": [], "simulation_status": None}
    validation = body.get("validation") if isinstance(body.get("validation"), dict) else body
    verdict = None
    for key in ("result_type", "verdict", "classification", "result"):
        value = validation.get(key) if isinstance(validation, dict) else None
        if isinstance(value, str) and value:
            verdict = value
            break
    features_raw = validation.get("features") if isinstance(validation, dict) else None
    features: list[dict[str, Any]] = []
    if isinstance(features_raw, list):
        for row in features_raw[:100]:
            if isinstance(row, dict):
                features.append({
                    k: row.get(k)
                    for k in ("feature_id", "id", "type", "classification", "description", "reason")
                    if row.get(k) is not None
                })
            elif isinstance(row, str):
                features.append({"description": row})
    simulation = body.get("simulation") if isinstance(body.get("simulation"), dict) else {}
    actions = simulation.get("transaction_actions") if isinstance(simulation.get("transaction_actions"), list) else []
    return {
        "status": validation.get("status") if isinstance(validation, dict) else None,
        "verdict": verdict,
        "features": features,
        "transaction_actions": [str(x) for x in actions[:50]],
        "simulation_status": simulation.get("status"),
        "exposure_address_count": len(simulation.get("exposures") or {}) if isinstance(simulation.get("exposures"), dict) else 0,
    }


def blockaid_risk(normalized: dict[str, Any]) -> tuple[float, bool, list[str]]:
    verdict = str(normalized.get("verdict") or "").strip().lower()
    feature_types = {
        str(f.get("type") or f.get("classification") or "").strip().lower()
        for f in normalized.get("features", []) if isinstance(f, dict)
    }
    malicious = verdict == "malicious" or "malicious" in feature_types
    warning = verdict in {"warning", "suspicious"} or bool(feature_types & {"warning", "suspicious"})
    messages: list[str] = []
    if malicious:
        messages.append("Blockaid returned an explicit malicious classification.")
        return 90.0, True, messages
    if warning:
        messages.append("Blockaid returned warning/suspicious security evidence.")
        return 35.0, False, messages
    if verdict in {"benign", "safe"}:
        messages.append("Blockaid returned benign external evidence; Rivexis does not interpret this as a guarantee of safety.")
    return 0.0, False, messages
