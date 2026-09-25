from rivexis_api.engines import (
    ENGINES,
    LIVE_ENGINE_VERSIONS,
    _b1_transaction_effects_summary,
    _normalize_current_live_contract,
)
from rivexis_api.models.engine import EngineResult
from rivexis_api.models.enums import AnalysisStatus, EngineId, FreshnessStatus, Severity
from rivexis_api.models.evidence import EvidenceRecord, SourceConflict


def evidence(provider: str, *, engine_version: str = "1.0.0", calculation_version: str = "1.0.0") -> EvidenceRecord:
    return EvidenceRecord(
        evidence_id=f"ev-{provider}",
        provider=provider,
        source_type="fixture",
        normalized_value={"provider": provider},
        engine_version=engine_version,
        calculation_version=calculation_version,
        confidence=80,
        freshness=FreshnessStatus.CURRENT,
    )


def result(engine_id: EngineId, *, provider_consensus: str = "SINGLE_SOURCE", evidence_rows=None, conflicts=None) -> EngineResult:
    return EngineResult(
        engine_id=engine_id,
        engine_version="0.0.1",
        status=AnalysisStatus.PARTIAL,
        risk_score=25,
        data_confidence=70,
        engine_confidence=70,
        severity=Severity.LOW,
        summary="fixture",
        evidence=evidence_rows or [],
        provider_consensus=provider_consensus,
        provider_conflicts=conflicts or [],
        data_freshness={"status": "CURRENT"},
    )


def test_live_contract_normalizes_parent_and_evidence_versions_and_multi_source_consensus():
    r = result(
        EngineId.F5,
        evidence_rows=[evidence("coingecko"), evidence("direct_rpc")],
    )
    normalized = _normalize_current_live_contract(r)
    assert normalized.engine_version == "1.2.0"
    assert {e.engine_version for e in normalized.evidence} == {"1.2.0"}
    assert {e.calculation_version for e in normalized.evidence} == {"f5-live-1.2.0"}
    assert normalized.provider_consensus == "MULTI_SOURCE"
    assert normalized.data_freshness["evidence_providers"] == ["coingecko", "direct_rpc"]
    assert normalized.data_freshness["evidence_freshness"] == ["CURRENT"]


def test_shared_collector_calculation_version_is_preserved_but_parent_engine_version_is_current():
    shared = evidence(
        "direct_rpc",
        engine_version="shared-1.1.0",
        calculation_version="protocol-native-1.1.0",
    )
    normalized = _normalize_current_live_contract(result(EngineId.F3, evidence_rows=[shared]))
    assert normalized.engine_version == "1.3.0"
    assert normalized.evidence[0].engine_version == "1.3.0"
    assert normalized.evidence[0].calculation_version == "protocol-native-1.1.0"


def test_no_evidence_cannot_claim_provider_consensus_but_user_input_only_is_preserved():
    unavailable = _normalize_current_live_contract(result(EngineId.F4, provider_consensus="SINGLE_SOURCE"))
    assert unavailable.provider_consensus == "UNAVAILABLE"
    assert unavailable.data_freshness["evidence_providers"] == []

    modeled = _normalize_current_live_contract(result(EngineId.F5, provider_consensus="USER_INPUT_ONLY"))
    assert modeled.provider_consensus == "USER_INPUT_ONLY"


def test_conflicts_override_source_count_when_deriving_consensus():
    conflict = SourceConflict(
        metric="price",
        source_a="oracle",
        value_a=100,
        source_b="market",
        value_b=110,
        resolution_method="unresolved",
        resolution_confidence=0,
    )
    normalized = _normalize_current_live_contract(
        result(
            EngineId.F3,
            evidence_rows=[evidence("direct_rpc"), evidence("coingecko")],
            conflicts=[conflict],
        )
    )
    assert normalized.provider_consensus == "CONFLICTING"
    assert normalized.status == AnalysisStatus.CONFLICTING_DATA


def test_live_conflicts_promote_completed_or_partial_but_preserve_stale_primary_gate():
    conflict = SourceConflict(
        metric="entity_identity",
        source_a="nansen",
        value_a="Entity A",
        source_b="arkham",
        value_b="Entity B",
        resolution_method="unresolved_external_attribution_conflict",
        resolution_confidence=0,
    )
    for original_status in (AnalysisStatus.COMPLETED, AnalysisStatus.PARTIAL):
        r = result(
            EngineId.B4,
            evidence_rows=[evidence("nansen"), evidence("arkham")],
            conflicts=[conflict],
        )
        r.status = original_status
        normalized = _normalize_current_live_contract(r)
        assert normalized.status == AnalysisStatus.CONFLICTING_DATA
        assert normalized.provider_consensus == "CONFLICTING"

    stale = result(
        EngineId.F3,
        evidence_rows=[evidence("oracle"), evidence("market")],
        conflicts=[conflict],
    )
    stale.status = AnalysisStatus.STALE_DATA
    normalized_stale = _normalize_current_live_contract(stale)
    assert normalized_stale.status == AnalysisStatus.STALE_DATA
    assert normalized_stale.provider_consensus == "CONFLICTING"


