from __future__ import annotations

from rivexis_api.provider_clients import ProviderCall
from rivexis_api.services import protocol_native
from rivexis_api.services.evm_decode import function_selector


def w(v: int) -> str:
    return hex(v)[2:].rjust(64, "0")


def wa(address: str) -> str:
    return address[2:].lower().rjust(64, "0")


def ret(*words: str) -> str:
    return "0x" + "".join(words)


class BaseRpc:
    def call(self, method, params=None):
        if method == "eth_chainId":
            return ProviderCall("direct_rpc", "chain", "rpc", "0x1", 1)
        if method == "eth_blockNumber":
            return ProviderCall("direct_rpc", "block", "rpc", "0x1234", 1)
        raise AssertionError((method, params))


def select(rpc):
    return "direct_rpc", rpc, rpc.call("eth_chainId"), []


def test_aave_v3_adapter_reads_reserve_and_user_health(monkeypatch):
    provider = "0x1111111111111111111111111111111111111111"
    asset = "0x2222222222222222222222222222222222222222"
    pool = "0x3333333333333333333333333333333333333333"
    user = "0x4444444444444444444444444444444444444444"

    class Rpc(BaseRpc):
        def call(self, method, params=None):
            if method == "eth_getCode":
                return ProviderCall("direct_rpc", "m-code", "rpc", "0x6001600055", 1)
            if method == "eth_getBlockByNumber":
                return ProviderCall("direct_rpc", "m-block", "rpc", {"timestamp": "0x100"}, 1)
            if method != "eth_call":
                return super().call(method, params)
            selector = params[0]["data"][:10]
            if selector == function_selector("getReserveConfigurationData(address)"):
                return ProviderCall("direct_rpc", "a-cfg", "rpc", ret(
                    w(6), w(7500), w(8000), w(10500), w(1000), w(1), w(1), w(0), w(1), w(0)
                ), 1)
            if selector == function_selector("getReserveCaps(address)"):
                return ProviderCall("direct_rpc", "a-caps", "rpc", ret(w(1000000), w(2000000)), 1)
            scalar = {
                function_selector("getDebtCeiling(address)"): 500000,
                function_selector("getPaused(address)"): 0,
                function_selector("getSiloedBorrowing(address)"): 0,
                function_selector("getLiquidationProtocolFee(address)"): 1000,
                function_selector("getReserveEModeCategory(address)"): 1,
            }
            if selector in scalar:
                return ProviderCall("direct_rpc", "a-s", "rpc", ret(w(scalar[selector])), 1)
            if selector == function_selector("getUserAccountData(address)"):
                return ProviderCall("direct_rpc", "a-pos", "rpc", ret(
                    w(100_000_000), w(75_000_000), w(5_000_000), w(8000), w(7500), w(int(1.0666666667 * 10**18))
                ), 1)
            raise AssertionError((method, params))

    rpc = Rpc()
    monkeypatch.setattr(protocol_native, "select_rpc_client", lambda chain: select(rpc))
    out = protocol_native.collect_protocol_native({
        "chain": "ethereum", "protocol_adapter": "aave_v3", "aave_data_provider": provider,
        "asset_address": asset, "aave_pool": pool, "user_address": user,
    })
    a = out.metrics["protocol_adapter"]
    assert a["adapter"] == "aave_v3"
    assert a["reserve_configuration"]["ltv_bps"] == 7500
    assert a["reserve_configuration"]["liquidation_threshold_bps"] == 8000
    assert a["reserve_caps"]["borrow_cap"] == 1000000
    assert round(a["position"]["health_factor"], 3) == 1.067
    assert any(e.source_type == "protocol_native_position" for e in out.evidence)


