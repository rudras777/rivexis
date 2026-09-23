from __future__ import annotations

from datetime import datetime, timezone

import pytest

from rivexis_api.models.enums import AnalysisStatus, FreshnessStatus, Severity
from rivexis_api.provider_clients import ProviderCall
from rivexis_api.services import live_f3

FEED = "0x1111111111111111111111111111111111111111"


def word(value: int) -> str:
    return f"{value & ((1 << 256) - 1):064x}"


class OracleRpc:
    def __init__(self, *, block="0x64", updated_at: int | None = None, answer=2_000_00000000):
        self.block = block
        self.updated_at = updated_at or int(datetime.now(timezone.utc).timestamp())
        self.answer = answer
        self.calls: list[tuple[str, list | None]] = []

    def call(self, method, params=None):
        self.calls.append((method, params))
        if method == "eth_blockNumber":
            return ProviderCall("direct_rpc", "block", "http://rpc.test", self.block, 1.0)
        if method == "eth_call":
            selector = params[0]["data"]
            if selector == live_f3.DECIMALS_SELECTOR:
                return ProviderCall("direct_rpc", "decimals", "http://rpc.test", "0x8", 1.0)
            if selector == live_f3.LATEST_ROUND_DATA_SELECTOR:
                payload = "0x" + "".join(
                    [
                        word(10),
                        word(self.answer),
                        word(self.updated_at - 5),
                        word(self.updated_at),
                        word(10),
                    ]
                )
                return ProviderCall("direct_rpc", "round", "http://rpc.test", payload, 1.0)
        raise AssertionError((method, params))


def install_rpc(monkeypatch, rpc: OracleRpc):
    probe = ProviderCall("direct_rpc", "probe", "http://rpc.test", "0x1", 1.0)
    monkeypatch.setattr(
        live_f3,
        "select_rpc_client",
        lambda chain: ("direct_rpc", rpc, probe, []),
    )


def base_input(**overrides):
    data = {
        "chain": "ethereum",
        "collateral_price_feed": FEED,
        "collateral_units": 2.0,
        "debt_units": 1000.0,
        "liquidation_threshold": 0.8,
        "debt_price_usd": 1.0,
    }
    data.update(overrides)
    return data


@pytest.mark.parametrize(
    "field,value",
    [
        ("collateral_units", True),
        ("debt_units", float("nan")),
        ("liquidation_threshold", float("inf")),
        ("price_conflict_tolerance_pct", False),
    ],
)
def test_f3_rejects_boolean_or_nonfinite_model_inputs_before_provider_use(monkeypatch, field, value):
    monkeypatch.setattr(
        live_f3,
        "select_rpc_client",
        lambda *_: (_ for _ in ()).throw(AssertionError("provider should not be called")),
    )

    result = live_f3.run_live_f3(base_input(**{field: value}))

    assert result.status == AnalysisStatus.INSUFFICIENT_DATA
    assert result.severity == Severity.UNKNOWN
    assert result.risk_score == 0


def test_f3_future_oracle_timestamp_is_unknown_not_live(monkeypatch):
    now = int(datetime.now(timezone.utc).timestamp())
    rpc = OracleRpc(updated_at=now + 3600)
    install_rpc(monkeypatch, rpc)

    result = live_f3.run_live_f3(base_input())

    assert result.status == AnalysisStatus.PARTIAL
    assert result.data_freshness["status"] == FreshnessStatus.UNKNOWN.value
    assert "credible collateral oracle observation timestamp" in result.missing_data
    assert any("materially in the future" in warning for warning in result.warnings)
    oracle_evidence = [
        item for item in result.evidence if item.source_type == "direct_oracle_state"
    ]
    assert oracle_evidence
    assert {item.freshness for item in oracle_evidence} == {FreshnessStatus.UNKNOWN}
    assert result.metrics["oracle"]["timestamp_status"] == "FUTURE"


def test_f3_oracle_reads_are_pinned_to_captured_block(monkeypatch):
    rpc = OracleRpc(block="0x64")
    install_rpc(monkeypatch, rpc)

    result = live_f3.run_live_f3(base_input())

    assert result.status == AnalysisStatus.PARTIAL
    eth_calls = [params for method, params in rpc.calls if method == "eth_call"]
    assert len(eth_calls) == 2
    assert all(params[-1] == "0x64" for params in eth_calls)
    assert not any(params[-1] == "latest" for params in eth_calls)
    assert result.block_reference == 100
    assert result.metrics["block_tag"] == "0x64"
    assert result.metrics["oracle"]["block_tag"] == "0x64"
    assert all(
        item.block_number == 100
        for item in result.evidence
        if item.source_type == "direct_oracle_state"
    )
    assert any("pinned to captured RPC block 0x64" in text for text in result.assumptions)


def test_f3_round_data_rejects_trailing_abi_words():
    payload = "0x" + "".join(word(value) for value in (1, 2, 3, 4, 5, 6))

    with pytest.raises(ValueError, match="exactly five ABI words"):
        live_f3._decode_round_data(payload)


def test_f3_nonpositive_or_nonfinite_user_debt_price_is_rejected(monkeypatch):
    rpc = OracleRpc()
    install_rpc(monkeypatch, rpc)

    for bad_price in (-1, 0, True, float("nan"), float("inf")):
        result = live_f3.run_live_f3(base_input(debt_price_usd=bad_price))
        assert result.status == AnalysisStatus.INSUFFICIENT_DATA
        assert result.severity == Severity.UNKNOWN
        assert "debt_price_usd" in result.summary


def test_f3_malformed_block_number_fails_closed(monkeypatch):
    rpc = OracleRpc(block="not-hex")
    install_rpc(monkeypatch, rpc)

    result = live_f3.run_live_f3(base_input())

    assert result.status == AnalysisStatus.PROVIDER_UNAVAILABLE
    assert result.severity == Severity.UNKNOWN
    assert result.risk_score == 0
    assert "live oracle evidence" in result.missing_data
