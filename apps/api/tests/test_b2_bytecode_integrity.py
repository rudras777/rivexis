from rivexis_api.engines import ENGINES
from rivexis_api.models.enums import AnalysisStatus, EngineId
from rivexis_api.provider_clients import ProviderCall
from rivexis_api.services import live_b2


TARGET = "0x1111111111111111111111111111111111111111"
IMPLEMENTATION = "0x2222222222222222222222222222222222222222"
OTHER_IMPLEMENTATION = "0x3333333333333333333333333333333333333333"


def minimal_proxy(implementation: str) -> str:
    return (
        "0x"
        + live_b2.EIP1167_PREFIX.hex()
        + implementation[2:]
        + live_b2.EIP1167_SUFFIX.hex()
    )


class Rpc:
    def __init__(self, code: str):
        self.code = code

    def call(self, method, params=None):
        if method == "eth_chainId":
            return ProviderCall("direct_rpc", "chain", "http://rpc", "0x1", 1)
        if method == "eth_blockNumber":
            return ProviderCall("direct_rpc", "block", "http://rpc", "0x64", 1)
        if method == "eth_getCode":
            return ProviderCall("direct_rpc", "code", "http://rpc", self.code, 1)
        raise AssertionError((method, params))


def configure(monkeypatch, rpc: Rpc, etherscan):
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
    monkeypatch.setattr(live_b2, "EtherscanClient", etherscan)


def test_b2_rpc_quantity_requires_canonical_bounded_hex():
    assert live_b2._rpc_quantity("0x0") == 0
    assert live_b2._rpc_quantity("0x10") == 16
    for value in (1, True, "10", "0x", "0x00", "0xgg", hex(2**256)):
        assert live_b2._rpc_quantity(value) is None


def test_runtime_opcode_parser_skips_push_data():
    observations = live_b2._runtime_bytecode_observations(
        bytes.fromhex("64f0f2f4f5ff00")
    )

    assert observations["opcode_presence"] == {}
    assert observations["instruction_count"] == 2
    assert observations["is_security_verdict"] is False


def test_runtime_opcode_parser_reports_structural_opcodes_without_verdict():
    observations = live_b2._runtime_bytecode_observations(
        bytes([0xF4, 0xF0, 0xF5, 0xFF])
    )

    assert observations["opcode_presence"] == {
        "CREATE": 1,
        "DELEGATECALL": 1,
        "CREATE2": 1,
        "SELFDESTRUCT": 1,
    }
    assert observations["is_security_verdict"] is False


def test_exact_eip1167_runtime_extracts_canonical_implementation():
    normalized = live_b2._bytecode(minimal_proxy(IMPLEMENTATION))
    assert normalized is not None

    observations = live_b2._runtime_bytecode_observations(normalized[1])

    assert observations["exact_eip1167_minimal_proxy"] is True
    assert observations["embedded_implementation"] == IMPLEMENTATION


def test_bytecode_size_is_bounded():
    oversized = "0x" + "00" * (live_b2.MAX_RUNTIME_BYTECODE_BYTES + 1)
    assert live_b2._bytecode(oversized) is None


def test_etherscan_proxy_metadata_requires_canonical_shape_and_address():
    valid = {
        "result": [
            {
                "SourceCode": "contract Proxy {}",
                "ABI": "[]",
                "ContractName": "Proxy",
                "CompilerVersion": "v0.8.0",
                "Proxy": "1",
                "Implementation": IMPLEMENTATION.upper().replace("0X", "0x"),
            }
        ]
    }
    normalized = live_b2._normalize_etherscan_source(valid)
    assert normalized is not None
    assert normalized["implementation"] == IMPLEMENTATION
    assert normalized["proxy"] is True

    assert live_b2._normalize_etherscan_source({"result": []}) is None
    invalid = {"result": [{**valid["result"][0], "Implementation": "not-an-address"}]}
    assert live_b2._normalize_etherscan_source(invalid) is None
    contradictory = {"result": [{**valid["result"][0], "Proxy": "0"}]}
    assert live_b2._normalize_etherscan_source(contradictory) is None


