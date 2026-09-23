from __future__ import annotations

from dataclasses import dataclass

from rivexis_api.models.enums import AnalysisStatus, EngineId
from rivexis_api.provider_clients import ProviderCall, ProviderError
from rivexis_api.providers import Resolution
from rivexis_api.services import live_b1, live_b2


@dataclass
class FakeRpc:
    revert: bool = False
    approval_code: str = "0x6001600055"

    def call(self, method, params=None):
        if method == "eth_chainId":
            return ProviderCall("direct_rpc", "req-chain", "http://rpc.test", "0x1", 1.2)
        if method == "eth_blockNumber":
            return ProviderCall("direct_rpc", "req-block", "http://rpc.test", "0x64", 1.5)
        if method == "eth_call":
            if self.revert:
                raise ProviderError("execution reverted: denied", provider_id="direct_rpc", code="RPC_-32000")
            return ProviderCall("direct_rpc", "req-call", "http://rpc.test", "0x", 2.1)
        if method == "eth_estimateGas":
            if self.revert:
                raise ProviderError("execution reverted", provider_id="direct_rpc", code="RPC_-32000")
            return ProviderCall("direct_rpc", "req-gas", "http://rpc.test", "0x5208", 2.2)
        if method == "eth_getCode":
            return ProviderCall("direct_rpc", "req-code", "http://rpc.test", self.approval_code, 1.1)
        if method == "eth_getTransactionByHash":
            return ProviderCall("direct_rpc", "req-tx", "http://rpc.test", None, 1.1)
        raise AssertionError(method)


def _select(fake):
    probe = fake.call("eth_chainId")
    return "direct_rpc", fake, probe, [{"provider_id": "alchemy", "error": "NOT_CONFIGURED"}]


def test_live_b1_rpc_dry_run_is_partial_and_non_demo(monkeypatch):
    fake = FakeRpc()
    monkeypatch.setattr(live_b1, "select_rpc_client", lambda chain: _select(fake))
    monkeypatch.setattr(live_b1, "resolve_provider", lambda *a, **k: Resolution("simulation", None, "PROVIDER_UNAVAILABLE", ["tenderly"]))
    r = live_b1.run_live_b1({
        "chain": "ethereum",
        "from": "0x1111111111111111111111111111111111111111",
        "to": "0x2222222222222222222222222222222222222222",
        "value": "0x0",
        "data": "0x",
    })
    assert r.engine_id == EngineId.B1
    assert r.status == AnalysisStatus.PARTIAL
    assert r.demo is False
    assert r.metrics["execution_success"] is True
    assert r.metrics["gas_estimate"] == 21000
    assert all(e.source_type != "demo" for e in r.evidence)
    assert "decoded internal call trace" in r.missing_data


def test_live_b1_revert_becomes_material_blocker(monkeypatch):
    fake = FakeRpc(revert=True)
    monkeypatch.setattr(live_b1, "select_rpc_client", lambda chain: _select(fake))
    monkeypatch.setattr(live_b1, "resolve_provider", lambda *a, **k: Resolution("simulation", None, "PROVIDER_UNAVAILABLE", ["tenderly"]))
    r = live_b1.run_live_b1({
        "chain": "1",
        "from": "0x1111111111111111111111111111111111111111",
        "to": "0x2222222222222222222222222222222222222222",
        "data": "0x",
    })
    assert r.risk_score >= 80
    assert r.hard_blockers
    assert r.metrics["execution_success"] is False


