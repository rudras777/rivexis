from __future__ import annotations

from time import time

from rivexis_api.models.enums import AnalysisStatus, FreshnessStatus, Severity
from rivexis_api.provider_clients import ProviderCall
from rivexis_api.services import live_f2


def install_result(monkeypatch, result):
    class FakeDefiLlama:
        def protocol(self, slug):
            return ProviderCall(
                "defillama",
                "f2-request",
                f"https://api.llama.fi/protocol/{slug}",
                result,
                7.5,
            )

    monkeypatch.setattr(live_f2, "DefiLlamaClient", FakeDefiLlama)


def valid_record(*, tvl=100_000_000.0, observed_at=None, latest_fetch_ok=True):
    return {
        "name": "Aave",
        "category": "Lending",
        "chains": ["Ethereum", "Base"],
        "audits": "2",
        "audit_links": [
            "https://example.com/audit-a.pdf",
            "https://example.com/audit-b.pdf",
        ],
        "latestFetchIsOk": latest_fetch_ok,
        "tvl": [
            {
                "date": int(time()) if observed_at is None else observed_at,
                "totalLiquidityUSD": tvl,
            }
        ],
    }


def test_f2_rejects_non_object_or_identityless_provider_record(monkeypatch):
    install_result(monkeypatch, [])
    non_object = live_f2.run_live_f2({"protocol": "aave"})
    assert non_object.status == AnalysisStatus.INSUFFICIENT_DATA
    assert non_object.severity == Severity.UNKNOWN
    assert non_object.risk_score == 0
    assert "non-object" in non_object.summary

    install_result(monkeypatch, {"tvl": 100_000_000})
    no_identity = live_f2.run_live_f2({"protocol": "aave"})
    assert no_identity.status == AnalysisStatus.INSUFFICIENT_DATA
    assert no_identity.risk_score == 0
    assert "protocol identity" in no_identity.summary

    install_result(monkeypatch, {"name": {"unexpected": "object"}, "tvl": 100_000_000})
    non_string_identity = live_f2.run_live_f2({"protocol": "aave"})
    assert non_string_identity.status == AnalysisStatus.INSUFFICIENT_DATA
    assert non_string_identity.risk_score == 0


def test_f2_rejects_truthy_string_provider_health_flag(monkeypatch):
    install_result(monkeypatch, valid_record(latest_fetch_ok="false"))
    result = live_f2.run_live_f2({"protocol": "aave"})

    assert result.status == AnalysisStatus.INSUFFICIENT_DATA
    assert result.severity == Severity.UNKNOWN
    assert result.risk_score == 0
    assert result.missing_data == ["boolean latestFetchIsOk metadata"]
    assert "truthiness" in result.summary


def test_f2_rejects_non_finite_or_negative_core_tvl(monkeypatch):
    install_result(monkeypatch, valid_record(tvl=float("nan")))
    non_finite = live_f2.run_live_f2({"protocol": "aave"})
    assert non_finite.status == AnalysisStatus.INSUFFICIENT_DATA
    assert non_finite.severity == Severity.UNKNOWN
    assert non_finite.risk_score == 0
    assert non_finite.missing_data == ["finite non-negative protocol TVL"]

    install_result(monkeypatch, valid_record(tvl=-1))
    negative = live_f2.run_live_f2({"protocol": "aave"})
    assert negative.status == AnalysisStatus.INSUFFICIENT_DATA
    assert negative.risk_score == 0


def test_f2_uses_actual_tvl_timestamp_for_freshness(monkeypatch):
    install_result(monkeypatch, valid_record(observed_at=int(time()) - 10 * 86400))
    result = live_f2.run_live_f2({"protocol": "aave"})

    assert result.status == AnalysisStatus.STALE_DATA
    assert result.evidence[0].freshness == FreshnessStatus.EXPIRED
    assert result.data_freshness["status"] == "EXPIRED"
    assert result.data_freshness["provider_observation_timestamp_present"] is True
    assert any("stale" in warning.lower() for warning in result.warnings)


def test_f2_does_not_claim_current_when_provider_observation_time_is_unusable(monkeypatch):
    install_result(monkeypatch, valid_record(observed_at=1))
    result = live_f2.run_live_f2({"protocol": "aave"})

    assert result.status == AnalysisStatus.PARTIAL
    assert result.evidence[0].freshness == FreshnessStatus.UNKNOWN
    assert result.data_freshness["status"] == "UNKNOWN"
    assert result.data_freshness["provider_observation_timestamp_present"] is False
    assert result.data_confidence == 62
    assert any("retrieval time is not treated" in assumption for assumption in result.assumptions)


def test_f2_provider_latest_fetch_failure_is_stale_gate_even_with_recent_tvl(monkeypatch):
    install_result(monkeypatch, valid_record(latest_fetch_ok=False))
    result = live_f2.run_live_f2({"protocol": "aave"})

    assert result.status == AnalysisStatus.STALE_DATA
    assert result.data_freshness["latest_fetch_ok"] is False
    assert result.data_freshness["status"] == "STALE"
    assert result.data_confidence <= 50
    assert result.provider_status[0]["status"] == "DEGRADED"
    assert any("latest protocol fetch is not healthy" in warning for warning in result.warnings)


