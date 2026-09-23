from __future__ import annotations

from uuid import uuid4

from rivexis_api.models.engine import EngineResult
from rivexis_api.models.enums import AnalysisStatus, EngineId, FreshnessStatus, Severity
from rivexis_api.models.evidence import EvidenceRecord, SourceConflict

ENGINE_NAMES = {
    EngineId.B1: "Transaction Simulation Engine",
    EngineId.B2: "Transaction & Contract Security Engine",
    EngineId.B3: "Real-Time Threat & Monitoring Engine",
    EngineId.B4: "On-Chain Entity & Fund-Flow Intelligence Engine",
    EngineId.B5: "Cross-Chain Route & Bridge Intelligence Engine",
    EngineId.F1: "Portfolio & Exposure Engine",
    EngineId.F2: "Protocol Risk Engine",
    EngineId.F3: "Position & Liquidation Risk Engine",
    EngineId.F4: "Yield & Strategy Risk Engine",
    EngineId.F5: "Treasury Allocation & Scenario Engine",
}

# Canonical versions for NEW live runs. Historical persisted analyses retain the
# version that was stored with them; this map is applied only at live dispatch.
LIVE_ENGINE_VERSIONS = {
    EngineId.B1: "1.2.0",
    EngineId.B2: "1.1.0",
    EngineId.B3: "1.1.0",
    EngineId.B4: "1.0.0",
    EngineId.B5: "1.1.0",
    EngineId.F1: "1.1.0",
    EngineId.F2: "1.2.0",
    EngineId.F3: "1.3.0",
    EngineId.F4: "1.2.0",
    EngineId.F5: "1.2.0",
}


def _sev(score):
    return (
        Severity.CRITICAL
        if score >= 80
        else Severity.HIGH
        if score >= 60
        else Severity.MODERATE
        if score >= 35
        else Severity.LOW
    )


def _b1_transaction_effects_summary(metrics: dict) -> dict:
    """Build a conservative canonical B1 effects summary from existing evidence.

    This does not infer token/NFT events that were never observed. It only reshapes
    already-normalized calldata, call-trace and prestate-diff evidence into a stable
    summary for downstream UI/report consumers.
    """

    calldata = metrics.get("calldata_decode")
    if not isinstance(calldata, dict):
        calldata = {}
    trace = metrics.get("call_trace")
    if not isinstance(trace, dict):
        trace = None
    state_diff = metrics.get("state_diff")
    if not isinstance(state_diff, dict):
        state_diff = None

    entry_approval = None
    signature = calldata.get("signature")
    if signature in {"approve(address,uint256)", "setApprovalForAll(address,bool)"}:
        entry_approval = {
            "trace_index": None,
            "contract": metrics.get("to"),
            "decode": calldata,
            "source": "entry_calldata",
        }

    internal_approvals = list(trace.get("approval_candidates") or []) if trace else []
    approvals = ([entry_approval] if entry_approval else []) + internal_approvals
    native_transfers = list(trace.get("native_value_transfers") or []) if trace else []
    changes = list(state_diff.get("changes") or []) if state_diff else []

    limitations = []
    if trace is None:
        limitations.append("Internal call trace was not available or not requested.")
    if state_diff is None or state_diff.get("status") != "NORMALIZED_PRESTATE_DIFF":
        limitations.append("Before/after contract-state diff was not available or not requested.")
    limitations.append(
        "Token/NFT transfer-event normalization is not proven by call traces alone; event/log evidence is not represented as a canonical asset-change list here."
    )

    return {
        "entry_method": {
            "status": calldata.get("status"),
            "selector": calldata.get("selector"),
            "signature": calldata.get("signature"),
            "standard": calldata.get("standard"),
            "confidence": calldata.get("confidence"),
        },
        "execution": {
            "success": metrics.get("execution_success"),
            "revert_reason": metrics.get("revert_reason"),
            "gas_estimate": metrics.get("gas_estimate") or metrics.get("gas_used"),
            "simulation_mode": metrics.get("simulation_mode"),
        },
        "internal_calls": {
            "available": trace is not None,
            "call_count": trace.get("call_count") if trace else None,
            "error_count": trace.get("error_count") if trace else None,
        },
        "native_value_transfers": native_transfers,
        "approval_candidates": approvals,
        "state_changes": {
            "available": bool(state_diff and state_diff.get("status") == "NORMALIZED_PRESTATE_DIFF"),
            "addresses_touched": state_diff.get("addresses_touched") if state_diff else None,
            "addresses_changed": state_diff.get("addresses_changed") if state_diff else None,
            "changes": changes,
            "truncated": state_diff.get("truncated") if state_diff else None,
        },
        "coverage": {
            "entry_calldata_decoded": bool(calldata.get("status") and calldata.get("status") not in {"NO_CALLDATA", "NO_SELECTOR", "UNKNOWN_SELECTOR"}),
            "internal_call_trace": trace is not None,
            "state_diff": bool(state_diff and state_diff.get("status") == "NORMALIZED_PRESTATE_DIFF"),
            "canonical_token_nft_event_changes": False,
        },
        "limitations": limitations,
    }