def test_current_live_failure_paths_use_canonical_engine_versions_without_provider_calls():
    fixtures = {
        EngineId.F2: {},
        EngineId.F3: {},
        EngineId.F4: {},
        EngineId.F5: {},
    }
    for engine_id, payload in fixtures.items():
        r = ENGINES[engine_id](payload, False)
        assert r.status == AnalysisStatus.INSUFFICIENT_DATA
        assert r.engine_version == LIVE_ENGINE_VERSIONS[engine_id]
        assert r.demo is False
        assert r.provider_consensus in {"UNAVAILABLE", "USER_INPUT_ONLY"}


def test_explicit_f3_adapter_request_discards_generic_modeled_fallback(monkeypatch):
    from rivexis_api.services import live_f3

    generic = EngineResult(
        engine_id=EngineId.F3,
        status=AnalysisStatus.PARTIAL,
        risk_score=5,
        data_confidence=95,
        engine_confidence=95,
        severity=Severity.LOW,
        summary="Generic modeled path looked low risk",
        metrics={"health_factor": 2.5, "position": {"health_factor": 2.5}},
        evidence=[evidence("direct_rpc")],
        provider_consensus="SINGLE_SOURCE",
    )
    monkeypatch.setattr(live_f3, "run_live_f3", lambda _: generic)

    r = ENGINES[EngineId.F3](
        {
            "protocol_adapter": "aave_v3",
            "user_address": "0x1111111111111111111111111111111111111111",
        },
        False,
    )

    assert r.status == AnalysisStatus.INSUFFICIENT_DATA
    assert r.risk_score == 0
    assert r.data_confidence == 0
    assert r.engine_confidence == 0
    assert r.severity == Severity.UNKNOWN
    assert r.provider_consensus == "UNAVAILABLE"
    assert r.evidence == []
    assert r.metrics["requested_protocol_adapter"] == "aave_v3"
    assert r.metrics["discarded_fallback_status"] == "PARTIAL"
    assert "discarded" in r.summary.lower()
    assert "authoritative protocol-native position evidence" in r.missing_data


def test_explicit_f3_adapter_request_preserves_provider_unavailable_state(monkeypatch):
    from rivexis_api.services import live_f3

    unavailable = EngineResult(
        engine_id=EngineId.F3,
        status=AnalysisStatus.PROVIDER_UNAVAILABLE,
        risk_score=0,
        data_confidence=0,
        engine_confidence=0,
        severity=Severity.UNKNOWN,
        summary="RPC unavailable",
        provider_consensus="UNAVAILABLE",
    )
    monkeypatch.setattr(live_f3, "run_live_f3", lambda _: unavailable)

    r = ENGINES[EngineId.F3](
        {
            "protocol_adapter": "aave_v3",
            "wallet": "0x1111111111111111111111111111111111111111",
        },
        False,
    )
    assert r.status == AnalysisStatus.PROVIDER_UNAVAILABLE
    assert r.severity == Severity.UNKNOWN
    assert r.risk_score == 0


def test_authoritative_f3_adapter_position_is_not_discarded(monkeypatch):
    from rivexis_api.services import live_f3

    authoritative = EngineResult(
        engine_id=EngineId.F3,
        status=AnalysisStatus.PARTIAL,
        risk_score=72,
        data_confidence=92,
        engine_confidence=92,
        severity=Severity.HIGH,
        summary="Authoritative adapter position",
        metrics={
            "authoritative_adapter": "aave_v3",
            "position": {"health_factor": 1.1},
        },
        evidence=[
            evidence(
                "direct_rpc",
                engine_version="shared-1.1.0",
                calculation_version="protocol-native-1.1.0",
            )
        ],
        provider_consensus="SINGLE_SOURCE",
    )
    monkeypatch.setattr(live_f3, "run_live_f3", lambda _: authoritative)

    r = ENGINES[EngineId.F3](
        {
            "protocol_adapter": "aave_v3",
            "user_address": "0x1111111111111111111111111111111111111111",
        },
        False,
    )
    assert r.status == AnalysisStatus.PARTIAL
    assert r.risk_score == 72
    assert r.metrics["authoritative_adapter"] == "aave_v3"
    assert r.engine_version == "1.3.0"
    assert r.evidence[0].engine_version == "1.3.0"
    assert r.evidence[0].calculation_version == "protocol-native-1.1.0"