def test_live_b2_exposes_exact_minimal_proxy_without_vulnerability_claim(monkeypatch):
    rpc = Rpc(minimal_proxy(IMPLEMENTATION))

    class NoEtherscan:
        configured = False

    configure(monkeypatch, rpc, NoEtherscan)
    result = live_b2.run_live_b2({"chain": "ethereum", "contract": TARGET})

    assert result.status == AnalysisStatus.PARTIAL
    assert result.metrics["proxy"] is True
    assert result.metrics["implementation"] == IMPLEMENTATION
    assert result.metrics["proxy_sources"] == ["exact_eip1167_runtime"]
    assert result.metrics["runtime_bytecode"]["is_security_verdict"] is False
    assert any(signal["type"] == "exact_eip1167_minimal_proxy" for signal in result.signals)
    assert {item.calculation_version for item in result.evidence} == {"b2-live-1.3.0"}


def test_zero_target_minimal_proxy_is_detected_but_identity_remains_missing(monkeypatch):
    rpc = Rpc(minimal_proxy("0x" + "0" * 40))

    class NoEtherscan:
        configured = False

    configure(monkeypatch, rpc, NoEtherscan)
    result = live_b2.run_live_b2({"chain": "ethereum", "contract": TARGET})

    assert result.metrics["proxy"] is True
    assert result.metrics["implementation"] is None
    assert result.metrics["proxy_sources"] == ["exact_eip1167_runtime"]
    assert "proxy implementation address" in result.missing_data


def test_live_b2_reports_direct_explorer_implementation_conflict(monkeypatch):
    rpc = Rpc(minimal_proxy(IMPLEMENTATION))

    class Etherscan:
        configured = True

        def get_source_code(self, chain, address):
            return ProviderCall(
                "etherscan",
                "source",
                "https://api.etherscan.io/v2/api",
                {
                    "result": [
                        {
                            "SourceCode": "contract Proxy {}",
                            "ABI": "[]",
                            "ContractName": "Proxy",
                            "CompilerVersion": "v0.8.0",
                            "Proxy": "1",
                            "Implementation": OTHER_IMPLEMENTATION,
                        }
                    ]
                },
                1,
            )

    configure(monkeypatch, rpc, Etherscan)
    result = live_b2.run_live_b2({"chain": "ethereum", "contract": TARGET})

    assert result.metrics["implementation"] is None
    assert result.metrics["implementation_conflict"] is True
    assert "resolved proxy implementation identity" in result.missing_data
    assert any(signal["type"] == "proxy_implementation_conflict" for signal in result.signals)
    assert len(result.provider_conflicts) == 1
    assert result.provider_conflicts[0].metric == "proxy_implementation"
    explorer = next(item for item in result.evidence if item.provider == "etherscan")
    assert explorer.block_number is None
    assert explorer.freshness.value == "UNKNOWN"
    assert result.data_freshness["status"] == "UNKNOWN"

    dispatched = ENGINES[EngineId.B2](
        {"chain": "ethereum", "contract": TARGET}, False
    )
    assert dispatched.status == AnalysisStatus.CONFLICTING_DATA
    assert dispatched.provider_consensus == "CONFLICTING"


def test_malformed_explorer_metadata_is_unavailable_not_unverified(monkeypatch):
    rpc = Rpc("0x6001600055")

    class Etherscan:
        configured = True

        def get_source_code(self, chain, address):
            return ProviderCall(
                "etherscan",
                "source",
                "https://api.etherscan.io/v2/api",
                {"result": []},
                1,
            )

    configure(monkeypatch, rpc, Etherscan)
    result = live_b2.run_live_b2({"chain": "ethereum", "contract": TARGET})

    assert result.metrics["verified_source"] is None
    assert "contract verification state" in result.missing_data
    assert not any("source code is not verified" in item for item in result.warnings)
