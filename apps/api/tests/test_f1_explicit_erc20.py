from __future__ import annotations

from time import time

from rivexis_api.engines import ENGINES
from rivexis_api.models.enums import AnalysisStatus, EngineId
from rivexis_api.provider_clients import ProviderCall
from rivexis_api.services import live_f1


class PortfolioRpc:
    def __init__(self, token_balance: int = 1_500_000, token_decimals: int = 6):
        self.token_balance = token_balance
        self.token_decimals = token_decimals
        self.balance_calls: list[tuple[str, list | None]] = []

    @staticmethod
    def _word(value: int) -> str:
        return "0x" + format(value, "064x")

    def call(self, method, params=None):
        self.balance_calls.append((method, params))
        if method == "eth_chainId":
            return ProviderCall("direct_rpc", "chain", "http://rpc.test", "0x1", 1.0)
        if method == "eth_blockNumber":
            return ProviderCall("direct_rpc", "block", "http://rpc.test", "0x64", 1.0)
        if method == "eth_getBalance":
            return ProviderCall("direct_rpc", "native", "http://rpc.test", "0x0", 1.0)
        if method == "eth_call":
            data = params[0]["data"]
            if data == live_f1.DECIMALS_SELECTOR:
                return ProviderCall(
                    "direct_rpc",
                    "token-decimals",
                    "http://rpc.test",
                    self._word(self.token_decimals),
                    1.0,
                )
            return ProviderCall(
                "direct_rpc",
                "token-balance",
                "http://rpc.test",
                self._word(self.token_balance),
                1.0,
            )
        raise AssertionError((method, params))


def _select(rpc: PortfolioRpc):
    return "direct_rpc", rpc, rpc.call("eth_chainId"), []


class StablecoinPrices:
    def simple_price(self, ids, vs_currency="usd"):
        assert ids == ["usd-coin"]
        return ProviderCall(
            "coingecko",
            "price",
            "https://api.coingecko.com/api/v3/simple/price",
            {
                "usd-coin": {
                    "usd": 1.0,
                    "last_updated_at": int(time()),
                    "usd_24h_change": 0.0,
                }
            },
            2.0,
        )


def test_f1_reads_explicit_erc20_balance_from_rpc_without_claiming_wallet_discovery(monkeypatch):
    rpc = PortfolioRpc(token_balance=1_500_000)
    monkeypatch.setattr(live_f1, "select_rpc_client", lambda chain: _select(rpc))
    monkeypatch.setattr(live_f1, "CoinGeckoClient", StablecoinPrices)

    wallet = "0x1111111111111111111111111111111111111111"
    token = "0x2222222222222222222222222222222222222222"
    result = live_f1.run_live_f1(
        {
            "chain": "ethereum",
            "wallet": wallet,
            "erc20_tokens": [
                {
                    "contract_address": token,
                    "coingecko_id": "usd-coin",
                    "symbol": "USDC",
                    "decimals": 6,
                }
            ],
        }
    )

    assert result.status == AnalysisStatus.PARTIAL
    assert result.engine_version == "1.2.0"
    assert result.block_reference == 100
    assert result.metrics["portfolio_value_usd"] == 1.5
    assert result.metrics["positions"] == [
        {
            "id": "usd-coin",
            "label": "USDC",
            "quantity": 1.5,
            "sources": ["wallet-erc20-balance"],
            "price_usd": 1.0,
            "value_usd": 1.5,
            "weight_pct": 100.0,
        }
    ]

    metadata_evidence = [e for e in result.evidence if e.source_type == "direct_token_metadata"]
    assert len(metadata_evidence) == 1
    assert metadata_evidence[0].normalized_value["token_contract"] == token
    assert metadata_evidence[0].normalized_value["caller_supplied_decimals"] == 6
    assert metadata_evidence[0].normalized_value["onchain_decimals"] == 6
    assert metadata_evidence[0].normalized_value["block_tag"] == "0x64"
    assert metadata_evidence[0].block_number == 100

    token_evidence = [e for e in result.evidence if e.source_type == "direct_token_balance"]
    assert len(token_evidence) == 1
    assert token_evidence[0].normalized_value["token_contract"] == token
    assert token_evidence[0].normalized_value["raw_balance"] == 1_500_000
    assert token_evidence[0].normalized_value["quantity"] == 1.5
    assert token_evidence[0].normalized_value["block_tag"] == "0x64"
    assert token_evidence[0].block_number == 100

    native_calls = [params for method, params in rpc.balance_calls if method == "eth_getBalance"]
    eth_calls = [params for method, params in rpc.balance_calls if method == "eth_call"]
    assert native_calls == [[wallet, "0x64"]]
    assert eth_calls[0] == [{"to": token, "data": live_f1.DECIMALS_SELECTOR}, "0x64"]
    assert eth_calls[1][0]["to"] == token
    assert eth_calls[1][0]["data"] == live_f1.BALANCE_OF_SELECTOR + ("0" * 24) + wallet[2:]
    assert eth_calls[1][1] == "0x64"
    assert all(
        params[-1] != "latest"
        for method, params in rpc.balance_calls
        if method in {"eth_getBalance", "eth_call"}
    )
    assert "automatic ERC-20 token discovery outside explicitly supplied contracts" in result.missing_data
    assert "NFT positions for wallet ingestion" in result.missing_data
    assert "DeFi protocol positions for wallet ingestion" in result.missing_data
    assert any("decimals are verified directly" in text for text in result.assumptions)
    assert any("pinned to captured RPC block 0x64" in text for text in result.assumptions)


