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


def test_every_declared_live_engine_has_an_explicit_canonical_version():
    assert set(LIVE_ENGINE_VERSIONS) == set(EngineId)
    assert all(version.count(".") == 2 for version in LIVE_ENGINE_VERSIONS.values())