def test_live_b2_detects_unlimited_approval_without_claiming_malicious(monkeypatch):
    fake = FakeRpc()
    monkeypatch.setattr(live_b2, "select_rpc_client", lambda chain: _select(fake))
    monkeypatch.setattr(live_b2, "resolve_provider", lambda *a, **k: Resolution("security", None, "PROVIDER_UNAVAILABLE", ["blockaid", "hypernative"]))
    spender = "33" * 20
    amount = "f" * 64
    calldata = "0x095ea7b3" + ("0" * 24) + spender + amount
    r = live_b2.run_live_b2({
        "chain": "ethereum",
        "to": "0x2222222222222222222222222222222222222222",
        "data": calldata,
    })
    assert r.engine_id == EngineId.B2
    assert r.status == AnalysisStatus.PARTIAL
    assert r.metrics["approval"]["unlimited"] is True
    assert r.risk_score >= 50
    assert not r.hard_blockers
    assert any("cannot classify" in w.lower() for w in r.warnings)


def test_live_b5_normalizes_lifi_quote(monkeypatch):
    class FakeLifi:
        def quote(self, params):
            return ProviderCall("lifi","req-lifi","https://li.quest/v1/quote",{
                "id":"route-1","tool":"across","toolDetails":{"name":"Across"},
                "action":{
                    "fromChainId":1,"toChainId":42161,
                    "fromAmount":"1000000",
                    "fromAddress":"0x1111111111111111111111111111111111111111",
                    "toAddress":"0x1111111111111111111111111111111111111111",
                    "slippage":0.005,
                    "fromToken":{"symbol":"USDC","coinKey":"USDC"},
                    "toToken":{"symbol":"USDC","coinKey":"USDC"}
                },
                "estimate":{"fromAmount":"1000000","toAmount":"998000","toAmountMin":"993000","executionDuration":45,"gasCosts":[{"amountUSD":"1.25"}],"feeCosts":[{"amountUSD":"0.75"}],"approvalAddress":"0x4444444444444444444444444444444444444444"},
                "includedSteps":[{"id":"1"},{"id":"2"}]
            },11.5)
    monkeypatch.setattr(live_b1, "LifiClient", getattr(live_b1, "LifiClient", None), raising=False)
    from rivexis_api.services import live_b5
    monkeypatch.setattr(live_b5,"LifiClient",FakeLifi)
    r=live_b5.run_live_b5({"source_chain":1,"destination_chain":42161,"source_token":"USDC","destination_token":"USDC","amount":"1000000","wallet":"0x1111111111111111111111111111111111111111"})
    assert r.status==AnalysisStatus.PARTIAL and r.demo is False
    assert r.metrics["expected_to_amount"]=="998000"
    assert r.metrics["gas_cost_usd"]==1.25
    assert r.metrics["integrity"]["status"]=="MATCHED"
    assert r.evidence[0].provider=="lifi"


def test_live_f1_values_manual_positions(monkeypatch):
    from rivexis_api.services import live_f1
    class FakeCG:
        def simple_price(self,ids,vs_currency="usd"):
            from time import time
            now=int(time())
            return ProviderCall("coingecko","req-cg","https://api.coingecko.com/api/v3/simple/price",{
                "ethereum":{"usd":2500.0,"last_updated_at":now,"usd_24h_change":1.2},
                "bitcoin":{"usd":80000.0,"last_updated_at":now,"usd_24h_change":-0.4}
            },5.0)
    monkeypatch.setattr(live_f1,"CoinGeckoClient",FakeCG)
    r=live_f1.run_live_f1({"manual_positions":[{"coingecko_id":"ethereum","symbol":"ETH","quantity":2},{"coingecko_id":"bitcoin","symbol":"BTC","quantity":0.1}]})
    assert r.status==AnalysisStatus.PARTIAL
    assert r.metrics["portfolio_value_usd"]==13000.0
    assert len(r.metrics["positions"])==2
    assert any(e.provider=="coingecko" for e in r.evidence)


