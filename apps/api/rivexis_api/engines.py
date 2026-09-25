from __future__ import annotations

from uuid import uuid4

from rivexis_api.chains import normalize_chain
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
    EngineId.B1: "1.3.0",
    EngineId.B2: "1.1.0",
    EngineId.B3: "1.1.0",
    EngineId.B4: "1.0.0",
    EngineId.B5: "1.2.0",
    EngineId.F1: "1.2.0",
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


def _b1_canonical_address(value: object) -> str | None:
    if not isinstance(value, str) or len(value) != 42 or not value.startswith("0x"):
        return None
    try:
        int(value[2:], 16)
    except ValueError:
        return None
    return value.lower()


def _b1_approval_scope(candidate: dict) -> dict:
    scoped = dict(candidate)
    if "contract" in scoped:
        scoped["contract"] = _b1_canonical_address(scoped.get("contract"))
    decoded = candidate.get("decode")
    if not isinstance(decoded, dict):
        scoped["scope"] = "UNKNOWN"
        return scoped
    signature = decoded.get("signature")
    parameters = decoded.get("parameters")
    if not isinstance(parameters, dict):
        scoped["scope"] = "UNKNOWN"
        return scoped
    if signature == "approve(address,uint256)":
        amount = parameters.get("amount_or_token_id")
        if not isinstance(amount, int) or isinstance(amount, bool) or amount < 0:
            scoped["scope"] = "UNKNOWN"
            return scoped
        scoped["scope"] = (
            "UINT256_MAX_CANDIDATE"
            if decoded.get("unlimited_approval_candidate") is True
            else "BOUNDED_AMOUNT_OR_TOKEN_ID"
        )
        scoped["enabled"] = amount > 0
        return scoped
    if signature == "setApprovalForAll(address,bool)":
        enabled = parameters.get("approved")
        if not isinstance(enabled, bool):
            scoped["scope"] = "UNKNOWN"
            return scoped
        scoped["scope"] = "ALL_ASSETS_OPERATOR" if enabled else "OPERATOR_REVOCATION"
        scoped["enabled"] = enabled
        return scoped
    scoped["scope"] = "UNKNOWN"
    return scoped