def _normalize_current_live_contract(result: EngineResult) -> EngineResult:
    """Normalize provenance fields for a newly executed live engine result.

    This intentionally runs only on fresh live dispatches. It must never be used
    to rewrite historical persisted analyses during retrieval/review.
    """

    expected_version = LIVE_ENGINE_VERSIONS[result.engine_id]
    result.engine_version = expected_version

    for evidence in result.evidence:
        # Evidence belongs to this engine run even when a shared collector or
        # provider adapter produced the raw observation. Collector identity is
        # retained separately in calculation_version/source_type/provider.
        evidence.engine_version = expected_version
        if evidence.calculation_version == "1.0.0":
            evidence.calculation_version = (
                f"{result.engine_id.value.lower()}-live-{expected_version}"
            )

    if result.engine_id == EngineId.B1 and isinstance(result.metrics, dict):
        result.metrics["transaction_effects"] = _b1_transaction_effects_summary(
            result.metrics
        )

    # Unresolved provider conflicts are a first-class analysis state. A fresh live
    # result must not describe itself as ordinary COMPLETED/PARTIAL while also
    # carrying unresolved SourceConflict records. Preserve STALE_DATA and terminal
    # unavailable/failure states because they communicate a stronger primary gate.
    if result.provider_conflicts and result.status in {
        AnalysisStatus.COMPLETED,
        AnalysisStatus.PARTIAL,
    }:
        result.status = AnalysisStatus.CONFLICTING_DATA

    providers = {e.provider for e in result.evidence if e.provider}
    if result.provider_conflicts:
        result.provider_consensus = "CONFLICTING"
    elif not providers:
        # Preserve USER_INPUT_ONLY where an engine intentionally models declared
        # user inputs without provider evidence; otherwise absence is unavailable.
        if result.provider_consensus != "USER_INPUT_ONLY":
            result.provider_consensus = "UNAVAILABLE"
    elif len(providers) == 1:
        result.provider_consensus = "SINGLE_SOURCE"
    else:
        result.provider_consensus = "MULTI_SOURCE"

    if result.data_freshness is None:
        result.data_freshness = {}
    result.data_freshness["evidence_providers"] = sorted(providers)
    result.data_freshness["evidence_freshness"] = sorted(
        {e.freshness.value for e in result.evidence}
    )
    return result


def _explicit_f3_adapter_requested(input_data: dict) -> bool:
    return bool(
        input_data.get("protocol_adapter")
        and (input_data.get("user_address") or input_data.get("wallet"))
    )