def test_live_f2_uses_defillama_as_external_evidence(monkeypatch):
    from rivexis_api.services import live_f2
    class FakeDL:
        def protocol(self,slug):
            return ProviderCall("defillama","req-dl","https://api.llama.fi/protocol/aave",{
                "name":"Aave","category":"Lending","chains":["Ethereum","Base"],"audits":"2","audit_links":["a","b"],"latestFetchIsOk":True,
                "tvl":[{"date":1,"totalLiquidityUSD":1000000000}]
            },7.0)
    monkeypatch.setattr(live_f2,"DefiLlamaClient",FakeDL)
    r=live_f2.run_live_f2({"protocol":"aave"})
    assert r.status==AnalysisStatus.PARTIAL
    assert r.metrics["tvl_usd"]==1000000000.0
    assert r.evidence[0].provider=="defillama"
    assert "direct smart-contract state and upgrade/admin privilege analysis" in r.missing_data


def test_live_b1_prefers_tenderly_when_configured(monkeypatch):
    fake = FakeRpc()
    monkeypatch.setattr(live_b1, "select_rpc_client", lambda chain: _select(fake))
    monkeypatch.setattr(live_b1, "resolve_provider", lambda *a, **k: Resolution("simulation", "tenderly", "RESOLVED", ["tenderly"]))
    class FakeTenderly:
        def simulate(self, chain, transaction, block_number=None):
            return ProviderCall("tenderly","req-tenderly","https://api.tenderly.co/simulate",{
                "simulation":{"id":"sim-1","network_id":"1","block_number":100},
                "transaction":{"status":True,"gas_used":21000,"logs":[]}
            },8.0)
    monkeypatch.setattr(live_b1,"TenderlyClient",FakeTenderly)
    r=live_b1.run_live_b1({"chain":"ethereum","from":"0x1111111111111111111111111111111111111111","to":"0x2222222222222222222222222222222222222222","data":"0x"})
    assert r.status==AnalysisStatus.PARTIAL
    assert r.metrics["execution_success"] is True
    assert any(e.provider=="tenderly" for e in r.evidence)
    assert "decoded internal call tree normalization" in r.missing_data


def test_live_b2_uses_etherscan_verification_when_available(monkeypatch):
    fake=FakeRpc()
    monkeypatch.setattr(live_b2,"select_rpc_client",lambda chain:_select(fake))
    monkeypatch.setattr(live_b2,"resolve_provider",lambda *a,**k:Resolution("security",None,"PROVIDER_UNAVAILABLE",["blockaid","hypernative"]))
    class FakeEtherscan:
        configured=True
        def get_source_code(self,chain,address):
            return ProviderCall("etherscan","req-es","https://api.etherscan.io/v2/api",{"status":"1","message":"OK","result":[{"SourceCode":"contract X{}","ABI":"[]","ContractName":"X","CompilerVersion":"v0.8.0","Proxy":"0","Implementation":""}]},4.0)
    monkeypatch.setattr(live_b2,"EtherscanClient",FakeEtherscan)
    r=live_b2.run_live_b2({"chain":"ethereum","to":"0x2222222222222222222222222222222222222222","data":"0x"})
    assert r.metrics["verified_source"] is True
    assert any(e.provider=="etherscan" for e in r.evidence)
    assert r.provider_consensus=="MULTI_SOURCE"


def test_live_f3_reads_chainlink_feed_and_models_liquidation(monkeypatch):
    from time import time
    from rivexis_api.services import live_f3
    def word(v): return hex(v if v>=0 else (1<<256)+v)[2:].rjust(64,'0')
    updated=int(time())
    round_data='0x'+''.join([word(10),word(2500_00000000),word(updated-5),word(updated),word(10)])
    class OracleRpc:
        def call(self,method,params=None):
            if method=='eth_chainId': return ProviderCall('direct_rpc','c','http://rpc','0x1',1)
            if method=='eth_blockNumber': return ProviderCall('direct_rpc','b','http://rpc','0x64',1)
            if method=='eth_call':
                data=params[0]['data']
                if data==live_f3.DECIMALS_SELECTOR:return ProviderCall('direct_rpc','d','http://rpc','0x'+word(8),1)
                if data==live_f3.LATEST_ROUND_DATA_SELECTOR:return ProviderCall('direct_rpc','r','http://rpc',round_data,1)
            raise AssertionError((method,params))
    rpc=OracleRpc();probe=rpc.call('eth_chainId')
    monkeypatch.setattr(live_f3,'select_rpc_client',lambda chain:('direct_rpc',rpc,probe,[]))
    r=live_f3.run_live_f3({
        'chain':'ethereum','collateral_price_feed':'0x2222222222222222222222222222222222222222',
        'collateral_units':1,'debt_units':1800,'debt_price_usd':1,'liquidation_threshold':0.8
    })
    assert r.status==AnalysisStatus.PARTIAL
    assert round(r.metrics['health_factor'],3)==1.111
    assert r.metrics['collateral_price_usd']==2500.0
    assert r.risk_score>=60
    assert any(e.source_type=='direct_oracle_state' for e in r.evidence)