def _b1_security_observations(
    *,
    calldata: dict,
    trace: dict | None,
    trace_available: bool,
    state_diff: dict | None,
    state_diff_available: bool,
    approvals: list[dict],
) -> dict:
    signals: list[dict] = []
    trace_status = trace.get("status") if trace else None
    canonical_trace_available = bool(
        trace_available
        and trace_status in {"NORMALIZED_CALL_TRACE", "PARTIAL_CALL_TRACE"}
        and trace.get("valid_call_count")
    )
    valid_calls = []
    if canonical_trace_available and isinstance(trace.get("calls"), list):
        valid_calls = [
            call
            for call in trace["calls"]
            if isinstance(call, dict) and call.get("integrity") == "VALID"
        ]

    patterns = (
        ("DELEGATECALL", "DELEGATECALL_OBSERVED", "execution_context"),
        ("CALLCODE", "CALLCODE_OBSERVED", "execution_context"),
        ("CREATE", "CONTRACT_CREATION_OBSERVED", "contract_lifecycle"),
        ("CREATE2", "DETERMINISTIC_CONTRACT_CREATION_OBSERVED", "contract_lifecycle"),
        ("SELFDESTRUCT", "SELFDESTRUCT_OPCODE_PATH_OBSERVED", "contract_lifecycle"),
    )
    for call_type, signal_type, category in patterns:
        matching = [call for call in valid_calls if call.get("call_type") == call_type]
        if matching:
            signals.append(
                {
                    "type": signal_type,
                    "category": category,
                    "count": len(matching),
                    "trace_indices": [call.get("trace_index") for call in matching[:64]],
                }
            )
    failed_calls = [call for call in valid_calls if call.get("error")]
    if failed_calls:
        signals.append(
            {
                "type": "INTERNAL_CALL_FAILURE_OBSERVED",
                "category": "execution_failure",
                "count": len(failed_calls),
                "trace_indices": [call.get("trace_index") for call in failed_calls[:64]],
            }
        )

    for scope, signal_type in (
        ("UINT256_MAX_CANDIDATE", "UNLIMITED_APPROVAL_CANDIDATE"),
        ("ALL_ASSETS_OPERATOR", "ALL_ASSETS_OPERATOR_APPROVAL_CANDIDATE"),
    ):
        matching = [
            candidate
            for candidate in approvals
            if candidate.get("scope") == scope
            and (
                candidate.get("source") == "entry_calldata"
                or canonical_trace_available
            )
            and candidate.get("contract") is not None
        ]
        if not matching:
            continue
        signals.append(
            {
                "type": signal_type,
                "category": "permission_scope",
                "count": len(matching),
                "candidates": [
                    {
                        "trace_index": candidate.get("trace_index"),
                        "contract": candidate.get("contract"),
                    }
                    for candidate in matching[:64]
                ],
            }
        )

    valid_state_changes = (
        state_diff.get("changes")
        if state_diff_available and isinstance(state_diff.get("changes"), list)
        else []
    )
    for change_type, signal_type in (
        ("ACCOUNT_CREATED", "ACCOUNT_CREATION_OBSERVED"),
        ("ACCOUNT_DELETED", "ACCOUNT_DELETION_OBSERVED"),
    ):
        matching = [
            change
            for change in valid_state_changes
            if isinstance(change, dict) and change.get("change_type") == change_type
        ]
        if matching:
            signals.append(
                {
                    "type": signal_type,
                    "category": "state_lifecycle",
                    "count": len(matching),
                    "addresses": [change.get("address") for change in matching[:64]],
                }
            )
    code_changes = [
        change
        for change in valid_state_changes
        if isinstance(change, dict)
        and change.get("change_type") == "MODIFIED"
        and isinstance(change.get("changed_fields"), list)
        and "code" in change["changed_fields"]
    ]
    if code_changes:
        signals.append(
            {
                "type": "RUNTIME_CODE_CHANGE_OBSERVED",
                "category": "state_lifecycle",
                "count": len(code_changes),
                "addresses": [change.get("address") for change in code_changes[:64]],
            }
        )

    entry_status = calldata.get("status")
    entry_available = bool(
        entry_status
        and entry_status
        not in {"NO_CALLDATA", "NO_SELECTOR", "UNKNOWN_SELECTOR", "MALFORMED_STANDARD_CALLDATA"}
    )
    coverage_available = bool(
        entry_available or canonical_trace_available or state_diff_available
    )
    return {
        "status": (
            "OBSERVATIONS_PRESENT"
            if signals
            else "NO_STRUCTURAL_OBSERVATION"
            if coverage_available
            else "INSUFFICIENT_COVERAGE"
        ),
        "is_security_verdict": False,
        "signals": signals,
        "signal_count": len(signals),
        "coverage": {
            "entry_calldata": entry_available,
            "canonical_internal_call_trace": canonical_trace_available,
            "canonical_state_diff": state_diff_available,
        },
        "note": "Structural execution observations are review cues, not proof of maliciousness or safety.",
    }