def _enforce_explicit_f3_adapter_contract(
    result: EngineResult, input_data: dict
) -> EngineResult:
    """Reject silent generic fallback for an explicitly requested F3 adapter.

    The F3 service can use a caller-modeled oracle path when no authoritative
    protocol adapter is requested. If the caller explicitly requests a protocol
    adapter, however, a generic modeled result must not be presented as though the
    requested authoritative position evidence succeeded.
    """

    if not _explicit_f3_adapter_requested(input_data):
        return result

    metrics = result.metrics if isinstance(result.metrics, dict) else {}
    authoritative_adapter = metrics.get("authoritative_adapter")
    position = metrics.get("position")
    if authoritative_adapter and isinstance(position, dict):
        return result

    requested = str(input_data.get("protocol_adapter"))
    return EngineResult(
        engine_id=EngineId.F3,
        engine_version=LIVE_ENGINE_VERSIONS[EngineId.F3],
        status=(
            AnalysisStatus.PROVIDER_UNAVAILABLE
            if result.status == AnalysisStatus.PROVIDER_UNAVAILABLE
            else AnalysisStatus.INSUFFICIENT_DATA
        ),
        risk_score=0,
        data_confidence=0,
        engine_confidence=0,
        severity=Severity.UNKNOWN,
        summary=(
            "F3 was asked to use an authoritative protocol adapter, but that "
            "adapter did not yield an authoritative position. The generic "
            "caller-modeled fallback was discarded."
        ),
        metrics={
            "requested_protocol_adapter": requested,
            "discarded_fallback_status": result.status.value,
        },
        warnings=[
            "Explicit protocol_adapter requests fail closed when authoritative "
            "position evidence is unavailable; remove protocol_adapter only if "
            "you intentionally want the separately disclosed generic modeled path."
        ],
        missing_data=["authoritative protocol-native position evidence"],
        provider_consensus="UNAVAILABLE",
        data_freshness={"status": FreshnessStatus.UNKNOWN.value},
        assumptions=[
            "No generic position-risk conclusion is substituted for an explicitly "
            "requested protocol-adapter result."
        ],
        demo=False,
    )


def _demo_evidence(engine_id, input_data):
    return EvidenceRecord(
        evidence_id=str(uuid4()),
        provider="Rivexis Demo Adapter",
        source_type="demo",
        normalized_value=input_data,
        confidence=75,
        freshness=FreshnessStatus.CURRENT,
    )


def _score(engine_id, d):
    # Deterministic, transparent demo heuristics only. Live engines must use normalized provider evidence.
    if engine_id == EngineId.B1:
        return min(
            100,
            (45 if d.get("will_revert") else 10)
            + (35 if d.get("unlimited_approval") else 0)
            + (20 if d.get("suspicious_value_flow") else 0),
        )
    if engine_id == EngineId.B2:
        return min(
            100,
            (85 if d.get("known_malicious") else 0)
            + (35 if d.get("unlimited_approval") else 0)
            + (20 if d.get("unverified_contract") else 0),
        )
    if engine_id == EngineId.B3:
        return min(
            100,
            (80 if d.get("active_exploit") else 0)
            + (40 if d.get("oracle_anomaly") else 0)
            + (30 if d.get("liquidity_deterioration") else 0),
        )
    if engine_id == EngineId.B4:
        return min(
            100,
            (35 if d.get("label_conflict") else 0)
            + (30 if d.get("suspicious_flow") else 0)
            + (20 if d.get("holder_concentration", 0) > 0.7 else 0),
        )
    if engine_id == EngineId.B5:
        return min(
            100,
            float(d.get("route_risk", 25))
            + (20 if d.get("bridge_incident") else 0)
            + (15 if d.get("low_liquidity") else 0),
        )
    if engine_id == EngineId.F1:
        concentration = float(d.get("largest_exposure_pct", 25))
        return min(
            100,
            max(10, concentration)
            + (25 if d.get("stablecoin_concentration", 0) > 0.7 else 0),
        )
    if engine_id == EngineId.F2:
        return min(
            100,
            (60 if d.get("exploit_history") else 0)
            + (25 if d.get("admin_privilege") else 0)
            + (25 if d.get("oracle_risk") else 0)
            + (20 if d.get("low_liquidity") else 0),
        )
    if engine_id == EngineId.F3:
        hf = float(d.get("health_factor", 2.0))
        return 90 if hf < 1.05 else 75 if hf < 1.2 else 45 if hf < 1.5 else 20
    if engine_id == EngineId.F4:
        apy = float(d.get("apy", 0))
        return min(
            100,
            20
            + (25 if apy > 30 else 0)
            + (30 if d.get("incentive_dependent") else 0)
            + (25 if d.get("lockup") else 0),
        )
    if engine_id == EngineId.F5:
        concentration = float(d.get("largest_allocation_pct", 25))
        return min(
            100,
            max(15, concentration)
            + (30 if d.get("stablecoin_depeg_scenario_loss_pct", 0) > 20 else 0),
        )
    return 0