def test_live_f4_uses_attributed_yield_data_without_calling_apy_safe(monkeypatch):
    from rivexis_api.services import live_f4

    class FakeYields:
        def pools(self):
            return ProviderCall(
                "defillama_yields",
                "req-yield",
                "https://yields.llama.fi/pools",
                {
                    "status": "success",
                    "data": [
                        {
                            "pool": "pool-a",
                            "project": "aave-v3",
                            "chain": "Ethereum",
                            "symbol": "USDC",
                            "tvlUsd": 125_000_000,
                            "apy": 8.0,
                            "apyBase": 3.0,
                            "apyReward": 5.0,
                            "apyMean30d": 6.5,
                            "sigma": 0.08,
                        }
                    ],
                },
                5.5,
            )

    monkeypatch.setattr(live_f4, "DefiLlamaYieldClient", FakeYields)
    r = live_f4.run_live_f4({"protocol": "aave", "asset": "USDC", "chain": "Ethereum"})
    assert r.engine_id == EngineId.F4
    assert r.status == AnalysisStatus.PARTIAL
    assert r.metrics["headline_apy_pct"] == 8.0
    assert r.metrics["reward_share"] == 0.625
    assert r.evidence[0].provider == "defillama_yields"
    assert all("safe" not in text.lower() for text in [r.summary, *r.warnings])
    assert "independent smart-contract/security evidence" in r.missing_data


def test_live_f5_treasury_screening_uses_current_market_refs(monkeypatch):
    from time import time
    from rivexis_api.services import live_f5

    class FakeCG:
        def simple_price(self, ids, vs_currency="usd"):
            now = int(time())
            return ProviderCall(
                "coingecko",
                "req-f5",
                "https://api.coingecko.com/api/v3/simple/price",
                {
                    "bitcoin": {"usd": 80000, "last_updated_at": now},
                    "ethereum": {"usd": 2500, "last_updated_at": now},
                    "usd-coin": {"usd": 1.0, "last_updated_at": now},
                },
                4.2,
            )

    monkeypatch.setattr(live_f5, "CoinGeckoClient", FakeCG)
    r = live_f5.run_live_f5({
        "capital_usd": 1_000_000,
        "max_concentration_pct": 35,
        "allocations": [
            {"coingecko_id": "bitcoin", "symbol": "BTC", "weight_pct": 30},
            {"coingecko_id": "ethereum", "symbol": "ETH", "weight_pct": 25},
            {"coingecko_id": "usd-coin", "symbol": "USDC", "weight_pct": 45, "stablecoin": True},
        ],
    })
    assert r.engine_id == EngineId.F5
    assert r.status == AnalysisStatus.PARTIAL
    assert round(r.metrics["largest_allocation_pct"], 1) == 45.0
    assert r.metrics["policy_violations"]
    assert r.metrics["scenario_losses_pct"]["broad_market_shock"] == 16.5
    assert r.evidence[0].provider == "coingecko"