def _b1_transaction_effects_summary(metrics: dict) -> dict:
    """Build a conservative canonical B1 effects summary from existing evidence.

    The summary reshapes normalized calldata, call-trace, state-diff and standard
    event-log evidence. It never invents token metadata or decodes unknown logs by
    analogy with a known standard.
    """

    calldata = metrics.get("calldata_decode")
    if not isinstance(calldata, dict):
        calldata = {}
    trace = metrics.get("call_trace")
    if not isinstance(trace, dict):
        trace = None
    trace_available = bool(
        trace
        and trace.get("call_count")
        and trace.get("status") != "UNAVAILABLE_CALL_TRACE"
    )
    state_diff = metrics.get("state_diff")
    if not isinstance(state_diff, dict):
        state_diff = None
    state_diff_available = bool(
        state_diff
        and state_diff.get("status")
        in {"NORMALIZED_PRESTATE_DIFF", "PARTIAL_PRESTATE_DIFF"}
    )
    event_effects = metrics.get("event_effects")
    if not isinstance(event_effects, dict):
        event_effects = None
    event_logs_normalized = bool(
        event_effects
        and event_effects.get("logs_available")
        and event_effects.get("status") == "NORMALIZED_STANDARD_EVENT_LOGS"
    )

    entry_approval = None
    signature = calldata.get("signature")
    if signature in {"approve(address,uint256)", "setApprovalForAll(address,bool)"}:
        entry_approval = {
            "trace_index": None,
            "contract": metrics.get("to"),
            "decode": calldata,
            "source": "entry_calldata",
        }

    internal_approvals = list(trace.get("approval_candidates") or []) if trace_available else []
    approvals = [
        _b1_approval_scope(candidate)
        for candidate in ([entry_approval] if entry_approval else [])
        + internal_approvals
        if isinstance(candidate, dict)
    ]
    native_transfers = list(trace.get("native_value_transfers") or []) if trace_available else []
    changes = list(state_diff.get("changes") or []) if state_diff_available else []
    asset_changes = list(event_effects.get("asset_changes") or []) if event_effects else []
    approval_events = list(event_effects.get("approval_events") or []) if event_effects else []

    limitations = []
    if not trace_available:
        limitations.append("Internal call trace was not available or not requested.")
    elif trace.get("status") == "PARTIAL_CALL_TRACE":
        limitations.append(
            "Internal call trace was only partially normalized; malformed or bounded nodes were excluded from promoted effects."
        )
    if not state_diff_available:
        limitations.append("Before/after contract-state diff was not available or not requested.")
    elif state_diff.get("status") == "PARTIAL_PRESTATE_DIFF":
        limitations.append(
            "Before/after contract-state diff was only partially normalized; malformed or bounded state was excluded from the change summary."
        )
    if not event_logs_normalized:
        limitations.append(
            "Canonical standard token/NFT event-log effects were not available from this run; call traces alone are not treated as proof of asset changes."
        )
    else:
        limitations.append(
            "Event amounts and token IDs are raw on-chain integers; token decimals, symbols, prices and ownership semantics are not inferred beyond the emitted standard event."
        )
        if event_effects.get("unknown_log_count"):
            limitations.append("Unrecognized/non-standard event logs remain semantically unclassified.")
        if event_effects.get("malformed_log_count"):
            limitations.append("Malformed standard-signature logs were excluded from canonical effects.")
        if event_effects.get("truncated"):
            limitations.append("Large event batches were output-capped; total effect counts remain authoritative for the normalized log set.")

    security_observations = _b1_security_observations(
        calldata=calldata,
        trace=trace,
        trace_available=trace_available,
        state_diff=state_diff,
        state_diff_available=state_diff_available,
        approvals=approvals,
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
            "available": trace_available,
            "status": trace.get("status") if trace else None,
            "call_count": trace.get("call_count") if trace else None,
            "valid_call_count": trace.get("valid_call_count") if trace else None,
            "error_count": trace.get("error_count") if trace else None,
            "malformed_node_count": trace.get("malformed_node_count") if trace else None,
            "discarded_node_count": trace.get("discarded_node_count") if trace else None,
            "truncated": trace.get("truncated") if trace else None,
        },
        "native_value_transfers": native_transfers,
        "approval_candidates": approvals,
        "asset_changes": asset_changes,
        "approval_events": approval_events,
        "security_observations": security_observations,
        "event_logs": {
            "available": event_logs_normalized,
            "source": event_effects.get("source") if event_effects else None,
            "outcome": event_effects.get("outcome") if event_effects else None,
            "input_log_count": event_effects.get("input_log_count") if event_effects else None,
            "decoded_log_count": event_effects.get("decoded_log_count") if event_effects else None,
            "asset_change_count": event_effects.get("asset_change_count") if event_effects else None,
            "approval_event_count": event_effects.get("approval_event_count") if event_effects else None,
            "unknown_log_count": event_effects.get("unknown_log_count") if event_effects else None,
            "malformed_log_count": event_effects.get("malformed_log_count") if event_effects else None,
            "truncated": event_effects.get("truncated") if event_effects else None,
        },
        "state_changes": {
            "available": state_diff_available,
            "status": state_diff.get("status") if state_diff else None,
            "addresses_touched": state_diff.get("addresses_touched") if state_diff else None,
            "addresses_changed": state_diff.get("addresses_changed") if state_diff else None,
            "changes": changes,
            "malformed_address_count": state_diff.get("malformed_address_count") if state_diff else None,
            "malformed_account_count": state_diff.get("malformed_account_count") if state_diff else None,
            "malformed_field_count": state_diff.get("malformed_field_count") if state_diff else None,
            "malformed_storage_entry_count": state_diff.get("malformed_storage_entry_count") if state_diff else None,
            "discarded_address_count": state_diff.get("discarded_address_count") if state_diff else None,
            "truncated": state_diff.get("truncated") if state_diff else None,
        },
        "coverage": {
            "entry_calldata_decoded": bool(calldata.get("status") and calldata.get("status") not in {"NO_CALLDATA", "NO_SELECTOR", "UNKNOWN_SELECTOR"}),
            "internal_call_trace": trace_available,
            "state_diff": state_diff_available,
            "canonical_token_nft_event_changes": event_logs_normalized,
            "canonical_approval_events": event_logs_normalized,
        },
        "limitations": limitations,
    }


