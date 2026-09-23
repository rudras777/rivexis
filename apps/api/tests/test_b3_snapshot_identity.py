from __future__ import annotations

from rivexis_api.engines import ENGINES
from rivexis_api.models.engine import EngineResult
from rivexis_api.models.enums import AnalysisStatus, EngineId, Severity
from rivexis_api.services import live_b3

ENTITY = "0x1111111111111111111111111111111111111111"
OTHER = "0x2222222222222222222222222222222222222222"
TOKEN = "0x3333333333333333333333333333333333333333"
OTHER_TOKEN = "0x4444444444444444444444444444444444444444"
ORACLE = "0x5555555555555555555555555555555555555555"
OTHER_ORACLE = "0x6666666666666666666666666666666666666666"


def snapshot(**overrides):
    row = {
        "chain_id": 1,
        "entity": ENTITY,
        "native_balance_wei": 100,
        "code_sha256": "abc",
    }
    row.update(overrides)
    return row


def assert_rejected(result):
    assert result.status == AnalysisStatus.INSUFFICIENT_DATA
    assert result.severity == Severity.UNKNOWN
    assert result.risk_score == 0
    assert result.data_confidence == 0
    assert result.engine_confidence == 0
    assert result.provider_consensus == "UNAVAILABLE"
    assert "same-entity same-chain prior B3 snapshot" in result.missing_data


def test_b3_rejects_previous_snapshot_from_different_entity_before_live_service(monkeypatch):
    monkeypatch.setattr(
        live_b3,
        "run_live_b3",
        lambda _: (_ for _ in ()).throw(AssertionError("live B3 must not run")),
    )
    result = ENGINES[EngineId.B3](
        {
            "chain": "ethereum",
            "entity": ENTITY,
            "previous_snapshot": snapshot(entity=OTHER),
        },
        False,
    )
    assert_rejected(result)
    assert "different monitored entity" in result.summary


def test_b3_rejects_previous_snapshot_from_different_chain_before_live_service(monkeypatch):
    monkeypatch.setattr(
        live_b3,
        "run_live_b3",
        lambda _: (_ for _ in ()).throw(AssertionError("live B3 must not run")),
    )
    result = ENGINES[EngineId.B3](
        {
            "chain": "ethereum",
            "entity": ENTITY,
            "previous_snapshot": snapshot(chain_id=42161),
        },
        False,
    )
    assert_rejected(result)
    assert "different blockchain network" in result.summary


def test_b3_rejects_mismatched_token_or_oracle_dependency(monkeypatch):
    monkeypatch.setattr(
        live_b3,
        "run_live_b3",
        lambda _: (_ for _ in ()).throw(AssertionError("live B3 must not run")),
    )
    token_result = ENGINES[EngineId.B3](
        {
            "chain": "ethereum",
            "entity": ENTITY,
            "token_contract": TOKEN,
            "previous_snapshot": snapshot(token_contract=OTHER_TOKEN),
        },
        False,
    )
    assert_rejected(token_result)
    assert "token_contract" in token_result.summary

    oracle_result = ENGINES[EngineId.B3](
        {
            "chain": "ethereum",
            "entity": ENTITY,
            "oracle_feed": ORACLE,
            "previous_snapshot": snapshot(oracle={"feed": OTHER_ORACLE}),
        },
        False,
    )
    assert_rejected(oracle_result)
    assert "oracle feed" in oracle_result.summary


def test_b3_same_identity_snapshot_reaches_existing_live_engine(monkeypatch):
    expected = EngineResult(
        engine_id=EngineId.B3,
        status=AnalysisStatus.PARTIAL,
        risk_score=20,
        data_confidence=80,
        engine_confidence=75,
        severity=Severity.LOW,
        summary="same snapshot identity accepted",
        provider_consensus="UNAVAILABLE",
        demo=False,
    )
    calls = []

    def fake_run(payload):
        calls.append(payload)
        return expected

    monkeypatch.setattr(live_b3, "run_live_b3", fake_run)
    result = ENGINES[EngineId.B3](
        {
            "chain": "ethereum",
            "entity": ENTITY,
            "token_contract": TOKEN,
            "oracle_feed": ORACLE,
            "previous_snapshot": snapshot(
                token_contract=TOKEN,
                oracle={"feed": ORACLE},
            ),
        },
        False,
    )

    assert len(calls) == 1
    assert result.status == AnalysisStatus.PARTIAL
    assert result.summary == "same snapshot identity accepted"
    assert result.engine_version == "1.1.0"