def test_b1_effect_summary_normalizes_trace_approvals_native_value_and_state_changes():
    entry_approval = {
        "status": "DECODED_STANDARD_SELECTOR",
        "selector": "0x095ea7b3",
        "signature": "approve(address,uint256)",
        "standard": "ERC20_OR_ERC721_AMBIGUOUS_WITHOUT_CONTRACT_INTERFACE",
        "parameters": {"spender_or_approved": "0x" + "44" * 20, "amount_or_token_id": 1},
        "confidence": 88,
    }
    internal_approval = {
        "trace_index": 1,
        "contract": "0x" + "33" * 20,
        "decode": entry_approval,
    }
    target = "0x" + "55" * 20
    metrics = {
        "to": target,
        "execution_success": True,
        "gas_estimate": 21000,
        "simulation_mode": "standards-based-rpc-dry-run",
        "calldata_decode": entry_approval,
        "call_trace": {
            "call_count": 2,
            "error_count": 0,
            "native_value_transfers": [
                {
                    "trace_index": 1,
                    "from": "0x" + "11" * 20,
                    "to": "0x" + "22" * 20,
                    "amount_wei": 16,
                }
            ],
            "approval_candidates": [internal_approval],
        },
        "state_diff": {
            "status": "NORMALIZED_PRESTATE_DIFF",
            "addresses_touched": 3,
            "addresses_changed": 1,
            "changes": [
                {
                    "address": "0x" + "33" * 20,
                    "changed_fields": ["balance"],
                    "changed_storage_slots": 2,
                }
            ],
            "truncated": False,
        },
    }
    effects = _b1_transaction_effects_summary(metrics)
    assert effects["entry_method"]["signature"] == "approve(address,uint256)"
    assert effects["execution"]["gas_estimate"] == 21000
    assert effects["internal_calls"]["available"] is True
    assert effects["internal_calls"]["call_count"] == 2
    assert effects["internal_calls"]["error_count"] == 0
    assert effects["native_value_transfers"][0]["amount_wei"] == 16
    assert len(effects["approval_candidates"]) == 2
    assert effects["approval_candidates"][0]["contract"] == target
    assert effects["state_changes"]["addresses_changed"] == 1
    assert effects["coverage"]["internal_call_trace"] is True
    assert effects["coverage"]["state_diff"] is True
    assert effects["coverage"]["canonical_token_nft_event_changes"] is False
    assert any("call traces alone are not treated as proof" in item for item in effects["limitations"])


def test_b1_effect_summary_is_explicit_when_trace_and_state_diff_are_missing():
    effects = _b1_transaction_effects_summary(
        {
            "execution_success": True,
            "calldata_decode": {"status": "UNKNOWN_SELECTOR", "selector": "0xdeadbeef", "confidence": 0},
        }
    )
    assert effects["internal_calls"]["available"] is False
    assert effects["state_changes"]["available"] is False
    assert effects["native_value_transfers"] == []
    assert effects["approval_candidates"] == []
    assert effects["asset_changes"] == []
    assert effects["approval_events"] == []
    assert effects["coverage"]["entry_calldata_decoded"] is False
    assert effects["coverage"]["canonical_token_nft_event_changes"] is False
    assert effects["coverage"]["canonical_approval_events"] is False
    assert len(effects["limitations"]) == 3


def test_b1_effect_summary_does_not_promote_unavailable_trace_evidence():
    effects = _b1_transaction_effects_summary(
        {
            "calldata_decode": {"status": "NO_CALLDATA"},
            "call_trace": {
                "status": "UNAVAILABLE_CALL_TRACE",
                "call_count": 0,
                "valid_call_count": 0,
                "error_count": 0,
                "native_value_transfers": [{"amount_wei": 99}],
                "approval_candidates": [{"contract": "0x" + "11" * 20}],
            },
        }
    )

    assert effects["internal_calls"]["available"] is False
    assert effects["coverage"]["internal_call_trace"] is False
    assert effects["native_value_transfers"] == []
    assert effects["approval_candidates"] == []