def _b3_snapshot_contract_error(input_data: dict) -> EngineResult | None:
    """Reject B3 change detection against an unrelated prior snapshot."""

    previous = input_data.get("previous_snapshot")
    if previous is None:
        return None
    if not isinstance(previous, dict):
        return _b3_snapshot_failure("previous_snapshot must be an object produced by B3")

    current_entity = str(
        input_data.get("entity")
        or input_data.get("address")
        or input_data.get("wallet")
        or input_data.get("contract")
        or ""
    ).strip().lower()
    previous_entity = str(previous.get("entity") or "").strip().lower()
    if not previous_entity:
        return _b3_snapshot_failure(
            "previous_snapshot is missing the monitored entity identity"
        )
    if current_entity and previous_entity != current_entity:
        return _b3_snapshot_failure(
            "previous_snapshot belongs to a different monitored entity"
        )

    try:
        current_chain = normalize_chain(
            input_data.get("chain") or input_data.get("network")
        )
    except ValueError:
        return None
    previous_chain_value = previous.get("chain_id")
    if isinstance(previous_chain_value, bool):
        return _b3_snapshot_failure(
            "previous_snapshot is missing a valid chain_id identity"
        )
    if isinstance(previous_chain_value, int):
        previous_chain_id = previous_chain_value
    elif isinstance(previous_chain_value, str) and previous_chain_value.isdigit():
        previous_chain_id = int(previous_chain_value)
    else:
        return _b3_snapshot_failure(
            "previous_snapshot is missing a valid chain_id identity"
        )
    if previous_chain_id != current_chain.chain_id:
        return _b3_snapshot_failure(
            "previous_snapshot belongs to a different blockchain network"
        )

    current_token = str(input_data.get("token_contract") or "").strip().lower()
    previous_token = str(previous.get("token_contract") or "").strip().lower()
    if current_token and not previous_token:
        return _b3_snapshot_failure(
            "previous_snapshot is missing the monitored token_contract identity"
        )
    if current_token and current_token != previous_token:
        return _b3_snapshot_failure(
            "previous_snapshot token_contract does not match the current monitor"
        )

    current_oracle = str(input_data.get("oracle_feed") or "").strip().lower()
    previous_oracle_data = previous.get("oracle")
    previous_oracle = (
        str(previous_oracle_data.get("feed") or "").strip().lower()
        if isinstance(previous_oracle_data, dict)
        else ""
    )
    if current_oracle and not previous_oracle:
        return _b3_snapshot_failure(
            "previous_snapshot is missing the monitored oracle feed identity"
        )
    if current_oracle and current_oracle != previous_oracle:
        return _b3_snapshot_failure(
            "previous_snapshot oracle feed does not match the current monitor"
        )
    return None


def _b3_snapshot_failure(message: str) -> EngineResult:
    return EngineResult(
        engine_id=EngineId.B3,
        engine_version=LIVE_ENGINE_VERSIONS[EngineId.B3],
        status=AnalysisStatus.INSUFFICIENT_DATA,
        risk_score=0,
        data_confidence=0,
        engine_confidence=0,
        severity=Severity.UNKNOWN,
        summary=message,
        warnings=[
            "B3 change detection was not run because prior-state identity could not be proven."
        ],
        missing_data=["same-entity same-chain prior B3 snapshot"],
        provider_consensus="UNAVAILABLE",
        data_freshness={"status": FreshnessStatus.UNKNOWN.value},
        assumptions=[
            "Rivexis does not compare monitoring snapshots across different or unverified entities/networks."
        ],
        demo=False,
    )


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

        snapshot_error = _b3_snapshot_contract_error(input_data)
        result = snapshot_error or run_live_b3(input_data)
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
