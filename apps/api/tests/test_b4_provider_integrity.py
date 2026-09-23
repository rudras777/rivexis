from __future__ import annotations

from rivexis_api.models.enums import AnalysisStatus, FreshnessStatus, Severity
from rivexis_api.provider_clients import ProviderCall
from rivexis_api.services import live_b4

WALLET = "0x1111111111111111111111111111111111111111"
OTHER = "0x2222222222222222222222222222222222222222"


class FakeRpc:
    def __init__(self, *, block="0x64", balance="0xde0b6b3a7640000"):
        self.block = block
        self.balance = balance

    def call(self, method, params=None):
        if method == "eth_blockNumber":
            return ProviderCall("direct_rpc", "block", "http://rpc.test", self.block, 1.0)
        if method == "eth_getBalance":
            return ProviderCall("direct_rpc", "balance", "http://rpc.test", self.balance, 1.0)
        raise AssertionError((method, params))


def install_rpc(monkeypatch, rpc=None):
    rpc = rpc or FakeRpc()
    monkeypatch.setattr(
        live_b4,
        "select_rpc_client",
        lambda chain: ("direct_rpc", rpc, ProviderCall("direct_rpc", "probe", "http://rpc.test", "0x1", 1.0), []),
    )


class NoEtherscan:
    configured = False


class NoNansen:
    configured = False


class NoArkham:
    configured = False
    credentialed = False
    license_approved = False


def install_optional_none(monkeypatch):
    monkeypatch.setattr(live_b4, "EtherscanClient", NoEtherscan)
    monkeypatch.setattr(live_b4, "NansenClient", NoNansen)
    monkeypatch.setattr(live_b4, "ArkhamClient", NoArkham)


def test_b4_invalid_history_limit_fails_before_provider_calls(monkeypatch):
    monkeypatch.setattr(
        live_b4,
        "select_rpc_client",
        lambda *_: (_ for _ in ()).throw(AssertionError("provider should not be called")),
    )

    result = live_b4.run_live_b4({"wallet": WALLET, "limit": "not-an-int"})

    assert result.status == AnalysisStatus.INSUFFICIENT_DATA
    assert result.severity == Severity.UNKNOWN
    assert result.risk_score == 0
    assert result.missing_data == ["positive history limit"]


def test_b4_malformed_rpc_numeric_state_does_not_become_zero_balance(monkeypatch):
    install_rpc(monkeypatch, FakeRpc(block="not-hex"))
    install_optional_none(monkeypatch)

    result = live_b4.run_live_b4({"wallet": WALLET})

    assert result.status == AnalysisStatus.PROVIDER_UNAVAILABLE
    assert result.severity == Severity.UNKNOWN
    assert result.risk_score == 0
    assert result.provider_status[0]["status"] == "MALFORMED_RESPONSE"
    assert "direct blockchain state" in result.missing_data


def test_b4_non_object_nansen_response_is_not_healthy_no_label_evidence(monkeypatch):
    install_rpc(monkeypatch)
    monkeypatch.setattr(live_b4, "EtherscanClient", NoEtherscan)

    class BadNansen:
        configured = True

        def address_labels(self, *, address, chain):
            return ProviderCall("nansen", "nansen-bad", "https://nansen.test", ["unexpected"], 2.0)

    monkeypatch.setattr(live_b4, "NansenClient", BadNansen)
    monkeypatch.setattr(live_b4, "ArkhamClient", NoArkham)

    result = live_b4.run_live_b4({"wallet": WALLET})

    assert result.status == AnalysisStatus.PARTIAL
    assert result.metrics["entity_profile"]["identity"] == "UNKNOWN ADDRESS"
    assert result.engine_confidence == 55
    assert not any(item.provider == "nansen" for item in result.evidence)
    assert any(
        row["provider_id"] == "nansen" and row["status"] == "MALFORMED_RESPONSE"
        for row in result.provider_status
    )
    assert any("non-object" in warning for warning in result.warnings)


def test_b4_valid_no_label_response_is_evidence_but_does_not_boost_attribution_confidence(monkeypatch):
    install_rpc(monkeypatch)
    monkeypatch.setattr(live_b4, "EtherscanClient", NoEtherscan)

    class EmptyNansen:
        configured = True

        def address_labels(self, *, address, chain):
            return ProviderCall("nansen", "nansen-empty", "https://nansen.test", {"data": []}, 2.0)

    monkeypatch.setattr(live_b4, "NansenClient", EmptyNansen)
    monkeypatch.setattr(live_b4, "ArkhamClient", NoArkham)

    result = live_b4.run_live_b4({"wallet": WALLET})

    nansen_evidence = [item for item in result.evidence if item.provider == "nansen"]
    assert len(nansen_evidence) == 1
    assert nansen_evidence[0].freshness == FreshnessStatus.UNKNOWN
    assert result.metrics["entity_profile"]["identity"] == "UNKNOWN ADDRESS"
    assert result.data_confidence == 58
    assert result.engine_confidence == 55


def test_b4_attributed_label_uses_unknown_freshness_without_provider_timestamp(monkeypatch):
    install_rpc(monkeypatch)
    monkeypatch.setattr(live_b4, "EtherscanClient", NoEtherscan)

    class LabelNansen:
        configured = True

        def address_labels(self, *, address, chain):
            return ProviderCall(
                "nansen",
                "nansen-label",
                "https://nansen.test",
                {"data": [{"label": "Example Exchange"}]},
                2.0,
            )

    monkeypatch.setattr(live_b4, "NansenClient", LabelNansen)
    monkeypatch.setattr(live_b4, "ArkhamClient", NoArkham)

    result = live_b4.run_live_b4({"wallet": WALLET})

    nansen_evidence = next(item for item in result.evidence if item.provider == "nansen")
    assert nansen_evidence.freshness == FreshnessStatus.UNKNOWN
    assert result.metrics["entity_profile"]["identity"] == "Example Exchange"
    assert result.data_confidence == 65
    assert result.engine_confidence == 62


def test_b4_malformed_indexed_value_row_is_skipped_not_zeroed_or_crashed(monkeypatch):
    install_rpc(monkeypatch)

    class BadHistoryEtherscan:
        configured = True

        def account_transactions(self, chain, address, *, offset):
            return ProviderCall(
                "etherscan",
                "txs",
                "https://etherscan.test",
                {"result": [{"from": WALLET, "to": OTHER, "value": "not-a-number"}]},
                2.0,
            )

        def token_transactions(self, chain, address, *, offset):
            return ProviderCall("etherscan", "tokens", "https://etherscan.test", {"result": []}, 2.0)

    monkeypatch.setattr(live_b4, "EtherscanClient", BadHistoryEtherscan)
    monkeypatch.setattr(live_b4, "NansenClient", NoNansen)
    monkeypatch.setattr(live_b4, "ArkhamClient", NoArkham)

    result = live_b4.run_live_b4({"wallet": WALLET})

    assert result.status == AnalysisStatus.PARTIAL
    assert result.metrics["activity"]["malformed_indexed_rows_skipped"] == 1
    assert result.metrics["activity"]["native_out"] == 0
    assert "fully normalized indexed transaction/token-transfer values" in result.missing_data
    assert any("Skipped 1 indexed history row" in warning for warning in result.warnings)
    etherscan_evidence = next(item for item in result.evidence if item.provider == "etherscan")
    assert etherscan_evidence.freshness == FreshnessStatus.UNKNOWN