def _run_live(engine_id: EngineId, input_data: dict) -> EngineResult:
    if engine_id == EngineId.B1:
        from rivexis_api.services.live_b1 import run_live_b1

        result = run_live_b1(input_data)
    elif engine_id == EngineId.B2:
        from rivexis_api.services.live_b2 import run_live_b2

        result = run_live_b2(input_data)
    elif engine_id == EngineId.B3:
        from rivexis_api.services.live_b3 import run_live_b3

        result = run_live_b3(input_data)
    elif engine_id == EngineId.B4:
        from rivexis_api.services.live_b4 import run_live_b4

        result = run_live_b4(input_data)
    elif engine_id == EngineId.B5:
        from rivexis_api.services.live_b5 import run_live_b5

        result = run_live_b5(input_data)
    elif engine_id == EngineId.F1:
        from rivexis_api.services.live_f1 import run_live_f1

        result = run_live_f1(input_data)
    elif engine_id == EngineId.F2:
        from rivexis_api.services.live_f2 import run_live_f2

        result = run_live_f2(input_data)
    elif engine_id == EngineId.F3:
        from rivexis_api.services.live_f3 import run_live_f3

        result = _enforce_explicit_f3_adapter_contract(
            run_live_f3(input_data), input_data
        )
    elif engine_id == EngineId.F4:
        from rivexis_api.services.live_f4 import run_live_f4

        result = run_live_f4(input_data)
    elif engine_id == EngineId.F5:
        from rivexis_api.services.live_f5 import run_live_f5

        result = run_live_f5(input_data)
    else:
        result = EngineResult(
            engine_id=engine_id,
            status=AnalysisStatus.INSUFFICIENT_DATA,
            risk_score=0,
            data_confidence=0,
            engine_confidence=0,
            severity=Severity.UNKNOWN,
            summary=f"{ENGINE_NAMES[engine_id]} requires normalized live provider evidence.",
            warnings=["No fabricated live analysis was produced."],
            missing_data=["normalized provider evidence"],
            provider_consensus="UNAVAILABLE",
            demo=False,
        )
    return _normalize_current_live_contract(result)


def run_engine(engine_id: EngineId, input_data: dict, demo: bool = False):
    if not demo:
        return _run_live(engine_id, input_data)

    score = _score(engine_id, input_data)
    blockers = []
    warnings = []
    mitigations = []
    conflicts = []
    if input_data.get("known_malicious") or input_data.get("active_exploit"):
        blockers.append("Material security blocker detected in demonstration input")
    if input_data.get("unlimited_approval"):
        warnings.append("Unlimited approval increases token exposure")
        mitigations.append("Reduce approval to the minimum required amount")
    if input_data.get("label_conflict"):
        conflicts.append(
            SourceConflict(
                metric="entity_label",
                source_a="Demo Source A",
                value_a="Entity A",
                source_b="Demo Source B",
                value_b="Entity B",
                severity="high",
                resolution_method="unresolved",
                resolution_confidence=0,
            )
        )
        warnings.append("Entity labels conflict; identity is not resolved")
    if input_data.get("price_conflict_pct", 0) > 3:
        conflicts.append(
            SourceConflict(
                metric="reference_price",
                source_a="Demo Price A",
                value_a=100,
                source_b="Demo Price B",
                value_b=100 * (1 + float(input_data["price_conflict_pct"]) / 100),
                difference_percentage=float(input_data["price_conflict_pct"]),
                severity="high",
                resolution_method="unresolved",
                resolution_confidence=0,
            )
        )
    status = AnalysisStatus.CONFLICTING_DATA if conflicts else AnalysisStatus.COMPLETED
    conf = 65 if conflicts else 82
    return EngineResult(
        engine_id=engine_id,
        status=status,
        risk_score=score,
        data_confidence=conf,
        engine_confidence=80,
        severity=_sev(score),
        summary=(
            f"Demonstration result for {ENGINE_NAMES[engine_id]}: "
            f"detected risk score {score:.0f}/100."
        ),
        metrics={"input_echo": input_data},
        warnings=warnings,
        hard_blockers=blockers,
        mitigations=mitigations,
        safer_alternatives=mitigations[:],
        evidence=[_demo_evidence(engine_id, input_data)],
        provider_consensus="CONFLICTING" if conflicts else "SINGLE SOURCE",
        provider_conflicts=conflicts,
        data_freshness={"status": "CURRENT", "source": "demo"},
        assumptions=["Synthetic demonstration inputs supplied by the user/interface."],
        demo=True,
    )


ENGINES = {
    eid: (lambda data, demo=False, eid=eid: run_engine(eid, data, demo))
    for eid in EngineId
}
