from __future__ import annotations

from rivexis_api.models.enums import AnalysisStatus
from rivexis_api.provider_clients import ProviderCall
from rivexis_api.services import live_b4

WALLET = "0x1111111111111111111111111111111111111111"
OTHER = "0x2222222222222222222222222222222222222222"
OTHER2 = "0x3333333333333333333333333333333333333333"
TOKEN_A = "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
TOKEN_B = "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"


class FakeRpc:
    def call(self, method, params=None):
        if method == "eth_blockNumber":
            return ProviderCall("direct_rpc", "block", "http://rpc.test", "0x64", 1.0)
        if method == "eth_getBalance":
            return ProviderCall("direct_rpc", "balance", "http://rpc.test", "0x0", 1.0)
        raise AssertionError((method, params))


class NoNansen:
    configured = False


class NoArkham:
    configured = False
    credentialed = False
    license_approved = False


def install(monkeypatch, etherscan_cls):
    rpc = FakeRpc()
    monkeypatch.setattr(
        live_b4,
        "select_rpc_client",
        lambda chain: (
            "direct_rpc",
            rpc,
            ProviderCall("direct_rpc", "probe", "http://rpc.test", "0x1", 1.0),
            [],
        ),
    )
    monkeypatch.setattr(live_b4, "EtherscanClient", etherscan_cls)
    monkeypatch.setattr(live_b4, "NansenClient", NoNansen)
    monkeypatch.setattr(live_b4, "ArkhamClient", NoArkham)


def history_client(*, normal_rows=None, token_rows=None):
    normal_rows = normal_rows or []
    token_rows = token_rows or []

    class HistoryEtherscan:
        configured = True

        def account_transactions(self, chain, address, *, offset):
            return ProviderCall(
                "etherscan",
                "txs",
                "https://etherscan.test",
                {"result": normal_rows},
                2.0,
            )

        def token_transactions(self, chain, address, *, offset):
            return ProviderCall(
                "etherscan",
                "tokens",
                "https://etherscan.test",
                {"result": token_rows},
                2.0,
            )

    return HistoryEtherscan


def token_row(*, contract, frm, to, value, decimals=6, symbol="USD"):
    return {
        "contractAddress": contract,
        "from": frm,
        "to": to,
        "value": str(value),
        "tokenDecimal": str(decimals),
        "tokenSymbol": symbol,
    }


def test_same_symbol_different_contracts_remain_separate_assets(monkeypatch):
    install(
        monkeypatch,
        history_client(
            token_rows=[
                token_row(contract=TOKEN_A, frm=WALLET, to=OTHER, value=1_000_000, symbol="USD"),
                token_row(contract=TOKEN_B, frm=OTHER2, to=WALLET, value=2_000_000, symbol="USD"),
            ]
        ),
    )

    result = live_b4.run_live_b4({"wallet": WALLET})

    assert result.status == AnalysisStatus.PARTIAL
    flows = {row["contract"]: row for row in result.metrics["token_flows"]}
    assert set(flows) == {TOKEN_A, TOKEN_B}
    assert flows[TOKEN_A]["symbol"] == "USD"
    assert flows[TOKEN_A]["out"] == 1.0
    assert flows[TOKEN_A]["in"] == 0.0
    assert flows[TOKEN_B]["in"] == 2.0
    assert flows[TOKEN_B]["out"] == 0.0
    assert result.metrics["activity"]["normalized_erc20_transfers"] == 2


def test_conflicting_decimals_for_same_contract_are_skipped(monkeypatch):
    install(
        monkeypatch,
        history_client(
            token_rows=[
                token_row(contract=TOKEN_A, frm=WALLET, to=OTHER, value=1_000_000, decimals=6, symbol="USDC"),
                token_row(contract=TOKEN_A, frm=OTHER, to=WALLET, value=10**18, decimals=18, symbol="USDC"),
            ]
        ),
    )

    result = live_b4.run_live_b4({"wallet": WALLET})

    assert result.metrics["activity"]["normalized_erc20_transfers"] == 1
    assert result.metrics["activity"]["token_metadata_conflicts_skipped"] == 1
    assert result.metrics["activity"]["malformed_indexed_rows_skipped"] == 1
    flow = result.metrics["token_flows"][0]
    assert flow["contract"] == TOKEN_A
    assert flow["decimals"] == 6
    assert flow["out"] == 1.0
    assert flow["in"] == 0.0
    assert any("decimals conflicted" in warning for warning in result.warnings)
    assert "consistent indexed ERC-20 metadata for every transfer" in result.missing_data


