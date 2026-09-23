from __future__ import annotations

from datetime import datetime, timezone
from time import time

from rivexis_api.models.enums import AnalysisStatus, Severity
from rivexis_api.provider_clients import ProviderCall
from rivexis_api.services import live_f5


def fail_provider():
    raise AssertionError("market provider must not be called for invalid F5 input")


def test_f5_rejects_negative_weight_before_market_provider(monkeypatch):
    monkeypatch.setattr(live_f5, "CoinGeckoClient", fail_provider)
    result = live_f5.run_live_f5(
        {
            "allocations": [
                {"coingecko_id": "bitcoin", "weight_pct": -10, "stablecoin": False},
                {"coingecko_id": "ethereum", "weight_pct": 110, "stablecoin": False},
            ]
        }
    )

    assert result.status == AnalysisStatus.INSUFFICIENT_DATA
    assert result.severity == Severity.UNKNOWN
    assert result.risk_score == 0
    assert "cannot be negative" in result.summary


def test_f5_rejects_negative_or_non_finite_quantities_and_capital(monkeypatch):
    monkeypatch.setattr(live_f5, "CoinGeckoClient", fail_provider)

    negative = live_f5.run_live_f5(
        {"allocations": [{"quantity": -1, "weight_pct": 100, "stablecoin": False}]}
    )
    assert negative.status == AnalysisStatus.INSUFFICIENT_DATA
    assert "quantity cannot be negative" in negative.summary

    non_finite = live_f5.run_live_f5(
        {"allocations": [{"weight_pct": float("inf"), "stablecoin": False}]}
    )
    assert non_finite.status == AnalysisStatus.INSUFFICIENT_DATA
    assert "finite number" in non_finite.summary

    bad_capital = live_f5.run_live_f5(
        {
            "capital_usd": -100,
            "allocations": [{"weight_pct": 100, "stablecoin": False}],
        }
    )
    assert bad_capital.status == AnalysisStatus.INSUFFICIENT_DATA
    assert "capital_usd" in bad_capital.summary


def test_f5_requires_real_boolean_stablecoin_flag_before_provider(monkeypatch):
    monkeypatch.setattr(live_f5, "CoinGeckoClient", fail_provider)
    result = live_f5.run_live_f5(
        {
            "allocations": [
                {"coingecko_id": "usd-coin", "weight_pct": 100, "stablecoin": "false"}
            ]
        }
    )

    assert result.status == AnalysisStatus.INSUFFICIENT_DATA
    assert result.severity == Severity.UNKNOWN
    assert "JSON boolean" in result.summary


def test_f5_does_not_silently_zero_unpriced_allocation_when_deriving_weights(monkeypatch):
    class PartialPrices:
        def simple_price(self, ids, vs_currency="usd"):
            assert ids == ["bitcoin", "ethereum"]
            return ProviderCall(
                "coingecko",
                "partial-price",
                "https://api.coingecko.com/api/v3/simple/price",
                {
                    "bitcoin": {
                        "usd": 80000,
                        "last_updated_at": int(time()),
                    }
                },
                2.0,
            )

    monkeypatch.setattr(live_f5, "CoinGeckoClient", PartialPrices)
    result = live_f5.run_live_f5(
        {
            "allocations": [
                {"coingecko_id": "bitcoin", "quantity": 1, "stablecoin": False},
                {"coingecko_id": "ethereum", "quantity": 10, "stablecoin": False},
            ]
        }
    )

    assert result.status == AnalysisStatus.INSUFFICIENT_DATA
    assert result.severity == Severity.UNKNOWN
    assert result.risk_score == 0
    assert "cannot be derived" in result.summary
    assert any("did not silently assign a zero weight" in warning for warning in result.warnings)
    assert any("ETH" in item or "ethereum" in item for item in result.missing_data)


def test_f5_stale_market_reference_promotes_analysis_to_stale_data(monkeypatch):
    stale_timestamp = int(datetime(2020, 1, 1, tzinfo=timezone.utc).timestamp())

    class StalePrices:
        def simple_price(self, ids, vs_currency="usd"):
            return ProviderCall(
                "coingecko",
                "stale-price",
                "https://api.coingecko.com/api/v3/simple/price",
                {
                    "bitcoin": {
                        "usd": 80000,
                        "last_updated_at": stale_timestamp,
                    }
                },
                2.0,
            )

    monkeypatch.setattr(live_f5, "CoinGeckoClient", StalePrices)
    result = live_f5.run_live_f5(
        {
            "allocations": [
                {"coingecko_id": "bitcoin", "weight_pct": 100, "stablecoin": False}
            ]
        }
    )

    assert result.status == AnalysisStatus.STALE_DATA
    assert result.data_freshness["status"] == "EXPIRED"
    assert any("stale" in warning.lower() for warning in result.warnings)


def test_f5_valid_explicit_weights_remain_normalized_and_partial(monkeypatch):
    class CurrentPrices:
        def simple_price(self, ids, vs_currency="usd"):
            now = int(time())
            return ProviderCall(
                "coingecko",
                "current-price",
                "https://api.coingecko.com/api/v3/simple/price",
                {
                    "bitcoin": {"usd": 80000, "last_updated_at": now},
                    "usd-coin": {"usd": 1, "last_updated_at": now},
                },
                2.0,
            )

    monkeypatch.setattr(live_f5, "CoinGeckoClient", CurrentPrices)
    result = live_f5.run_live_f5(
        {
            "capital_usd": 100000,
            "allocations": [
                {"coingecko_id": "bitcoin", "weight_pct": 40, "stablecoin": False},
                {"coingecko_id": "usd-coin", "weight_pct": 60, "stablecoin": True},
            ],
        }
    )

    assert result.status == AnalysisStatus.PARTIAL
    assert result.metrics["stablecoin_weight_pct"] == 60.0
    assert result.metrics["largest_allocation_pct"] == 60.0
    assert sum(row["weight_pct"] for row in result.metrics["allocations"]) == 100.0
