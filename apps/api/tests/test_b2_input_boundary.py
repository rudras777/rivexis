from __future__ import annotations

from rivexis_api.models.enums import AnalysisStatus, Severity
from rivexis_api.provider_clients import ProviderCall
from rivexis_api.services import live_b2

VALID_TARGET = "0x1111111111111111111111111111111111111111"
VALID_HASH = "0x" + "ab" * 32


def fail_if_provider_called(*args, **kwargs):
    raise AssertionError("provider should not be called for invalid B2 input")


def test_b2_rejects_non_hex_target_before_provider_use(monkeypatch):
    monkeypatch.setattr(live_b2, "select_rpc_client", fail_if_provider_called)
    result = live_b2.run_live_b2(
        {"chain": "ethereum", "to": "0x" + "z" * 40, "data": "0x"}
    )

    assert result.status == AnalysisStatus.INSUFFICIENT_DATA
    assert result.severity == Severity.UNKNOWN
    assert result.provider_consensus == "UNAVAILABLE"
    assert "valid 20-byte EVM address" in result.summary


def test_b2_rejects_malformed_transaction_hash_before_provider_use(monkeypatch):
    monkeypatch.setattr(live_b2, "select_rpc_client", fail_if_provider_called)
    result = live_b2.run_live_b2(
        {"chain": "ethereum", "transaction_hash": "0x1234", "contract": VALID_TARGET}
    )

    assert result.status == AnalysisStatus.INSUFFICIENT_DATA
    assert result.severity == Severity.UNKNOWN
    assert "32-byte" in result.summary


def test_b2_rejects_invalid_explicit_sender_before_provider_use(monkeypatch):
    monkeypatch.setattr(live_b2, "select_rpc_client", fail_if_provider_called)
    result = live_b2.run_live_b2(
        {
            "chain": "ethereum",
            "transaction": {
                "from": "0x" + "g" * 40,
                "to": VALID_TARGET,
                "data": "0x",
            },
        }
    )

    assert result.status == AnalysisStatus.INSUFFICIENT_DATA
    assert result.severity == Severity.UNKNOWN
    assert "from address" in result.summary


def test_b2_malformed_rpc_transaction_address_is_invalid_data_not_provider_outage(monkeypatch):
    class Rpc:
        def call(self, method, params=None):
            if method == "eth_chainId":
                return ProviderCall("direct_rpc", "chain", "http://rpc", "0x1", 1)
            if method == "eth_blockNumber":
                return ProviderCall("direct_rpc", "block", "http://rpc", "0x64", 1)
            if method == "eth_getTransactionByHash":
                return ProviderCall(
                    "direct_rpc",
                    "tx",
                    "http://rpc",
                    {
                        "hash": VALID_HASH,
                        "from": "0x2222222222222222222222222222222222222222",
                        "to": "0x" + "z" * 40,
                        "input": "0x",
                    },
                    1,
                )
            raise AssertionError((method, params))

    rpc = Rpc()
    monkeypatch.setattr(
        live_b2,
        "select_rpc_client",
        lambda chain: ("direct_rpc", rpc, rpc.call("eth_chainId"), []),
    )
    result = live_b2.run_live_b2(
        {"chain": "ethereum", "transaction_hash": VALID_HASH}
    )

    assert result.status == AnalysisStatus.INSUFFICIENT_DATA
    assert result.status != AnalysisStatus.PROVIDER_UNAVAILABLE
    assert result.severity == Severity.UNKNOWN
    assert "Resolved transaction destination" in result.summary