def test_malformed_rows_do_not_inflate_activity_risk_threshold(monkeypatch):
    malformed = [
        {"from": WALLET, "to": OTHER, "value": "not-a-number"}
        for _ in range(200)
    ]
    valid = [{"from": WALLET, "to": OTHER, "value": "0"}]
    install(monkeypatch, history_client(normal_rows=malformed + valid))

    result = live_b4.run_live_b4({"wallet": WALLET, "limit": 250})

    assert result.metrics["activity"]["indexed_normal_transactions"] == 201
    assert result.metrics["activity"]["normalized_normal_transactions"] == 1
    assert result.metrics["activity"]["normalized_activity_records"] == 1
    assert result.metrics["activity"]["malformed_indexed_rows_skipped"] == 200
    # B4's activity surcharge starts only at 150 VALID normalized records.
    assert result.risk_score == 10.0


def test_counterparty_flow_direction_assets_and_concentration_are_descriptive(monkeypatch):
    install(
        monkeypatch,
        history_client(
            normal_rows=[
                {"from": WALLET, "to": OTHER, "value": str(2 * 10**18)},
                {"from": OTHER, "to": WALLET, "value": str(10**18)},
                {"from": WALLET, "to": OTHER2, "value": "0"},
            ],
            token_rows=[
                token_row(contract=TOKEN_A, frm=WALLET, to=OTHER, value=3_000_000, symbol="USDC"),
                token_row(contract=TOKEN_B, frm=OTHER2, to=WALLET, value=4_000_000, symbol="USDT"),
            ],
        ),
    )

    result = live_b4.run_live_b4({"wallet": WALLET})

    rows = {row["address"]: row for row in result.metrics["top_counterparties"]}
    assert rows[OTHER]["interaction_count"] == 3
    assert rows[OTHER]["inbound_record_count"] == 1
    assert rows[OTHER]["outbound_record_count"] == 2
    assert rows[OTHER]["native_in"] == 1.0
    assert rows[OTHER]["native_out"] == 2.0
    assert rows[OTHER]["native_net"] == -1.0
    assert rows[OTHER]["token_assets"][0]["contract"] == TOKEN_A
    assert rows[OTHER]["token_assets"][0]["out"] == 3.0

    assert rows[OTHER2]["interaction_count"] == 2
    assert rows[OTHER2]["inbound_record_count"] == 1
    assert rows[OTHER2]["outbound_record_count"] == 1

    concentration = result.metrics["counterparty_concentration"]
    assert concentration["unique_counterparties"] == 2
    assert concentration["indexed_records_with_counterparty"] == 5
    assert concentration["top_counterparty_share_pct"] == 60.0
    assert concentration["top3_share_pct"] == 100.0
    assert concentration["interaction_hhi"] == 5200.0
    assert concentration["risk_interpretation"] == "descriptive_only_not_scored"
    assert result.risk_score == 10.0


def test_self_transfers_are_not_outbound_flow_or_self_counterparty(monkeypatch):
    install(
        monkeypatch,
        history_client(
            normal_rows=[
                {"from": WALLET, "to": WALLET, "value": str(3 * 10**18)}
            ],
            token_rows=[
                token_row(
                    contract=TOKEN_A,
                    frm=WALLET,
                    to=WALLET,
                    value=5_000_000,
                    symbol="USDC",
                )
            ],
        ),
    )

    result = live_b4.run_live_b4({"wallet": WALLET})

    activity = result.metrics["activity"]
    assert activity["normalized_activity_records"] == 2
    assert activity["self_normal_transactions"] == 1
    assert activity["self_erc20_transfers"] == 1
    assert activity["native_in"] == 0
    assert activity["native_out"] == 0
    assert activity["native_net"] == 0
    assert result.metrics["top_counterparties"] == []
    assert result.metrics["counterparty_concentration"]["unique_counterparties"] == 0
    token = result.metrics["token_flows"][0]
    assert token["count"] == 1
    assert token["in"] == 0
    assert token["out"] == 0
    assert token["net"] == 0
