from __future__ import annotations

from rivexis_api.provider_clients import ProviderCall
from rivexis_api.services.deployment_registry import list_protocol_deployments, enrich_protocol_adapter_input, REGISTRY_VERSION
from rivexis_api.services.evm_decode import function_selector
from rivexis_api.services.protocol_adapters import collect_protocol_adapter


def w(v: int) -> str:
    return hex(v)[2:].rjust(64, "0")


def wa(address: str) -> str:
    return address[2:].lower().rjust(64, "0")


def ret(*words: str) -> str:
    return "0x" + "".join(words)


class AaveOfficialRpc:
    asset = "0x2222222222222222222222222222222222222222"
    source = "0x3333333333333333333333333333333333333333"
    strategy = "0x4444444444444444444444444444444444444444"

    def __init__(self):
        self.block_tags = []

    def call(self, method, params=None):
        assert method == "eth_call"
        self.block_tags.append(params[1])
        selector = params[0]["data"][:10]
        if selector == function_selector("getReserveConfigurationData(address)"):
            return ProviderCall("direct_rpc", "cfg", "rpc", ret(w(6), w(7500), w(8000), w(10500), w(1000), w(1), w(1), w(0), w(1), w(0)), 1)
        if selector == function_selector("getReserveCaps(address)"):
            return ProviderCall("direct_rpc", "caps", "rpc", ret(w(1000), w(2000)), 1)
        scalar = {
            function_selector("getDebtCeiling(address)"): 0,
            function_selector("getPaused(address)"): 0,
            function_selector("getSiloedBorrowing(address)"): 0,
            function_selector("getLiquidationProtocolFee(address)"): 1000,
            function_selector("getReserveEModeCategory(address)"): 0,
        }
        if selector in scalar:
            return ProviderCall("direct_rpc", "scalar", "rpc", ret(w(scalar[selector])), 1)
        if selector == function_selector("getInterestRateStrategyAddress(address)"):
            return ProviderCall("direct_rpc", "strategy", "rpc", ret(wa(self.strategy)), 1)
        if selector == function_selector("getSourceOfAsset(address)"):
            return ProviderCall("direct_rpc", "source", "rpc", ret(wa(self.source)), 1)
        raise AssertionError((method, params))


def test_registry_contains_official_protocol_sources():
    aave = list_protocol_deployments("aave_v3", 1)[0]
    compound = list_protocol_deployments("compound_v3", 1)[0]
    morpho = list_protocol_deployments("morpho_blue", 8453)[0]
    assert aave["contracts"]["pool"] == "0x87870bca3f3fd6335c3f4ce8392d69350b4fa4e2"
    assert compound["contracts"]["comet"] == "0xc3d688b66703497daa19211eedff47f25384cdc3"
    assert morpho["contracts"]["morpho"] == "0xbbbbbbbbbb9cc5e90e3b3af64bdaf62c37eeffcb"
    assert all(x["registry_version"] == REGISTRY_VERSION for x in (aave, compound, morpho))
    assert all(x["source_kind"].startswith("official_") for x in (aave, compound, morpho))


def test_aave_official_registry_autofill_and_historical_read():
    rpc = AaveOfficialRpc()
    out = collect_protocol_adapter(
        {"protocol_adapter": "aave_v3", "asset_address": rpc.asset, "at_block": 0x1200},
        rpc=rpc, chain_id=1, block_number=0x1234,
    )
    identity = out.metrics["deployment_identity"]
    assert identity["status"] == "VERIFIED"
    assert out.metrics["data_provider"] == "0x0a16f2fcc0d44fae41cc54e079281d84a363becd"
    assert out.metrics["interest_rate_strategy"] == rpc.strategy
    assert out.metrics["asset_oracle_source"] == rpc.source
    assert out.metrics["read_block_number"] == 0x1200
    assert out.metrics["block_tag"] == "0x1200"
    assert rpc.block_tags and set(rpc.block_tags) == {"0x1200"}
    assert "official deployment identity allowlist verification" not in out.missing_data
    assert any(e.source_type == "official_deployment_registry" for e in out.evidence)


def test_explicit_aave_mismatch_is_not_silently_overridden():
    supplied = "0x1111111111111111111111111111111111111111"
    enriched, identity = enrich_protocol_adapter_input({"protocol_adapter": "aave_v3", "aave_data_provider": supplied}, 1)
    assert enriched["aave_data_provider"] == supplied
    assert identity["status"] == "MISMATCH"
    assert identity["expected"] != supplied