def test_b1_effect_summary_exposes_partial_trace_integrity():
    effects = _b1_transaction_effects_summary(
        {
            "calldata_decode": {"status": "NO_CALLDATA"},
            "call_trace": {
                "status": "PARTIAL_CALL_TRACE",
                "call_count": 2,
                "valid_call_count": 1,
                "error_count": 0,
                "malformed_node_count": 1,
                "discarded_node_count": 1,
                "truncated": True,
            },
        }
    )

    assert effects["internal_calls"]["available"] is True
    assert effects["internal_calls"]["status"] == "PARTIAL_CALL_TRACE"
    assert effects["internal_calls"]["valid_call_count"] == 1
    assert effects["internal_calls"]["truncated"] is True
    assert any("partially normalized" in item for item in effects["limitations"])


def test_b1_effect_summary_exposes_normalized_event_effects_without_token_metadata_inference():
    event_effects = {
        "status": "NORMALIZED_STANDARD_EVENT_LOGS",
        "source": "tenderly_simulation",
        "outcome": "predicted",
        "logs_available": True,
        "input_log_count": 3,
        "decoded_log_count": 2,
        "asset_change_count": 1,
        "approval_event_count": 1,
        "unknown_log_count": 1,
        "malformed_log_count": 0,
        "truncated": False,
        "asset_changes": [
            {
                "standard": "ERC20",
                "event": "Transfer",
                "contract": "0x" + "22" * 20,
                "from": "0x" + "11" * 20,
                "to": "0x" + "33" * 20,
                "amount_raw": "1250000",
            }
        ],
        "approval_events": [
            {
                "standard": "ERC20",
                "event": "Approval",
                "contract": "0x" + "22" * 20,
                "owner": "0x" + "11" * 20,
                "spender": "0x" + "44" * 20,
                "amount_raw": "7",
            }
        ],
        "raw_amounts_unscaled": True,
    }
    effects = _b1_transaction_effects_summary(
        {
            "execution_success": True,
            "simulation_mode": "tenderly",
            "calldata_decode": {"status": "NO_CALLDATA"},
            "event_effects": event_effects,
        }
    )
    assert effects["coverage"]["canonical_token_nft_event_changes"] is True
    assert effects["coverage"]["canonical_approval_events"] is True
    assert effects["asset_changes"][0]["amount_raw"] == "1250000"
    assert effects["approval_events"][0]["amount_raw"] == "7"
    assert effects["event_logs"]["source"] == "tenderly_simulation"
    assert effects["event_logs"]["outcome"] == "predicted"
    assert effects["event_logs"]["unknown_log_count"] == 1
    assert any("raw on-chain integers" in item for item in effects["limitations"])
    assert any("Unrecognized/non-standard" in item for item in effects["limitations"])


def test_live_b1_dispatch_attaches_effect_summary_without_inventing_asset_changes(monkeypatch):
    from rivexis_api.services import live_b1

    b1 = EngineResult(
        engine_id=EngineId.B1,
        status=AnalysisStatus.PARTIAL,
        risk_score=15,
        data_confidence=82,
        engine_confidence=72,
        severity=Severity.LOW,
        summary="RPC dry-run fixture",
        metrics={
            "execution_success": True,
            "calldata_decode": {
                "status": "DECODED_STANDARD_SELECTOR",
                "selector": "0xa9059cbb",
                "signature": "transfer(address,uint256)",
                "standard": "ERC20",
                "confidence": 95,
            },
            "call_trace": {
                "call_count": 1,
                "error_count": 0,
                "native_value_transfers": [],
                "approval_candidates": [],
            },
            "state_diff": None,
        },
        evidence=[evidence("direct_rpc")],
        provider_consensus="SINGLE_SOURCE",
    )
    monkeypatch.setattr(live_b1, "run_live_b1", lambda _: b1)

    normalized = ENGINES[EngineId.B1]({"transaction": {}}, False)
    effects = normalized.metrics["transaction_effects"]
    assert effects["entry_method"]["signature"] == "transfer(address,uint256)"
    assert effects["coverage"]["internal_call_trace"] is True
    assert effects["coverage"]["state_diff"] is False
    assert effects["coverage"]["canonical_token_nft_event_changes"] is False
    assert normalized.engine_version == "1.3.0"
    assert normalized.evidence[0].engine_version == "1.3.0"


def test_every_declared_live_engine_has_an_explicit_canonical_version():
    assert set(LIVE_ENGINE_VERSIONS) == set(EngineId)
    assert all(version.count(".") == 2 for version in LIVE_ENGINE_VERSIONS.values())
