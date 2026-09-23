from __future__ import annotations

from dataclasses import dataclass
from time import time

import pytest

from rivexis_api.models.enums import AnalysisStatus, FreshnessStatus, Severity
from rivexis_api.provider_clients import ProviderCall, ProviderError
from rivexis_api.services import live_f1


WALLET = "0x1111111111111111111111111111111111111111"
TOKEN = "0x2222222222222222222222222222222222222222"


class EthPrice:
    def __init__(self, *, price=1000.0, timestamp=None):
        self.price = price
        self.timestamp = int(time()) if timestamp is None else timestamp

    def simple_price(self, ids, vs_currency="usd"):
        assert ids == ["ethereum"]
        return ProviderCall(
            "coingecko",
            "price",
            "https://api.coingecko.com/api/v3/simple/price",
            {"ethereum": {"usd": self.price, "last_updated_at": self.timestamp}},
            2.0,
        )


@dataclass
class NativeRpc:
    native_result: object = "0xde0b6b3a7640000"  # 1 ETH
    block_result: object = "0x64"

    def __post_init__(self):
        self.calls: list[tuple[str, object]] = []

    def call(self, method, params=None):
        self.calls.append((method, params))
        if method == "eth_chainId":
            return ProviderCall("direct_rpc", "chain", "http://rpc.test", "0x1", 1.0)
        if method == "eth_blockNumber":
            return ProviderCall("direct_rpc", "block", "http://rpc.test", self.block_result, 1.0)
        if method == "eth_getBalance":
            return ProviderCall("direct_rpc", "native", "http://rpc.test", self.native_result, 1.0)
        raise AssertionError((method, params))


def _select(rpc):
    return "direct_rpc", rpc, rpc.call("eth_chainId"), []


@pytest.mark.parametrize("quantity", [-1, float("nan"), float("inf"), "nan", "inf"])
def test_f1_rejects_negative_or_non_finite_manual_quantities(quantity):
    result = live_f1.run_live_f1(
        {"manual_positions": [{"coingecko_id": "ethereum", "quantity": quantity}]}
    )

    assert result.status == AnalysisStatus.INSUFFICIENT_DATA
    assert result.risk_score == 0
    assert result.data_confidence == 0
    assert result.engine_confidence == 0
    assert result.severity == Severity.UNKNOWN


def test_f1_rejects_conflicting_duplicate_erc20_contract_metadata():
    result = live_f1.run_live_f1(
        {
            "wallet": WALLET,
            "erc20_tokens": [
                {"contract_address": TOKEN, "coingecko_id": "usd-coin", "decimals": 6},
                {"contract_address": TOKEN, "coingecko_id": "tether", "decimals": 6},
            ],
        }
    )

    assert result.status == AnalysisStatus.INSUFFICIENT_DATA
    assert result.risk_score == 0
    assert "conflicting" in result.summary.lower()


@pytest.mark.parametrize(
    ("block_result", "native_result"),
    [("not-a-quantity", "0x0"), ("0x64", "0xnothex"), ("0x64", -1)],
)
def test_f1_malformed_direct_chain_quantities_fail_closed(monkeypatch, block_result, native_result):
    rpc = NativeRpc(native_result=native_result, block_result=block_result)
    monkeypatch.setattr(live_f1, "select_rpc_client", lambda chain: _select(rpc))
    monkeypatch.setattr(live_f1, "CoinGeckoClient", EthPrice)

    result = live_f1.run_live_f1({"chain": "ethereum", "wallet": WALLET})

    assert result.status == AnalysisStatus.PROVIDER_UNAVAILABLE
    assert result.risk_score == 0
    assert result.severity == Severity.UNKNOWN
    assert "did not score an incomplete portfolio" in result.summary


def test_f1_duplicate_wallets_are_deduplicated_before_balance_and_valuation(monkeypatch):
    rpc = NativeRpc()
    monkeypatch.setattr(live_f1, "select_rpc_client", lambda chain: _select(rpc))
    monkeypatch.setattr(live_f1, "CoinGeckoClient", EthPrice)

    result = live_f1.run_live_f1(
        {"chain": "ethereum", "wallets": [WALLET, WALLET.upper().replace("0X", "0x")]}
    )

    assert result.status == AnalysisStatus.PARTIAL
    assert result.metrics["portfolio_value_usd"] == 1000.0
    assert result.metrics["positions"][0]["quantity"] == 1.0
    balance_calls = [call for call in rpc.calls if call[0] == "eth_getBalance"]
    assert len(balance_calls) == 1


class TokenReadFailureRpc(NativeRpc):
    def call(self, method, params=None):
        if method == "eth_call":
            raise ProviderError(
                "token call failed",
                provider_id="direct_rpc",
                code="RPC_-32000",
            )
        return super().call(method, params)