def test_compound_v3_adapter_reads_factors_price_and_liquidatability(monkeypatch):
    comet = "0x1111111111111111111111111111111111111111"
    asset = "0x2222222222222222222222222222222222222222"
    feed = "0x3333333333333333333333333333333333333333"
    user = "0x4444444444444444444444444444444444444444"

    class Rpc(BaseRpc):
        def call(self, method, params=None):
            if method != "eth_call":
                return super().call(method, params)
            selector = params[0]["data"][:10]
            if selector == function_selector("getAssetInfoByAddress(address)"):
                return ProviderCall("direct_rpc", "c-info", "rpc", ret(
                    w(0), wa(asset), wa(feed), w(10**8), w(int(.80*10**18)), w(int(.85*10**18)), w(int(.90*10**18)), w(1000*10**8)
                ), 1)
            if selector == function_selector("getPrice(address)"):
                return ProviderCall("direct_rpc", "c-price", "rpc", ret(w(65000 * 10**8)), 1)
            if selector == function_selector("isLiquidatable(address)"):
                return ProviderCall("direct_rpc", "c-liq", "rpc", ret(w(1)), 1)
            if selector == function_selector("isBorrowCollateralized(address)"):
                return ProviderCall("direct_rpc", "c-col", "rpc", ret(w(0)), 1)
            if selector == function_selector("borrowBalanceOf(address)"):
                return ProviderCall("direct_rpc", "c-bor", "rpc", ret(w(5000 * 10**6)), 1)
            if selector == function_selector("collateralBalanceOf(address,address)"):
                return ProviderCall("direct_rpc", "c-bal", "rpc", ret(w(1 * 10**8)), 1)
            raise AssertionError((method, params))

    rpc = Rpc()
    monkeypatch.setattr(protocol_native, "select_rpc_client", lambda chain: select(rpc))
    out = protocol_native.collect_protocol_native({
        "chain": "ethereum", "protocol_adapter": "compound_v3", "comet_address": comet,
        "collateral_asset": asset, "user_address": user,
    })
    c = out.metrics["protocol_adapter"]
    assert c["adapter"] == "compound_v3"
    assert c["asset_info"]["price_feed"] == feed
    assert c["protocol_price"]["price_usd"] == 65000
    assert c["position"]["is_liquidatable"] is True
    assert out.risk_delta >= 50


def test_morpho_blue_adapter_reads_immutable_market_and_health(monkeypatch):
    market_id = "0x" + "ab" * 32
    loan = "0x1111111111111111111111111111111111111111"
    collateral = "0x2222222222222222222222222222222222222222"
    oracle = "0x3333333333333333333333333333333333333333"
    irm = "0x4444444444444444444444444444444444444444"
    user = "0x5555555555555555555555555555555555555555"

    class Rpc(BaseRpc):
        def call(self, method, params=None):
            if method == "eth_getCode":
                return ProviderCall("direct_rpc", "m-code", "rpc", "0x6001600055", 1)
            if method == "eth_getBlockByNumber":
                return ProviderCall("direct_rpc", "m-block", "rpc", {"timestamp": "0x100"}, 1)
            if method != "eth_call":
                return super().call(method, params)
            selector = params[0]["data"][:10]
            if selector == function_selector("idToMarketParams(bytes32)"):
                return ProviderCall("direct_rpc", "m-par", "rpc", ret(wa(loan), wa(collateral), wa(oracle), wa(irm), w(int(.86*10**18))), 1)
            if selector == function_selector("market(bytes32)"):
                return ProviderCall("direct_rpc", "m-state", "rpc", ret(w(1_000_000), w(1_000_000), w(800_000), w(800_000), w(100), w(int(.1*10**18))), 1)
            if selector == function_selector("price()"):
                return ProviderCall("direct_rpc", "m-price", "rpc", ret(w(2 * 10**36)), 1)
            if selector == function_selector("position(bytes32,address)"):
                # 100 collateral * price 2 = 200 loan value; borrow 160 -> HF 1.075
                return ProviderCall("direct_rpc", "m-pos", "rpc", ret(w(0), w(160), w(100)), 1)
            if selector == function_selector("isIrmEnabled(address)"):
                return ProviderCall("direct_rpc", "m-irm-enabled", "rpc", ret(w(1)), 1)
            if selector == function_selector("isMorphoChainlinkOracleV2(address)"):
                return ProviderCall("direct_rpc", "m-oracle-factory", "rpc", ret(w(0)), 1)
            oracle_address_getters = {
                function_selector("BASE_VAULT()"), function_selector("BASE_FEED_1()"), function_selector("BASE_FEED_2()"),
                function_selector("QUOTE_VAULT()"), function_selector("QUOTE_FEED_1()"), function_selector("QUOTE_FEED_2()"),
            }
            if selector in oracle_address_getters:
                return ProviderCall("direct_rpc", "m-comp-a", "rpc", ret(w(0)), 1)
            if selector in {function_selector("BASE_VAULT_CONVERSION_SAMPLE()"), function_selector("QUOTE_VAULT_CONVERSION_SAMPLE()"), function_selector("SCALE_FACTOR()")}:
                return ProviderCall("direct_rpc", "m-comp-u", "rpc", ret(w(10**18)), 1)
            raise AssertionError((method, params))

    rpc = Rpc()
    monkeypatch.setattr(protocol_native, "select_rpc_client", lambda chain: select(rpc))
    out = protocol_native.collect_protocol_native({
        "chain": "ethereum", "protocol_adapter": "morpho_blue", "morpho_market_id": market_id,
        "user_address": user,
    })
    m = out.metrics["protocol_adapter"]
    assert m["adapter"] == "morpho_blue"
    assert m["market_params"]["oracle"] == oracle
    assert m["market_params"]["lltv"] == .86
    assert m["market_state"]["utilization"] == .8
    assert round(m["position"]["health_factor"], 3) == 1.075
    assert any(e.source_type == "protocol_native_market_parameters" for e in out.evidence)

