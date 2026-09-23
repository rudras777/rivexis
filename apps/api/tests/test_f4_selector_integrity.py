from __future__ import annotations

from time import time

from rivexis_api.models.enums import AnalysisStatus, FreshnessStatus, Severity
from rivexis_api.provider_clients import ProviderCall
from rivexis_api.services import live_f4


def install_rows(monkeypatch, rows):
    class FakeYieldClient:
        def pools(self):
            return ProviderCall(
                "defillama_yields",
                "yield-request",
                "https://yields.llama.fi/pools",
                {"data": rows},
                12.5,
            )

    monkeypatch.setattr(live_f4, "DefiLlamaYieldClient", FakeYieldClient)


def pool(pool_id: str, *, apy=8.0, tvl=10_000_000.0, timestamp=None):
    return {
        "pool": pool_id,
        "project": "aave-v3",
        "symbol": "USDC",
        "chain": "Ethereum",
        "apy": apy,
        "apyBase": 5.0,
        "apyReward": 3.0,
        "tvlUsd": tvl,
        "timestamp": time() if timestamp is None else timestamp,
        "sigma": 0.02,
        "il7d": 0.0,
        "apyMean30d": 7.5,
    }


def test_f4_ambiguous_broad_selector_fails_closed_instead_of_choosing_largest_tvl(monkeypatch):
    install_rows(
        monkeypatch,
        [
            pool("pool-small", tvl=2_000_000),
            pool("pool-large", tvl=200_000_000),
        ],
    )

    result = live_f4.run_live_f4(
        {"protocol": "aave", "asset": "USDC", "chain": "Ethereum"}
    )

    assert result.status == AnalysisStatus.INSUFFICIENT_DATA
    assert result.severity == Severity.UNKNOWN
    assert result.risk_score == 0
    assert result.engine_confidence == 0
    assert result.metrics["matching_pool_count"] == 2
    assert result.metrics["candidate_pool_ids"] == ["pool-small", "pool-large"]
    assert "did not silently choose" in result.summary
    assert "unique yield-pool selector" in result.missing_data


def test_f4_exact_pool_id_selects_only_requested_pool(monkeypatch):
    install_rows(
        monkeypatch,
        [
            pool("pool-small", apy=4.0, tvl=2_000_000),
            pool("pool-large", apy=14.0, tvl=200_000_000),
        ],
    )

    result = live_f4.run_live_f4({"pool_id": "pool-small"})

    assert result.status == AnalysisStatus.PARTIAL
    assert result.metrics["pool_id"] == "pool-small"
    assert result.metrics["headline_apy_pct"] == 4.0
    assert result.metrics["tvl_usd"] == 2_000_000


def test_f4_rejects_non_finite_core_provider_metrics_instead_of_substituting_zero(monkeypatch):
    install_rows(monkeypatch, [pool("bad-apy", apy=float("nan"))])
    bad_apy = live_f4.run_live_f4({"pool_id": "bad-apy"})

    assert bad_apy.status == AnalysisStatus.INSUFFICIENT_DATA
    assert bad_apy.severity == Severity.UNKNOWN
    assert bad_apy.risk_score == 0
    assert bad_apy.missing_data == ["finite apy"]

    install_rows(monkeypatch, [pool("bad-tvl", tvl=float("inf"))])
    bad_tvl = live_f4.run_live_f4({"pool_id": "bad-tvl"})

    assert bad_tvl.status == AnalysisStatus.INSUFFICIENT_DATA
    assert bad_tvl.risk_score == 0
    assert bad_tvl.missing_data == ["finite tvlUsd"]


def test_f4_stale_or_expired_yield_timestamp_promotes_status_to_stale_data(monkeypatch):
    install_rows(monkeypatch, [pool("stale-pool", timestamp=time() - 2 * 86400)])

    result = live_f4.run_live_f4({"pool_id": "stale-pool"})

    assert result.status == AnalysisStatus.STALE_DATA
    assert result.evidence[0].freshness == FreshnessStatus.EXPIRED
    assert result.data_freshness["status"] == "EXPIRED"
    assert any("stale" in warning.lower() for warning in result.warnings)


def test_f4_materially_future_timestamp_is_not_treated_as_current(monkeypatch):
    install_rows(monkeypatch, [pool("future-pool", timestamp=time() + 3600)])

    result = live_f4.run_live_f4({"pool_id": "future-pool"})

    assert result.status == AnalysisStatus.PARTIAL
    assert result.evidence[0].freshness == FreshnessStatus.UNKNOWN
    assert result.data_freshness["status"] == "UNKNOWN"
    assert result.data_confidence == 62