def test_compound_registry_autofill_and_core_configuration():
    asset = "0x2222222222222222222222222222222222222222"
    feed = "0x3333333333333333333333333333333333333333"
    governor = "0x6d903f6003cca6255d85cca4d3b5e5146dc33925"
    guardian = "0xbbf3f1421d886e9b2c5d716b5192ac998af2012c"
    base = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
    base_feed = "0x8fffffd4afb6115b954bd326cbe7b4ba576818f6"

    class Rpc:
        def call(self, method, params=None):
            if method == "eth_getCode":
                return ProviderCall("direct_rpc", "code", "rpc", "0x6001600055", 1)
            if method == "eth_getBlockByNumber":
                return ProviderCall("direct_rpc", "block", "rpc", {"timestamp": "0x1000"}, 1)
            assert method == "eth_call"
            selector = params[0]["data"][:10]
            if selector == function_selector("getAssetInfoByAddress(address)"):
                return ProviderCall("direct_rpc", "info", "rpc", ret(w(0), wa(asset), wa(feed), w(10**18), w(int(.75*10**18)), w(int(.82*10**18)), w(int(.93*10**18)), w(10**24)), 1)
            if selector == function_selector("getPrice(address)"):
                return ProviderCall("direct_rpc", "price", "rpc", ret(w(2000 * 10**8)), 1)
            addresses = {
                function_selector("governor()"): governor,
                function_selector("pauseGuardian()"): guardian,
                function_selector("baseToken()"): base,
                function_selector("baseTokenPriceFeed()"): base_feed,
                function_selector("extensionDelegate()"): "0x5555555555555555555555555555555555555555",
            }
            if selector in addresses:
                return ProviderCall("direct_rpc", "addr", "rpc", ret(wa(addresses[selector])), 1)
            uints = {
                function_selector("numAssets()"): 5,
                function_selector("getUtilization()"): int(.7*10**18),
                function_selector("targetReserves()"): 5_000_000 * 10**6,
            }
            if selector in uints:
                return ProviderCall("direct_rpc", "uint", "rpc", ret(w(uints[selector])), 1)
            if selector in {
                function_selector("isSupplyPaused()"), function_selector("isTransferPaused()"),
                function_selector("isWithdrawPaused()"), function_selector("isAbsorbPaused()"),
                function_selector("isBuyPaused()"),
            }:
                return ProviderCall("direct_rpc", "bool", "rpc", ret(w(0)), 1)
            raise AssertionError((method, params))

    out = collect_protocol_adapter({"protocol_adapter": "compound_v3", "compound_market": "usdc", "collateral_asset": asset}, rpc=Rpc(), chain_id=1, block_number=100)
    assert out.metrics["deployment_identity"]["status"] == "VERIFIED"
    assert out.metrics["comet"] == "0xc3d688b66703497daa19211eedff47f25384cdc3"
    assert out.metrics["core_configuration"]["governor"] == governor
    assert out.metrics["core_configuration"]["num_assets"] == 5
    assert out.metrics["core_configuration"]["supply_paused"] is False


