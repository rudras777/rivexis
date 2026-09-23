from rivexis_api.engines import ENGINES, LIVE_ENGINE_VERSIONS, _normalize_current_live_contract
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


def test_every_declared_live_engine_has_an_explicit_canonical_version():
    assert set(LIVE_ENGINE_VERSIONS) == set(EngineId)
    assert all(version.count(".") == 2 for version in LIVE_ENGINE_VERSIONS.values())
