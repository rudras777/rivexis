from __future__ import annotations

from datetime import datetime, timezone

from rivexis_api.models.enums import AnalysisStatus, FreshnessStatus, Severity
from rivexis_api.provider_clients import ProviderCall
from rivexis_api.providers import Resolution
from rivexis_api.services import live_b3

ENTITY = "0x1111111111111111111111111111111111111111"
TOKEN = "0x2222222222222222222222222222222222222222"
ORACLE = "0x3333333333333333333333333333333333333333"


def word(value: int) -> str:
    return f"{value & ((1 << 256) - 1):064x}"


class SnapshotRpc:
    def __init__(
        self,
        *,
        block="0x64",
        balance="0x10",
        code="0x60016000",
        total_supply="0x64",
        oracle_updated_at: int | None = None,
        oracle_answer: int = 2_000_00000000,
    ):
        self.block = block
        self.balance = balance
        self.code = code
        self.total_supply = total_supply
        self.oracle_updated_at = oracle_updated_at
        self.oracle_answer = oracle_answer
        self.calls: list[tuple[str, list | None]] = []

    def call(self, method, params=None):
        self.calls.append((method, params))
        if method == "eth_chainId":
            return ProviderCall("direct_rpc", "chain", "http://rpc.test", "0x1", 1.0)
        if method == "eth_blockNumber":
            return ProviderCall("direct_rpc", "block", "http://rpc.test", self.block, 1.0)
        if method == "eth_getBalance":
            return ProviderCall("direct_rpc", "balance", "http://rpc.test", self.balance, 1.0)
        if method == "eth_getCode":
            return ProviderCall("direct_rpc", "code", "http://rpc.test", self.code, 1.0)
        if method == "eth_call":
            data = params[0]["data"]
            if data == live_b3.TOTAL_SUPPLY_SELECTOR:
                return ProviderCall("direct_rpc", "supply", "http://rpc.test", self.total_supply, 1.0)
            if data == live_b3.DECIMALS_SELECTOR:
                return ProviderCall("direct_rpc", "decimals", "http://rpc.test", "0x8", 1.0)
            if data == live_b3.LATEST_ROUND_DATA_SELECTOR:
                updated_at = self.oracle_updated_at
                assert updated_at is not None
                payload = "0x" + "".join(
                    [
                        word(10),
                        word(self.oracle_answer),
                        word(updated_at - 5),
                        word(updated_at),
                        word(10),
                    ]
                )
                return ProviderCall("direct_rpc", "round", "http://rpc.test", payload, 1.0)
        raise AssertionError((method, params))


def install(monkeypatch, rpc: SnapshotRpc):
    probe = rpc.call("eth_chainId")
    monkeypatch.setattr(
        live_b3,
        "select_rpc_client",
        lambda chain: ("direct_rpc", rpc, probe, []),
    )
    monkeypatch.setattr(
        live_b3,
        "resolve_provider",
        lambda *a, **k: Resolution("threat", None, "PROVIDER_UNAVAILABLE", ["blockaid", "hypernative"]),
    )


def test_nonfinite_monitoring_threshold_fails_before_provider_call(monkeypatch):
    monkeypatch.setattr(
        live_b3,
        "select_rpc_client",
        lambda *_: (_ for _ in ()).throw(AssertionError("provider should not be called")),
    )

    result = live_b3.run_live_b3(
        {
            "chain": "ethereum",
            "entity": ENTITY,
            "balance_change_threshold_pct": float("nan"),
        }
    )

    assert result.status == AnalysisStatus.INSUFFICIENT_DATA
    assert result.severity == Severity.UNKNOWN
    assert result.risk_score == 0
    assert "valid balance_change_threshold_pct" in result.missing_data


def test_malformed_rpc_balance_or_bytecode_fails_closed(monkeypatch):
    for rpc in (
        SnapshotRpc(balance="not-hex"),
        SnapshotRpc(code="0x123"),
        SnapshotRpc(code="0xzz"),
    ):
        install(monkeypatch, rpc)
        result = live_b3.run_live_b3({"chain": "ethereum", "entity": ENTITY})
        assert result.status == AnalysisStatus.PROVIDER_UNAVAILABLE
        assert result.severity == Severity.UNKNOWN
        assert result.risk_score == 0
        assert "current chain snapshot" in result.missing_data
        assert any(row.get("status") == "MALFORMED_RESPONSE" for row in result.provider_status)


def test_malformed_total_supply_is_missing_not_zero_evidence(monkeypatch):
    rpc = SnapshotRpc(total_supply="bad")
    install(monkeypatch, rpc)

    result = live_b3.run_live_b3(
        {"chain": "ethereum", "entity": ENTITY, "token_contract": TOKEN}
    )

    assert result.status == AnalysisStatus.PARTIAL
    assert "token total supply" in result.missing_data
    assert "token_total_supply_raw" not in result.metrics["snapshot"]
    assert not any(
        evidence.provider_endpoint == "totalSupply()" for evidence in result.evidence
    )


