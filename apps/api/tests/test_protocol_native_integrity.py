from __future__ import annotations

from time import time

import pytest

from rivexis_api.models.enums import FreshnessStatus
from rivexis_api.provider_clients import ProviderCall
from rivexis_api.services import protocol_native

CONTRACT = "0x2222222222222222222222222222222222222222"
ORACLE = "0x3333333333333333333333333333333333333333"


class NoExplorer:
    configured = False


def word(value: int) -> str:
    return hex(value if value >= 0 else (1 << 256) + value)[2:].rjust(64, "0")


def install_rpc(monkeypatch, rpc) -> None:
    monkeypatch.setattr(
        protocol_native,
        "select_rpc_client",
        lambda chain: (
            "direct_rpc",
            rpc,
            ProviderCall("direct_rpc", "probe", "rpc", "0x1", 1),
            [],
        ),
    )
    monkeypatch.setattr(protocol_native, "EtherscanClient", NoExplorer)


def test_protocol_native_rejects_noncanonical_chain_head_without_crashing(monkeypatch):
    class Rpc:
        def call(self, method, params=None):
            assert method == "eth_blockNumber"
            return ProviderCall("direct_rpc", "block", "rpc", "0x064", 1)

    install_rpc(monkeypatch, Rpc())
    result = protocol_native.collect_protocol_native(
        {"chain": "ethereum", "contract_address": CONTRACT}
    )

    assert result.block_number is None
    assert result.evidence == []
    assert "protocol-native RPC state" in result.missing_data
    assert any(item["status"] == "MALFORMED_RPC_STATE" for item in result.provider_status)


@pytest.mark.parametrize("at_block", [True, str(2**256)])
def test_protocol_native_rejects_boolean_or_overrange_requested_block(monkeypatch, at_block):
    class Rpc:
        def call(self, method, params=None):
            assert method == "eth_blockNumber"
            return ProviderCall("direct_rpc", "block", "rpc", "0x64", 1)

    install_rpc(monkeypatch, Rpc())
    result = protocol_native.collect_protocol_native(
        {"chain": "ethereum", "contract_address": CONTRACT, "at_block": at_block}
    )

    assert result.block_number is None
    assert result.evidence == []
    assert any(item["status"] == "MALFORMED_RPC_STATE" for item in result.provider_status)


@pytest.mark.parametrize("runtime_code", ["0x0", "0xzz", "6001", "oversized"])
def test_protocol_native_never_treats_malformed_or_oversized_code_as_deployed(monkeypatch, runtime_code):
    if runtime_code == "oversized":
        runtime_code = "0x" + "00" * (128 * 1024 + 1)
    class Rpc:
        def call(self, method, params=None):
            if method == "eth_blockNumber":
                return ProviderCall("direct_rpc", "block", "rpc", "0x64", 1)
            if method == "eth_getCode":
                assert params[-1] == "0x64"
                return ProviderCall("direct_rpc", "code", "rpc", runtime_code, 1)
            raise AssertionError((method, params))

    install_rpc(monkeypatch, Rpc())
    result = protocol_native.collect_protocol_native(
        {"chain": "ethereum", "contract_address": CONTRACT}
    )

    contract = result.metrics["declared_contracts"][0]
    assert contract["state_error"] == "MALFORMED_RUNTIME_CODE"
    assert "has_code" not in contract
    assert not any(e.source_type == "direct_contract_state" for e in result.evidence)
    assert any("no deployed-code inference" in warning for warning in result.warnings)
    assert result.confidence == 62


@pytest.mark.parametrize(
    ("decimals_result", "round_result"),
    [
        ("0x08", "0x" + word(1) * 5),
        ("0x" + word(8), "0x" + word(1) * 4),
        ("0x" + word(8), "0x" + word(1) * 5 + word(0)),
        ("0x" + word(8), "0x" + "z" * (64 * 5)),
    ],
)
def test_protocol_native_oracle_requires_exact_canonical_abi_words(
    monkeypatch, decimals_result, round_result
):
    class Rpc:
        def call(self, method, params=None):
            if method == "eth_blockNumber":
                return ProviderCall("direct_rpc", "block", "rpc", "0x64", 1)
            if method == "eth_call":
                result = (
                    decimals_result
                    if params[0]["data"] == protocol_native.DECIMALS_SELECTOR
                    else round_result
                )
                return ProviderCall("direct_rpc", "call", "rpc", result, 1)
            raise AssertionError((method, params))

    install_rpc(monkeypatch, Rpc())
    result = protocol_native.collect_protocol_native(
        {"chain": "ethereum", "protocol_oracle_feed": ORACLE}
    )

    assert result.metrics["declared_oracle"] is None
    assert "normalized protocol oracle state" in result.missing_data
    assert not any(e.source_type == "direct_oracle_state" for e in result.evidence)


def test_protocol_native_future_oracle_time_remains_unknown(monkeypatch):
    updated_at = int(time()) + 3600
    round_result = "0x" + "".join(
        [word(10), word(100_00000000), word(updated_at), word(updated_at), word(10)]
    )

    class Rpc:
        def call(self, method, params=None):
            if method == "eth_blockNumber":
                return ProviderCall("direct_rpc", "block", "rpc", "0x64", 1)
            if method == "eth_call":
                result = (
                    "0x" + word(8)
                    if params[0]["data"] == protocol_native.DECIMALS_SELECTOR
                    else round_result
                )
                return ProviderCall("direct_rpc", "call", "rpc", result, 1)
            raise AssertionError((method, params))

    install_rpc(monkeypatch, Rpc())
    result = protocol_native.collect_protocol_native(
        {"chain": "ethereum", "protocol_oracle_feed": ORACLE}
    )

    assert result.metrics["declared_oracle"]["freshness"] == "UNKNOWN"
    evidence = next(e for e in result.evidence if e.source_type == "direct_oracle_state")
    assert evidence.freshness == FreshnessStatus.UNKNOWN
    assert "credible protocol oracle observation timestamp" in result.missing_data
    assert result.confidence == 62


def test_protocol_native_rejects_malformed_explorer_identity_metadata(monkeypatch):
    class Rpc:
        def call(self, method, params=None):
            if method == "eth_blockNumber":
                return ProviderCall("direct_rpc", "block", "rpc", "0x64", 1)
            if method == "eth_getCode":
                return ProviderCall("direct_rpc", "code", "rpc", "0x6000", 1)
            if method == "eth_getStorageAt":
                return ProviderCall("direct_rpc", "slot", "rpc", "0x" + "0" * 64, 1)
            raise AssertionError((method, params))

    class BadExplorer:
        configured = True

        def get_source_code(self, chain, address):
            return ProviderCall(
                "etherscan",
                "source",
                "etherscan",
                {
                    "result": [
                        {
                            "SourceCode": "contract P {}",
                            "ABI": "[]",
                            "Proxy": "1",
                            "Implementation": "not-an-address",
                        }
                    ]
                },
                1,
            )

    install_rpc(monkeypatch, Rpc())
    monkeypatch.setattr(protocol_native, "EtherscanClient", BadExplorer)
    result = protocol_native.collect_protocol_native(
        {"chain": "ethereum", "contract_address": CONTRACT}
    )

    assert not any(e.provider == "etherscan" for e in result.evidence)
    assert any(item["status"] == "MALFORMED_EXPLORER_METADATA" for item in result.provider_status)
    assert any("verified source/proxy metadata" in item for item in result.missing_data)
