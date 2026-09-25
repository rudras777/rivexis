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
        self.calls: list[tuple[str, list | None]] = []

    def call(self, method, params=None):
        self.calls.append((method, params))
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
    return rpc


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

    for invalid in ("not-an-int", 1.5, True, 0, -1):
        result = live_b4.run_live_b4({"wallet": WALLET, "limit": invalid})

        assert result.status == AnalysisStatus.INSUFFICIENT_DATA
        assert result.severity == Severity.UNKNOWN
        assert result.risk_score == 0
        assert result.missing_data == ["positive history limit"]


def test_b4_malformed_rpc_numeric_state_does_not_become_zero_balance(monkeypatch):
    for rpc in (
        FakeRpc(block="not-hex"),
        FakeRpc(block="100"),
        FakeRpc(block="0x00"),
        FakeRpc(block=100),
        FakeRpc(balance="1"),
        FakeRpc(balance="0x00"),
    ):
        install_rpc(monkeypatch, rpc)
        install_optional_none(monkeypatch)

        result = live_b4.run_live_b4({"wallet": WALLET})

        assert result.status == AnalysisStatus.PROVIDER_UNAVAILABLE
        assert result.severity == Severity.UNKNOWN
        assert result.risk_score == 0
        assert result.provider_status[0]["status"] == "MALFORMED_RESPONSE"
        assert "direct blockchain state" in result.missing_data


def test_b4_native_balance_is_pinned_to_captured_rpc_block(monkeypatch):
    rpc = install_rpc(monkeypatch)
    install_optional_none(monkeypatch)

    result = live_b4.run_live_b4({"wallet": WALLET})

    assert result.status == AnalysisStatus.PARTIAL
    assert ("eth_getBalance", [WALLET, "0x64"]) in rpc.calls
    assert not any(
        method == "eth_getBalance" and params and params[-1] == "latest"
        for method, params in rpc.calls
    )
    direct = next(item for item in result.evidence if item.source_type == "direct_state")
    assert direct.block_number == 100
    assert direct.normalized_value["block_tag"] == "0x64"
    assert result.data_freshness["status"] == FreshnessStatus.LIVE.value
    assert result.data_freshness["direct_state"] == FreshnessStatus.LIVE.value
    assert result.data_freshness["direct_state_block_number"] == 100
    assert result.data_freshness["indexed_history"] == "UNAVAILABLE"
    assert result.data_freshness["entity_labels"] == "UNAVAILABLE"
    assert any("pinned to captured RPC block 0x64" in text for text in result.assumptions)
    assert {item.calculation_version for item in result.evidence} == {
        "b4-live-1.1.0"
    }


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
    assert result.data_freshness["status"] == FreshnessStatus.LIVE.value
    assert result.data_freshness["entity_labels"] == "UNAVAILABLE"
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
    assert nansen_evidence[0].block_number is None
    assert result.metrics["entity_profile"]["identity"] == "UNKNOWN ADDRESS"
    assert result.data_confidence == 58
    assert result.engine_confidence == 55
    assert result.data_freshness["status"] == FreshnessStatus.UNKNOWN.value
    assert result.data_freshness["direct_state"] == FreshnessStatus.LIVE.value
    assert result.data_freshness["direct_state_block_number"] == 100
    assert result.data_freshness["entity_labels"] == FreshnessStatus.UNKNOWN.value


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
    assert nansen_evidence.block_number is None
    assert result.metrics["entity_profile"]["identity"] == "Example Exchange"
    assert result.data_confidence == 65
    assert result.engine_confidence == 62
    assert result.data_freshness["status"] == FreshnessStatus.UNKNOWN.value
    assert result.data_freshness["entity_labels"] == FreshnessStatus.UNKNOWN.value
    assert any("applies only to direct-state evidence" in text for text in result.assumptions)


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
    assert etherscan_evidence.block_number is None
    assert result.data_freshness["status"] == FreshnessStatus.UNKNOWN.value
    assert result.data_freshness["direct_state"] == FreshnessStatus.LIVE.value
    assert result.data_freshness["direct_state_block_number"] == 100
    assert result.data_freshness["indexed_history"] == FreshnessStatus.UNKNOWN.value
    assert result.data_freshness["entity_labels"] == "UNAVAILABLE"


def test_b4_non_object_indexer_rows_are_counted_as_malformed(monkeypatch):
    install_rpc(monkeypatch)

    class MixedHistoryEtherscan:
        configured = True

        def account_transactions(self, chain, address, *, offset):
            return ProviderCall(
                "etherscan",
                "txs-mixed",
                "https://etherscan.test",
                {
                    "result": [
                        {"from": WALLET, "to": OTHER, "value": "0"},
                        "not-an-object",
                        None,
                    ]
                },
                2.0,
            )

        def token_transactions(self, chain, address, *, offset):
            return ProviderCall(
                "etherscan",
                "tokens-empty",
                "https://etherscan.test",
                {"result": []},
                2.0,
            )

    monkeypatch.setattr(live_b4, "EtherscanClient", MixedHistoryEtherscan)
    monkeypatch.setattr(live_b4, "NansenClient", NoNansen)
    monkeypatch.setattr(live_b4, "ArkhamClient", NoArkham)

    result = live_b4.run_live_b4({"wallet": WALLET})

    assert result.metrics["activity"]["normalized_normal_transactions"] == 1
    assert result.metrics["activity"]["malformed_indexed_rows_skipped"] == 2
    evidence = next(item for item in result.evidence if item.provider == "etherscan")
    assert evidence.normalized_value["malformed_non_object_row_count"] == 2