def test_f1_rejects_caller_decimals_that_disagree_with_contract(monkeypatch):
    rpc = PortfolioRpc(token_balance=1_500_000, token_decimals=18)
    monkeypatch.setattr(live_f1, "select_rpc_client", lambda chain: _select(rpc))

    class ShouldNotPrice:
        def simple_price(self, ids, vs_currency="usd"):
            raise AssertionError("market pricing must not run after token metadata mismatch")

    monkeypatch.setattr(live_f1, "CoinGeckoClient", ShouldNotPrice)
    result = live_f1.run_live_f1(
        {
            "chain": "ethereum",
            "wallet": "0x1111111111111111111111111111111111111111",
            "erc20_tokens": [
                {
                    "contract_address": "0x2222222222222222222222222222222222222222",
                    "coingecko_id": "usd-coin",
                    "symbol": "USDC",
                    "decimals": 6,
                }
            ],
        }
    )

    assert result.status == AnalysisStatus.PROVIDER_UNAVAILABLE
    assert result.risk_score == 0
    assert result.engine_confidence == 0
    assert result.provider_status[-1]["status"] == "TOKEN_METADATA_MISMATCH"
    assert any("do not match on-chain decimals 18" in warning for warning in result.warnings)


def test_f1_aggregates_duplicate_asset_rows_before_concentration_scoring(monkeypatch):
    class TwoAssetPrices:
        def simple_price(self, ids, vs_currency="usd"):
            assert ids == ["bitcoin", "ethereum"]
            now = int(time())
            return ProviderCall(
                "coingecko",
                "price",
                "https://api.coingecko.com/api/v3/simple/price",
                {
                    "ethereum": {"usd": 100.0, "last_updated_at": now},
                    "bitcoin": {"usd": 100.0, "last_updated_at": now},
                },
                2.0,
            )

    monkeypatch.setattr(live_f1, "CoinGeckoClient", TwoAssetPrices)
    result = live_f1.run_live_f1(
        {
            "manual_positions": [
                {"coingecko_id": "ethereum", "symbol": "ETH", "quantity": 1},
                {"coingecko_id": "ethereum", "symbol": "ETH", "quantity": 1},
                {"coingecko_id": "bitcoin", "symbol": "BTC", "quantity": 2},
            ]
        }
    )

    assert result.status == AnalysisStatus.PARTIAL
    assert len(result.metrics["positions"]) == 2
    eth = next(row for row in result.metrics["positions"] if row["id"] == "ethereum")
    btc = next(row for row in result.metrics["positions"] if row["id"] == "bitcoin")
    assert eth["quantity"] == 2.0
    assert btc["quantity"] == 2.0
    assert eth["weight_pct"] == 50.0
    assert btc["weight_pct"] == 50.0
    assert result.metrics["largest_exposure_pct"] == 50.0
    assert result.metrics["concentration_hhi"] == 0.5


def test_f1_dispatch_preserves_new_contract_version_and_evidence_version(monkeypatch):
    rpc = PortfolioRpc(token_balance=2_000_000)
    monkeypatch.setattr(live_f1, "select_rpc_client", lambda chain: _select(rpc))
    monkeypatch.setattr(live_f1, "CoinGeckoClient", StablecoinPrices)

    result = ENGINES[EngineId.F1](
        {
            "chain": "ethereum",
            "wallet": "0x1111111111111111111111111111111111111111",
            "erc20_tokens": [
                {
                    "contract_address": "0x2222222222222222222222222222222222222222",
                    "coingecko_id": "usd-coin",
                    "symbol": "USDC",
                    "decimals": 6,
                }
            ],
        },
        False,
    )

    assert result.engine_version == "1.2.0"
    assert {e.engine_version for e in result.evidence} == {"1.2.0"}
    assert any(e.calculation_version == "f1-live-1.4.0" for e in result.evidence)