def test_future_oracle_timestamp_is_unknown_not_fresh(monkeypatch):
    now = int(datetime.now(timezone.utc).timestamp())
    rpc = SnapshotRpc(oracle_updated_at=now + 3600)
    install(monkeypatch, rpc)

    result = live_b3.run_live_b3(
        {"chain": "ethereum", "entity": ENTITY, "oracle_feed": ORACLE}
    )

    assert result.status == AnalysisStatus.PARTIAL
    oracle_evidence = [
        evidence for evidence in result.evidence if evidence.source_type == "direct_oracle_state"
    ]
    assert oracle_evidence
    assert {evidence.freshness for evidence in oracle_evidence} == {FreshnessStatus.UNKNOWN}
    assert result.data_freshness["oracle"] == "UNKNOWN"
    assert "credible oracle observation timestamp" in result.missing_data
    assert any("materially in the future" in warning for warning in result.warnings)


def test_stale_oracle_promotes_result_to_stale_data(monkeypatch):
    now = int(datetime.now(timezone.utc).timestamp())
    rpc = SnapshotRpc(oracle_updated_at=now - 7200)
    install(monkeypatch, rpc)

    result = live_b3.run_live_b3(
        {"chain": "ethereum", "entity": ENTITY, "oracle_feed": ORACLE}
    )

    assert result.status == AnalysisStatus.STALE_DATA
    assert result.data_freshness["status"] == "STALE"
    assert result.data_freshness["oracle"] == "STALE"
    assert result.risk_score >= 65
    assert any(signal["type"] == "oracle_stale" for signal in result.signals)


def test_custom_oracle_age_gate_reports_stale_overall_freshness(monkeypatch):
    now = int(datetime.now(timezone.utc).timestamp())
    rpc = SnapshotRpc(oracle_updated_at=now - 300)
    install(monkeypatch, rpc)

    result = live_b3.run_live_b3(
        {
            "chain": "ethereum",
            "entity": ENTITY,
            "oracle_feed": ORACLE,
            "oracle_max_age_seconds": 60,
        }
    )

    assert result.status == AnalysisStatus.STALE_DATA
    assert result.data_freshness["oracle"] == "CURRENT"
    assert result.data_freshness["status"] == "STALE"


def test_uppercase_previous_code_hash_is_same_hash_not_change(monkeypatch):
    rpc = SnapshotRpc()
    install(monkeypatch, rpc)

    base = live_b3.run_live_b3({"chain": "ethereum", "entity": ENTITY})
    code_hash = base.metrics["snapshot"]["code_sha256"]

    result = live_b3.run_live_b3(
        {
            "chain": "ethereum",
            "entity": ENTITY,
            "previous_snapshot": {
                "chain_id": 1,
                "entity": ENTITY,
                "native_balance_wei": base.metrics["snapshot"]["native_balance_wei"],
                "code_sha256": code_hash.upper(),
            },
        }
    )

    assert not any(signal["type"] == "runtime_bytecode_changed" for signal in result.signals)
    assert not any("Runtime bytecode changed" in blocker for blocker in result.hard_blockers)


def test_b3_all_direct_snapshot_reads_are_pinned_to_captured_block(monkeypatch):
    now = int(datetime.now(timezone.utc).timestamp())
    rpc = SnapshotRpc(oracle_updated_at=now)
    install(monkeypatch, rpc)

    result = live_b3.run_live_b3(
        {
            "chain": "ethereum",
            "entity": ENTITY,
            "token_contract": TOKEN,
            "oracle_feed": ORACLE,
        }
    )

    assert result.status == AnalysisStatus.PARTIAL
    assert result.metrics["snapshot"]["block_number"] == 100
    assert result.metrics["snapshot"]["block_tag"] == "0x64"
    assert ("eth_getBalance", [ENTITY, "0x64"]) in rpc.calls
    assert ("eth_getCode", [ENTITY, "0x64"]) in rpc.calls
    snapshot_eth_calls = [params for method, params in rpc.calls if method == "eth_call"]
    assert snapshot_eth_calls
    assert all(params[-1] == "0x64" for params in snapshot_eth_calls)
    assert not any(
        params and params[-1] == "latest"
        for method, params in rpc.calls
        if method in {"eth_getBalance", "eth_getCode", "eth_call"}
    )
    assert all(
        evidence.normalized_value.get("block_tag") == "0x64"
        for evidence in result.evidence
        if evidence.provider_endpoint in {"eth_getBalance", "eth_getCode", "totalSupply()"}
    )
    assert any("pinned to captured block 0x64" in text for text in result.assumptions)
