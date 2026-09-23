from __future__ import annotations

from rivexis_api.engines import ENGINES
from rivexis_api.models.enums import AnalysisStatus, EngineId, Severity
from rivexis_api.provider_clients import ProviderCall
from rivexis_api.services import live_b5

WALLET = "0x1111111111111111111111111111111111111111"


def quote_body(**overrides):
    body = {
        "id": "route-1",
        "tool": "across",
        "toolDetails": {"name": "Across"},
        "action": {
            "fromChainId": 1,
            "toChainId": 42161,
            "fromAmount": "1000000",
            "fromAddress": WALLET,
            "toAddress": WALLET,
            "slippage": 0.005,
            "fromToken": {"symbol": "USDC", "coinKey": "USDC"},
            "toToken": {"symbol": "USDC", "coinKey": "USDC"},
        },
        "estimate": {
            "fromAmount": "1000000",
            "toAmount": "998000",
            "toAmountMin": "993000",
            "executionDuration": 45,
            "gasCosts": [],
            "feeCosts": [],
        },
        "includedSteps": [{"id": "1"}],
    }
    for key, value in overrides.items():
        if key.startswith("action__"):
            body["action"][key.removeprefix("action__")] = value
        elif key.startswith("estimate__"):
            body["estimate"][key.removeprefix("estimate__")] = value
        else:
            body[key] = value
    return body


class FakeLifi:
    body = quote_body()
    calls = []

    def quote(self, params):
        type(self).calls.append(params)
        return ProviderCall(
            "lifi",
            "quote-1",
            "https://li.quest/v1/quote",
            type(self).body,
            2.0,
        )


def payload(**overrides):
    base = {
        "source_chain": "ethereum",
        "destination_chain": "arbitrum",
        "source_token": "USDC",
        "destination_token": "USDC",
        "amount": "1000000",
        "wallet": WALLET,
        "slippage": 0.005,
    }
    base.update(overrides)
    return base


def install(monkeypatch, body):
    FakeLifi.body = body
    FakeLifi.calls = []
    monkeypatch.setattr(live_b5, "LifiClient", FakeLifi)


def test_b5_matching_quote_remains_partial_and_records_integrity(monkeypatch):
    install(monkeypatch, quote_body())
    result = live_b5.run_live_b5(payload())

    assert result.status == AnalysisStatus.PARTIAL
    assert result.engine_version == "1.3.0"
    assert result.metrics["integrity"] == {"status": "MATCHED", "conflict_count": 0}
    assert result.metrics["from_chain"] == 1
    assert result.metrics["to_chain"] == 42161
    assert result.metrics["requested"]["from_amount"] == "1000000"
    assert result.metrics["gas_cost_usd"] == 0.0
    assert result.metrics["fee_cost_usd"] == 0.0
    assert result.metrics["execution_duration_seconds"] == 45.0
    assert result.provider_conflicts == []
    assert result.risk_score > 0
    assert FakeLifi.calls[0]["toAddress"] == WALLET


def test_b5_mismatched_quote_fails_closed_and_discards_route_scoring(monkeypatch):
    install(
        monkeypatch,
        quote_body(
            action__toChainId=10,
            action__fromAmount="999999",
            action__fromAddress="0x2222222222222222222222222222222222222222",
        ),
    )
    result = live_b5.run_live_b5(payload())

    assert result.status == AnalysisStatus.CONFLICTING_DATA
    assert result.severity == Severity.UNKNOWN
    assert result.risk_score == 0
    assert result.engine_confidence == 0
    assert result.provider_consensus == "CONFLICTING"
    metrics = {conflict.metric for conflict in result.provider_conflicts}
    assert "route.to_chain_id" in metrics
    assert "route.from_amount" in metrics
    assert "route.from_address" in metrics
    assert result.metrics["integrity"]["status"] == "CONFLICTING"
    assert "request-consistent and internally valid cross-chain route quote" in result.missing_data


def test_b5_rejects_internally_impossible_minimum_above_expected(monkeypatch):
    install(monkeypatch, quote_body(estimate__toAmount="998000", estimate__toAmountMin="999000"))
    result = live_b5.run_live_b5(payload())

    assert result.status == AnalysisStatus.CONFLICTING_DATA
    assert result.risk_score == 0
    assert result.severity == Severity.UNKNOWN
    assert any(conflict.metric == "route.minimum_not_above_expected" for conflict in result.provider_conflicts)


