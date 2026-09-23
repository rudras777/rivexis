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


def test_b2_approval_decoder_rejects_noncanonical_address_padding():
    calldata = (
        "0x095ea7b3"
        + "1" * 24
        + VALID_TARGET[2:]
        + f"{1:064x}"
    )

    decoded = live_b2._decode_approval(calldata)

    assert decoded == {"type": "MALFORMED_APPROVAL", "selector": "0x095ea7b3"}


def test_b2_approval_for_all_rejects_noncanonical_bool_word():
    calldata = (
        "0xa22cb465"
        + "0" * 24
        + VALID_TARGET[2:]
        + f"{2:064x}"
    )

    decoded = live_b2._decode_approval(calldata)

    assert decoded == {"type": "MALFORMED_APPROVAL", "selector": "0xa22cb465"}


def test_b2_contract_code_is_pinned_to_captured_block(monkeypatch):
    class Rpc:
        def __init__(self):
            self.calls = []

        def call(self, method, params=None):
            self.calls.append((method, params))
            if method == "eth_chainId":
                return ProviderCall("direct_rpc", "chain", "http://rpc", "0x1", 1)
            if method == "eth_blockNumber":
                return ProviderCall("direct_rpc", "block", "http://rpc", "0x64", 1)
            if method == "eth_getCode":
                return ProviderCall("direct_rpc", "code", "http://rpc", "0x", 1)
            raise AssertionError((method, params))

    rpc = Rpc()
    monkeypatch.setattr(
        live_b2,
        "select_rpc_client",
        lambda chain: ("direct_rpc", rpc, rpc.call("eth_chainId"), []),
    )
    monkeypatch.setattr(
        live_b2,
        "resolve_provider",
        lambda *args, **kwargs: type("Resolution", (), {"provider_id": None})(),
    )

    result = live_b2.run_live_b2({"chain": "ethereum", "contract": VALID_TARGET})

    assert result.status == AnalysisStatus.PARTIAL
    assert ("eth_getCode", [VALID_TARGET, "0x64"]) in rpc.calls
    assert not any(
        method == "eth_getCode" and params and params[-1] == "latest"
        for method, params in rpc.calls
    )
    direct = next(
        item for item in result.evidence if item.provider_endpoint == "eth_getCode"
    )
    assert direct.block_number == 100
    assert direct.normalized_value["block_tag"] == "0x64"
    assert any("pinned to captured RPC block 0x64" in text for text in result.assumptions)


def test_b2_malformed_contract_bytecode_is_not_treated_as_contract_state(monkeypatch):
    class Rpc:
        def call(self, method, params=None):
            if method == "eth_chainId":
                return ProviderCall("direct_rpc", "chain", "http://rpc", "0x1", 1)
            if method == "eth_blockNumber":
                return ProviderCall("direct_rpc", "block", "http://rpc", "0x64", 1)
            if method == "eth_getCode":
                return ProviderCall("direct_rpc", "code", "http://rpc", "0xzz", 1)
            raise AssertionError((method, params))

    rpc = Rpc()
    monkeypatch.setattr(
        live_b2,
        "select_rpc_client",
        lambda chain: ("direct_rpc", rpc, rpc.call("eth_chainId"), []),
    )
    monkeypatch.setattr(
        live_b2,
        "resolve_provider",
        lambda *args, **kwargs: type("Resolution", (), {"provider_id": None})(),
    )

    result = live_b2.run_live_b2({"chain": "ethereum", "contract": VALID_TARGET})

    assert result.status == AnalysisStatus.PARTIAL
    assert result.metrics["contract_code_present"] is False
    assert "contract bytecode state" in result.missing_data
    assert not any(item.provider_endpoint == "eth_getCode" for item in result.evidence)