def test_f3_uses_protocol_native_aave_position_without_manual_model(monkeypatch):
    from rivexis_api.services import live_f3
    provider = "0x1111111111111111111111111111111111111111"
    asset = "0x2222222222222222222222222222222222222222"
    pool = "0x3333333333333333333333333333333333333333"
    user = "0x4444444444444444444444444444444444444444"

    class Rpc(BaseRpc):
        def call(self, method, params=None):
            if method != "eth_call": return super().call(method, params)
            selector=params[0]["data"][:10]
            if selector==function_selector("getReserveConfigurationData(address)"):
                return ProviderCall("direct_rpc","cfg","rpc",ret(w(6),w(7500),w(8000),w(10500),w(1000),w(1),w(1),w(0),w(1),w(0)),1)
            if selector==function_selector("getReserveCaps(address)"):
                return ProviderCall("direct_rpc","caps","rpc",ret(w(1),w(2)),1)
            if selector in {function_selector("getDebtCeiling(address)"),function_selector("getPaused(address)"),function_selector("getSiloedBorrowing(address)"),function_selector("getReserveEModeCategory(address)")}:
                return ProviderCall("direct_rpc","s","rpc",ret(w(0)),1)
            if selector==function_selector("getLiquidationProtocolFee(address)"):
                return ProviderCall("direct_rpc","fee","rpc",ret(w(1000)),1)
            if selector==function_selector("getUserAccountData(address)"):
                return ProviderCall("direct_rpc","pos","rpc",ret(w(100),w(85),w(0),w(8000),w(7500),w(int(.94*10**18))),1)
            raise AssertionError((method,params))
    rpc=Rpc(); monkeypatch.setattr(protocol_native,"select_rpc_client",lambda chain: select(rpc))
    r=live_f3.run_live_f3({"chain":"ethereum","protocol_adapter":"aave_v3","aave_data_provider":provider,"asset_address":asset,"aave_pool":pool,"user_address":user})
    assert r.metrics["authoritative_adapter"]=="aave_v3"
    assert r.risk_score>=90
    assert r.hard_blockers
    assert "collateral_price_feed" not in " ".join(r.missing_data)