def test_b5_rejects_malformed_or_untrustworthy_cost_metadata(monkeypatch):
    bad_cost_sets = [
        [{"amountUSD": -1}],
        [{"amountUSD": "NaN"}],
        [{"amountUSD": "Infinity"}],
        [{"amountUSD": None}],
        ["not-a-cost-row"],
        {"amountUSD": "1"},
    ]
    for gas_costs in bad_cost_sets:
        install(monkeypatch, quote_body(estimate__gasCosts=gas_costs))
        result = live_b5.run_live_b5(payload())
        assert result.status == AnalysisStatus.CONFLICTING_DATA
        assert result.risk_score == 0
        assert result.severity == Severity.UNKNOWN
        assert any(conflict.metric == "route.gas_costs" for conflict in result.provider_conflicts)

    install(monkeypatch, quote_body(estimate__feeCosts=[{"amountUSD": "NaN"}]))
    result = live_b5.run_live_b5(payload())
    assert result.status == AnalysisStatus.CONFLICTING_DATA
    assert any(conflict.metric == "route.fee_costs" for conflict in result.provider_conflicts)


def test_b5_sums_only_finite_non_negative_provider_costs(monkeypatch):
    install(
        monkeypatch,
        quote_body(
            estimate__gasCosts=[{"amountUSD": "1.25"}, {"amountUSD": 0.75}],
            estimate__feeCosts=[{"amountUSD": "2.50"}],
        ),
    )
    result = live_b5.run_live_b5(payload())

    assert result.status == AnalysisStatus.PARTIAL
    assert result.metrics["gas_cost_usd"] == 2.0
    assert result.metrics["fee_cost_usd"] == 2.5


def test_b5_rejects_invalid_execution_duration_and_step_structure(monkeypatch):
    for duration in (-1, "NaN", "Infinity", None, True):
        install(monkeypatch, quote_body(estimate__executionDuration=duration))
        result = live_b5.run_live_b5(payload())
        assert result.status == AnalysisStatus.CONFLICTING_DATA
        assert any(conflict.metric == "route.execution_duration" for conflict in result.provider_conflicts)

    for steps in (None, {}, [None], [{}], ["step"]):
        install(monkeypatch, quote_body(includedSteps=steps))
        result = live_b5.run_live_b5(payload())
        assert result.status == AnalysisStatus.CONFLICTING_DATA
        assert any(conflict.metric == "route.included_steps" for conflict in result.provider_conflicts)


def test_b5_non_finite_requested_slippage_fails_before_provider_call(monkeypatch):
    install(monkeypatch, quote_body())
    for bad in ("NaN", "Infinity", "-Infinity"):
        result = live_b5.run_live_b5(payload(slippage=bad))
        assert result.status == AnalysisStatus.INSUFFICIENT_DATA
        assert result.severity == Severity.UNKNOWN
    assert FakeLifi.calls == []


def test_b5_invalid_amount_and_wallet_fail_before_provider_call(monkeypatch):
    install(monkeypatch, quote_body())

    bad_amount = live_b5.run_live_b5(payload(amount="0"))
    assert bad_amount.status == AnalysisStatus.INSUFFICIENT_DATA
    assert bad_amount.severity == Severity.UNKNOWN
    assert FakeLifi.calls == []

    bad_wallet = live_b5.run_live_b5(payload(wallet="not-an-address"))
    assert bad_wallet.status == AnalysisStatus.INSUFFICIENT_DATA
    assert bad_wallet.severity == Severity.UNKNOWN
    assert FakeLifi.calls == []


def test_b5_dispatch_preserves_current_contract_and_evidence_versions(monkeypatch):
    install(monkeypatch, quote_body())
    result = ENGINES[EngineId.B5](payload(), False)

    assert result.engine_version == "1.3.0"
    assert {e.engine_version for e in result.evidence} == {"1.3.0"}
    assert {e.calculation_version for e in result.evidence} == {"b5-live-1.3.0"}
    assert result.status == AnalysisStatus.PARTIAL