def test_f2_malformed_audit_metadata_cannot_reduce_risk(monkeypatch):
    record = valid_record()
    record["audits"] = True
    install_result(monkeypatch, record)

    result = live_f2.run_live_f2({"protocol": "aave"})

    assert result.status == AnalysisStatus.PARTIAL
    assert result.risk_score == 35
    assert result.severity == Severity.MODERATE
    assert result.metrics["audit_count"] == 0
    assert result.metrics["audit_links_count"] == 2
    assert result.metrics["audit_declared_count"] is None
    assert result.metrics["audit_metadata_usable_for_scoring"] is False
    assert result.metrics["audit_metadata_issues"] == ["AUDITS_COUNT_BOOLEAN"]
    assert any("ignored it for risk scoring" in warning for warning in result.warnings)
    assert any("No validated provider-supplied HTTPS audit reference" in warning for warning in result.warnings)


def test_f2_declared_audits_without_usable_references_do_not_count(monkeypatch):
    record = valid_record()
    record["audit_links"] = []
    install_result(monkeypatch, record)

    result = live_f2.run_live_f2({"protocol": "aave"})

    assert result.status == AnalysisStatus.PARTIAL
    assert result.risk_score == 35
    assert result.metrics["audit_count"] == 0
    assert result.metrics["audit_links_count"] == 0
    assert result.metrics["audit_declared_count"] == 2
    assert result.metrics["audit_metadata_usable_for_scoring"] is False
    assert result.metrics["audit_metadata_issues"] == []
    assert any("declared audits without usable HTTPS audit references" in warning for warning in result.warnings)


def test_f2_invalid_or_contradictory_audit_links_fail_closed(monkeypatch):
    record = valid_record()
    record["audits"] = "1"
    record["audit_links"] = [
        "https://example.com/audit-a.pdf",
        "https://example.com/audit-b.pdf",
        "http://example.com/insecure-audit.pdf",
    ]
    install_result(monkeypatch, record)

    result = live_f2.run_live_f2({"protocol": "aave"})

    assert result.risk_score == 35
    assert result.metrics["audit_count"] == 0
    assert result.metrics["audit_links_count"] == 2
    assert result.metrics["audit_metadata_usable_for_scoring"] is False
    assert result.metrics["audit_metadata_issues"] == [
        "AUDIT_COUNT_LINK_CONFLICT",
        "AUDIT_LINK_INVALID_URL",
    ]


def test_f2_recent_valid_record_remains_partial_screening(monkeypatch):
    install_result(monkeypatch, valid_record())
    result = live_f2.run_live_f2({"protocol": "aave"})

    assert result.status == AnalysisStatus.PARTIAL
    assert result.metrics["name"] == "Aave"
    assert result.metrics["tvl_usd"] == 100_000_000.0
    assert result.metrics["audit_count"] == 2
    assert result.metrics["audit_links_count"] == 2
    assert result.metrics["audit_declared_count"] == 2
    assert result.metrics["audit_metadata_usable_for_scoring"] is True
    assert result.metrics["audit_metadata_issues"] == []
    assert result.risk_score == 20
    assert result.evidence[0].freshness == FreshnessStatus.CURRENT
    assert result.data_freshness["status"] == "CURRENT"
    assert result.provider_consensus == "SINGLE_SOURCE"
    assert any("not independent proof" in assumption for assumption in result.assumptions)


def test_f2_boolean_tvl_is_malformed_not_numeric_provider_evidence(monkeypatch):
    for boolean_tvl in (True, False):
        install_result(monkeypatch, valid_record(tvl=boolean_tvl))
        result = live_f2.run_live_f2({"protocol": "aave"})

        assert result.status == AnalysisStatus.INSUFFICIENT_DATA
        assert result.severity == Severity.UNKNOWN
        assert result.risk_score == 0
        assert result.missing_data == ["finite non-negative protocol TVL"]
        assert result.provider_status[0]["status"] == "MALFORMED_PROTOCOL_RECORD"


def test_f2_boolean_tvl_timestamp_stays_unknown(monkeypatch):
    install_result(monkeypatch, valid_record(observed_at=True))
    result = live_f2.run_live_f2({"protocol": "aave"})

    assert result.status == AnalysisStatus.PARTIAL
    assert result.evidence[0].freshness == FreshnessStatus.UNKNOWN
    assert result.data_freshness["status"] == "UNKNOWN"
    assert result.data_freshness["provider_observation_timestamp_present"] is False
    assert result.data_freshness["age_seconds"] is None
    assert result.data_confidence == 62


def test_f2_boolean_current_chain_tvl_is_malformed(monkeypatch):
    record = {
        "name": "Aave",
        "category": "Lending",
        "chains": ["Ethereum"],
        "audits": "1",
        "audit_links": ["https://example.com/audit.pdf"],
        "latestFetchIsOk": True,
        "currentChainTvls": {"Ethereum": True},
    }
    install_result(monkeypatch, record)

    result = live_f2.run_live_f2({"protocol": "aave"})

    assert result.status == AnalysisStatus.INSUFFICIENT_DATA
    assert result.severity == Severity.UNKNOWN
    assert result.risk_score == 0
    assert result.missing_data == ["finite non-negative protocol TVL"]