def test_f1_explicit_token_read_failure_cannot_fall_through_to_manual_only_score(monkeypatch):
    rpc = TokenReadFailureRpc(native_result="0x0")
    monkeypatch.setattr(live_f1, "select_rpc_client", lambda chain: _select(rpc))

    class ShouldNotPrice:
        def simple_price(self, ids, vs_currency="usd"):
            raise AssertionError("market pricing must not run after requested balance evidence fails")

    monkeypatch.setattr(live_f1, "CoinGeckoClient", ShouldNotPrice)
    result = live_f1.run_live_f1(
        {
            "chain": "ethereum",
            "wallet": WALLET,
            "manual_positions": [{"coingecko_id": "bitcoin", "quantity": 1}],
            "erc20_tokens": [
                {
                    "contract_address": TOKEN,
                    "coingecko_id": "usd-coin",
                    "decimals": 6,
                }
            ],
        }
    )

    assert result.status == AnalysisStatus.PROVIDER_UNAVAILABLE
    assert result.risk_score == 0
    assert result.engine_confidence == 0
    assert "complete explicitly requested wallet/token balance evidence" in result.missing_data


class TokenQuantityRpc(NativeRpc):
    def __init__(self, token_result):
        super().__init__(native_result="0x0")
        self.token_result = token_result

    def call(self, method, params=None):
        if method == "eth_call":
            return ProviderCall("direct_rpc", "token", "http://rpc.test", self.token_result, 1.0)
        return super().call(method, params)


@pytest.mark.parametrize("token_result", ["0xnothex", -1, None, True])
def test_f1_malformed_erc20_balance_cannot_become_zero_exposure(monkeypatch, token_result):
    rpc = TokenQuantityRpc(token_result)
    monkeypatch.setattr(live_f1, "select_rpc_client", lambda chain: _select(rpc))
    result = live_f1.run_live_f1(
        {
            "chain": "ethereum",
            "wallet": WALLET,
            "erc20_tokens": [
                {
                    "contract_address": TOKEN,
                    "coingecko_id": "usd-coin",
                    "decimals": 6,
                }
            ],
        }
    )

    assert result.status == AnalysisStatus.PROVIDER_UNAVAILABLE
    assert result.risk_score == 0
    assert result.severity == Severity.UNKNOWN


class TwoAssetPrices:
    def __init__(self, bitcoin_price=50_000.0, include_bitcoin=True, timestamp=None):
        self.bitcoin_price = bitcoin_price
        self.include_bitcoin = include_bitcoin
        self.timestamp = int(time()) if timestamp is None else timestamp

    def simple_price(self, ids, vs_currency="usd"):
        assert ids == ["bitcoin", "ethereum"]
        rows = {
            "ethereum": {"usd": 2_500.0, "last_updated_at": self.timestamp},
        }
        if self.include_bitcoin:
            rows["bitcoin"] = {"usd": self.bitcoin_price, "last_updated_at": self.timestamp}
        return ProviderCall(
            "coingecko",
            "price",
            "https://api.coingecko.com/api/v3/simple/price",
            rows,
            2.0,
        )


def _two_manual_positions():
    return {
        "manual_positions": [
            {"coingecko_id": "ethereum", "quantity": 1},
            {"coingecko_id": "bitcoin", "quantity": 1},
        ]
    }


def test_f1_missing_market_price_cannot_silently_remove_exposure_from_weights(monkeypatch):
    monkeypatch.setattr(
        live_f1,
        "CoinGeckoClient",
        lambda: TwoAssetPrices(include_bitcoin=False),
    )
    result = live_f1.run_live_f1(_two_manual_positions())

    assert result.status == AnalysisStatus.INSUFFICIENT_DATA
    assert result.risk_score == 0
    assert result.engine_confidence == 0
    assert result.severity == Severity.UNKNOWN
    assert any("bitcoin" in item for item in result.missing_data)
    assert any("did not silently exclude" in warning for warning in result.warnings)


@pytest.mark.parametrize("bad_price", [float("nan"), float("inf"), -1, 0, "nan"])
def test_f1_non_positive_or_non_finite_market_price_cannot_enter_scoring(monkeypatch, bad_price):
    monkeypatch.setattr(
        live_f1,
        "CoinGeckoClient",
        lambda: TwoAssetPrices(bitcoin_price=bad_price),
    )
    result = live_f1.run_live_f1(_two_manual_positions())

    assert result.status == AnalysisStatus.INSUFFICIENT_DATA
    assert result.risk_score == 0
    assert result.severity == Severity.UNKNOWN
    assert result.provider_status[-1]["status"] == "INCOMPLETE_RESPONSE"


@pytest.mark.parametrize("timestamp", [None, int(time()) + 3600])
def test_f1_incomplete_or_future_market_timestamp_is_unknown_not_current(monkeypatch, timestamp):
    class TimestampPrices:
        def simple_price(self, ids, vs_currency="usd"):
            assert ids == ["ethereum"]
            row = {"usd": 2500.0}
            if timestamp is not None:
                row["last_updated_at"] = timestamp
            return ProviderCall(
                "coingecko",
                "price",
                "https://api.coingecko.com/api/v3/simple/price",
                {"ethereum": row},
                2.0,
            )

    monkeypatch.setattr(live_f1, "CoinGeckoClient", TimestampPrices)
    result = live_f1.run_live_f1(
        {"manual_positions": [{"coingecko_id": "ethereum", "quantity": 1}]}
    )

    assert result.status == AnalysisStatus.PARTIAL
    assert result.data_freshness["status"] == FreshnessStatus.UNKNOWN.value
    assert result.data_confidence == 60
    assert result.evidence[-1].freshness == FreshnessStatus.UNKNOWN
    assert any("freshness is UNKNOWN" in warning for warning in result.warnings)
    assert any("retrieval time is not treated" in assumption for assumption in result.assumptions)