def test_live_b4_preserves_unknown_identity_and_normalizes_fund_flow(monkeypatch):
    from rivexis_api.services import live_b4

    class B4Rpc:
        def call(self, method, params=None):
            if method == "eth_chainId": return ProviderCall("direct_rpc", "c", "http://rpc", "0x1", 1)
            if method == "eth_blockNumber": return ProviderCall("direct_rpc", "b", "http://rpc", "0x64", 1)
            if method == "eth_getBalance": return ProviderCall("direct_rpc", "bal", "http://rpc", hex(2 * 10**18), 1)
            raise AssertionError(method)
    rpc=B4Rpc();probe=rpc.call("eth_chainId")
    monkeypatch.setattr(live_b4,"select_rpc_client",lambda chain:("direct_rpc",rpc,probe,[]))

    class FakeES:
        configured=True
        def account_transactions(self, chain, address, **kwargs):
            return ProviderCall("etherscan","tx","https://api.etherscan.io/v2/api",{"status":"1","result":[
                {"from":address,"to":"0x2222222222222222222222222222222222222222","value":str(10**18)},
                {"from":"0x3333333333333333333333333333333333333333","to":address,"value":str(2*10**18)}
            ]},2)
        def token_transactions(self, chain, address, **kwargs):
            return ProviderCall("etherscan","tok","https://api.etherscan.io/v2/api",{"status":"1","result":[
                {"from":"0x4444444444444444444444444444444444444444","to":address,"value":"1000000","tokenDecimal":"6","tokenSymbol":"USDC","contractAddress":"0x5555555555555555555555555555555555555555"}
            ]},2)
    monkeypatch.setattr(live_b4,"EtherscanClient",FakeES)
    wallet="0x1111111111111111111111111111111111111111"
    r=live_b4.run_live_b4({"chain":"ethereum","wallet":wallet})
    assert r.status==AnalysisStatus.PARTIAL
    assert r.metrics["entity_profile"]["identity"]=="UNKNOWN ADDRESS"
    assert r.metrics["activity"]["native_net"]==1.0
    assert r.metrics["token_flows"][0]["net"]==1.0
    assert all(x["identity"]=="UNKNOWN ADDRESS" for x in r.metrics["top_counterparties"])
    assert r.provider_consensus=="MULTI_SOURCE"


def test_live_b3_snapshot_change_detection_is_non_demo(monkeypatch):
    from rivexis_api.services import live_b3

    class MonitorRpc:
        def __init__(self, balance: int, code: str):
            self.balance = balance
            self.code = code

        def call(self, method, params=None):
            if method == "eth_chainId":
                return ProviderCall("direct_rpc", "b3-chain", "http://rpc.test", "0x1", 1.0)
            if method == "eth_blockNumber":
                return ProviderCall("direct_rpc", "b3-block", "http://rpc.test", "0x65", 1.0)
            if method == "eth_getBalance":
                return ProviderCall("direct_rpc", "b3-bal", "http://rpc.test", hex(self.balance), 1.0)
            if method == "eth_getCode":
                return ProviderCall("direct_rpc", "b3-code", "http://rpc.test", self.code, 1.0)
            raise AssertionError((method, params))

    first_rpc = MonitorRpc(1_000, "0x6001")
    first_probe = first_rpc.call("eth_chainId")
    monkeypatch.setattr(live_b3, "select_rpc_client", lambda chain: ("direct_rpc", first_rpc, first_probe, []))
    first = live_b3.run_live_b3({"chain": "ethereum", "entity": "0x1111111111111111111111111111111111111111"})
    assert first.status == AnalysisStatus.PARTIAL
    assert first.demo is False
    assert first.metrics["signals_detected"] == 0
    assert "prior monitoring snapshot for change detection" in first.missing_data

    second_rpc = MonitorRpc(400, "0x6002")
    second_probe = second_rpc.call("eth_chainId")
    monkeypatch.setattr(live_b3, "select_rpc_client", lambda chain: ("direct_rpc", second_rpc, second_probe, []))
    second = live_b3.run_live_b3({
        "chain": "ethereum",
        "entity": "0x1111111111111111111111111111111111111111",
        "previous_snapshot": first.metrics["snapshot"],
        "balance_change_threshold_pct": 20,
    })
    assert second.status == AnalysisStatus.PARTIAL
    assert second.risk_score >= 80
    assert second.hard_blockers
    assert any(s["type"] == "large_native_balance_withdrawal" for s in second.signals)
    assert any(s["type"] == "runtime_bytecode_changed" for s in second.signals)