def test_morpho_registry_and_chainlink_oracle_composition():
    market_id = "0x" + "ab" * 32
    loan = "0x1111111111111111111111111111111111111111"
    collateral = "0x2222222222222222222222222222222222222222"
    oracle = "0x3333333333333333333333333333333333333333"
    official_irm = "0x870ac11d48b15db9a138cf899d20f13f79ba00bc"
    feed1 = "0x4444444444444444444444444444444444444444"

    class Rpc:
        def call(self, method, params=None):
            if method == "eth_getCode":
                return ProviderCall("direct_rpc", "code", "rpc", "0x6001600055", 1)
            if method == "eth_getBlockByNumber":
                return ProviderCall("direct_rpc", "block", "rpc", {"timestamp": "0x1000"}, 1)
            assert method == "eth_call"
            selector = params[0]["data"][:10]
            if selector == function_selector("idToMarketParams(bytes32)"):
                return ProviderCall("direct_rpc", "params", "rpc", ret(wa(loan), wa(collateral), wa(oracle), wa(official_irm), w(int(.86*10**18))), 1)
            if selector == function_selector("market(bytes32)"):
                return ProviderCall("direct_rpc", "market", "rpc", ret(w(1000), w(1000), w(500), w(500), w(1), w(0)), 1)
            if selector == function_selector("price()"):
                return ProviderCall("direct_rpc", "price", "rpc", ret(w(2*10**36)), 1)
            if selector == function_selector("isIrmEnabled(address)"):
                return ProviderCall("direct_rpc", "irm-enabled", "rpc", ret(w(1)), 1)
            if selector == function_selector("isMorphoChainlinkOracleV2(address)"):
                return ProviderCall("direct_rpc", "oracle-factory", "rpc", ret(w(1)), 1)
            if selector == function_selector("rateAtTarget(bytes32)"):
                return ProviderCall("direct_rpc", "rate-target", "rpc", ret(w(123456)), 1)
            if selector == function_selector("MORPHO()"):
                return ProviderCall("direct_rpc", "irm-morpho", "rpc", ret(wa("0xbbbbbbbbbb9cc5e90e3b3af64bdaf62c37eeffcb")), 1)
            if selector == function_selector("borrowRateView((address,address,address,address,uint256),(uint128,uint128,uint128,uint128,uint128,uint128))"):
                return ProviderCall("direct_rpc", "borrow-rate", "rpc", ret(w(1268391679)), 1)
            if selector == function_selector("decimals()"):
                return ProviderCall("direct_rpc", "feed-dec", "rpc", ret(w(8)), 1)
            if selector == function_selector("latestRoundData()"):
                return ProviderCall("direct_rpc", "feed-round", "rpc", ret(w(1),w(2000_00000000),w(0),w(0x0ff0),w(1)), 1)
            addresses = {
                function_selector("BASE_VAULT()"): "0x0000000000000000000000000000000000000000",
                function_selector("BASE_FEED_1()"): feed1,
                function_selector("BASE_FEED_2()"): "0x0000000000000000000000000000000000000000",
                function_selector("QUOTE_VAULT()"): "0x0000000000000000000000000000000000000000",
                function_selector("QUOTE_FEED_1()"): "0x0000000000000000000000000000000000000000",
                function_selector("QUOTE_FEED_2()"): "0x0000000000000000000000000000000000000000",
            }
            if selector in addresses:
                return ProviderCall("direct_rpc", "comp-a", "rpc", ret(wa(addresses[selector])), 1)
            if selector in {function_selector("BASE_VAULT_CONVERSION_SAMPLE()"), function_selector("QUOTE_VAULT_CONVERSION_SAMPLE()")}:
                return ProviderCall("direct_rpc", "sample", "rpc", ret(w(1)), 1)
            if selector == function_selector("SCALE_FACTOR()"):
                return ProviderCall("direct_rpc", "scale", "rpc", ret(w(10**36)), 1)
            raise AssertionError((method, params))

    out = collect_protocol_adapter({"protocol_adapter": "morpho_blue", "morpho_market_id": market_id}, rpc=Rpc(), chain_id=1, block_number=100)
    assert out.metrics["deployment_identity"]["status"] == "VERIFIED"
    assert out.metrics["irm_classification"] == "official_adaptive_curve"
    assert out.metrics["oracle_composition"]["base_feed_1"] == feed1
    assert out.metrics["oracle_composition"]["recognized_morpho_chainlink_oracle_v2_surface"] is True
    assert out.metrics["dependency_provenance"]["irm_enabled_by_morpho"] is True
    assert out.metrics["dependency_provenance"]["oracle_created_by_official_factory"] is True
    assert out.metrics["dependency_provenance"]["adaptive_curve_rate_at_target_raw"] == 123456

def test_protocol_native_propagates_historical_block(monkeypatch):
    from rivexis_api.services import protocol_native

    class Rpc(AaveOfficialRpc):
        def call(self, method, params=None):
            if method == "eth_blockNumber":
                return ProviderCall("direct_rpc", "head", "rpc", "0x1234", 1)
            return super().call(method, params)

    rpc = Rpc()
    monkeypatch.setattr(protocol_native, "select_rpc_client", lambda chain: ("direct_rpc", rpc, ProviderCall("direct_rpc", "probe", "rpc", "0x1", 1), []))
    out = protocol_native.collect_protocol_native({"chain": "ethereum", "protocol_adapter": "aave_v3", "asset_address": rpc.asset, "at_block": "0x1200"})
    assert out.block_number == 0x1200
    assert out.metrics["protocol_adapter"]["read_block_number"] == 0x1200
    assert set(rpc.block_tags) == {"0x1200"}


def test_protocol_deployment_registry_api_surface():
    from fastapi.testclient import TestClient
    from rivexis_api.main import app

    with TestClient(app) as client:
        response = client.get("/api/v1/protocol-deployments", params={"adapter": "aave_v3", "chain_id": 1})
        assert response.status_code == 200
        body = response.json()
        assert body["registry_version"] == REGISTRY_VERSION
        assert len(body["items"]) == 1
        assert body["items"][0]["deployment_id"] == "aave-v3-ethereum"