def test_live_b1_uses_verified_abi_to_decode_unknown_selector(monkeypatch):
    from rivexis_api.services.evm_decode import function_selector
    fake=FakeRpc()
    monkeypatch.setattr(live_b1,"select_rpc_client",lambda chain:_select(fake))
    monkeypatch.setattr(live_b1,"resolve_provider",lambda *a,**k:Resolution("simulation",None,"PROVIDER_UNAVAILABLE",["tenderly"]))
    target="0x3333333333333333333333333333333333333333"
    sig="allocate(address,uint256)"
    calldata=function_selector(sig)+("0"*24)+target[2:]+f"{777:064x}"
    class FakeEtherscan:
        configured=True
        def get_abi(self,chain,address):
            import json
            abi=[{"type":"function","name":"allocate","inputs":[{"name":"recipient","type":"address"},{"name":"amount","type":"uint256"}],"outputs":[]}]
            return ProviderCall("etherscan","abi-1","https://api.etherscan.io/v2/api",{"status":"1","message":"OK","result":json.dumps(abi)},3.0)
    monkeypatch.setattr(live_b1,"EtherscanClient",FakeEtherscan)
    r=live_b1.run_live_b1({"chain":"ethereum","from":"0x1111111111111111111111111111111111111111","to":"0x2222222222222222222222222222222222222222","data":calldata})
    assert r.metrics["calldata_decode"]["status"]=="DECODED_VERIFIED_ABI"
    assert r.metrics["calldata_decode"]["signature"]==sig
    assert any(e.source_type=="verified_contract_abi" for e in r.evidence)


def test_live_b1_optional_debug_trace_and_state_diff(monkeypatch):
    class TraceRpc(FakeRpc):
        def call(self,method,params=None):
            if method=="debug_traceCall":
                tracer=(params or [None,None,{}])[2].get("tracer")
                if tracer=="callTracer":
                    return ProviderCall("direct_rpc","trace-1","http://rpc.test",{"type":"CALL","from":"0x"+"11"*20,"to":"0x"+"22"*20,"value":"0x0","input":"0x","calls":[{"type":"CALL","from":"0x"+"22"*20,"to":"0x"+"33"*20,"value":"0x5","input":"0x"}]},3.0)
                if tracer=="prestateTracer":
                    return ProviderCall("direct_rpc","diff-1","http://rpc.test",{"pre":{"0x"+"22"*20:{"balance":"0x10","storage":{"0x01":"0x01"}}},"post":{"0x"+"22"*20:{"balance":"0x0f","storage":{"0x01":"0x02"}}}},4.0)
            return super().call(method,params)
    fake=TraceRpc()
    monkeypatch.setattr(live_b1,"select_rpc_client",lambda chain:_select(fake))
    monkeypatch.setattr(live_b1,"resolve_provider",lambda *a,**k:Resolution("simulation",None,"PROVIDER_UNAVAILABLE",["tenderly"]))
    r=live_b1.run_live_b1({"chain":"ethereum","from":"0x1111111111111111111111111111111111111111","to":"0x2222222222222222222222222222222222222222","data":"0x","trace":True,"state_diff":True})
    assert r.metrics["call_trace"]["call_count"]==2
    assert r.metrics["call_trace"]["native_value_transfers"][0]["amount_wei"]==5
    assert r.metrics["state_diff"]["addresses_changed"]==1
    assert any(e.source_type=="execution_trace" for e in r.evidence)
    assert any(e.source_type=="state_diff" for e in r.evidence)
