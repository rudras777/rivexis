from __future__ import annotations

from dataclasses import dataclass

from rivexis_api.models.enums import AnalysisStatus, FreshnessStatus
from rivexis_api.provider_clients import ProviderCall
from rivexis_api.providers import Resolution
from rivexis_api.services import live_b2, live_b3, live_b4


@dataclass
class FakeRpc:
    def call(self, method, params=None):
        if method == "eth_chainId":
            return ProviderCall("direct_rpc", "chain", "http://rpc", "0x1", 1)
        if method == "eth_blockNumber":
            return ProviderCall("direct_rpc", "block", "http://rpc", "0x64", 1)
        if method == "eth_getCode":
            return ProviderCall("direct_rpc", "code", "http://rpc", "0x6001", 1)
        if method == "eth_getBalance":
            return ProviderCall("direct_rpc", "bal", "http://rpc", hex(10**18), 1)
        if method == "eth_getTransactionByHash":
            return ProviderCall("direct_rpc", "tx", "http://rpc", None, 1)
        raise AssertionError((method, params))


def _select():
    rpc = FakeRpc()
    return "direct_rpc", rpc, rpc.call("eth_chainId"), []


def test_b2_consumes_malicious_blockaid_evidence(monkeypatch):
    monkeypatch.setattr(live_b2, "select_rpc_client", lambda chain: _select())
    monkeypatch.setattr(live_b2, "resolve_provider", lambda *a, **k: Resolution("security", "blockaid", "RESOLVED", ["blockaid"]))

    class NoES:
        configured = False

    class FakeBlockaid:
        def scan_transaction(self, **kwargs):
            return ProviderCall(
                "blockaid", "ba-1", "https://api.blockaid.io/v0/evm/transaction/scan",
                {"validation": {"status": "Success", "result_type": "Malicious", "features": [{"type": "Malicious", "feature_id": "DRAINER"}]},
                 "simulation": {"status": "Success", "transaction_actions": ["approval"], "exposures": {"x": []}}},
                7.0,
            )

    monkeypatch.setattr(live_b2, "EtherscanClient", NoES)
    monkeypatch.setattr(live_b2, "BlockaidClient", FakeBlockaid)
    r = live_b2.run_live_b2({
        "chain": "ethereum",
        "from": "0x1111111111111111111111111111111111111111",
        "to": "0x2222222222222222222222222222222222222222",
        "data": "0x",
    })
    assert r.status == AnalysisStatus.PARTIAL
    assert r.risk_score >= 90
    assert r.hard_blockers
    assert any(e.provider == "blockaid" for e in r.evidence)
    assert any(s.get("provider") == "blockaid" for s in r.signals)


def test_b2_blockaid_benign_is_evidence_not_safety_guarantee(monkeypatch):
    monkeypatch.setattr(live_b2, "select_rpc_client", lambda chain: _select())
    monkeypatch.setattr(live_b2, "resolve_provider", lambda *a, **k: Resolution("security", "blockaid", "RESOLVED", ["blockaid"]))

    class NoES:
        configured = False

    class FakeBlockaid:
        def scan_address(self, **kwargs):
            return ProviderCall("blockaid", "ba-2", "https://api.blockaid.io/v0/evm/address/scan", {"status": "Success", "result_type": "Benign", "features": []}, 3.0)

    monkeypatch.setattr(live_b2, "EtherscanClient", NoES)
    monkeypatch.setattr(live_b2, "BlockaidClient", FakeBlockaid)
    r = live_b2.run_live_b2({"chain": "ethereum", "address": "0x2222222222222222222222222222222222222222"})
    assert not r.hard_blockers
    assert any("not interpret this as a guarantee" in w for w in r.warnings)
    assert r.provider_consensus == "MULTI_SOURCE"


def test_b3_consumes_blockaid_address_screening_without_claiming_streaming(monkeypatch):
    monkeypatch.setattr(live_b3, "select_rpc_client", lambda chain: _select())
    monkeypatch.setattr(live_b3, "resolve_provider", lambda *a, **k: Resolution("threat", "blockaid", "RESOLVED", ["blockaid"]))

    class FakeBlockaid:
        def scan_address(self, **kwargs):
            return ProviderCall("blockaid", "ba-b3", "https://api.blockaid.io/v0/evm/address/scan", {"status": "Success", "result_type": "Warning", "features": [{"type": "Warning", "feature_id": "SUSPICIOUS"}]}, 4.0)

    monkeypatch.setattr(live_b3, "BlockaidClient", FakeBlockaid)
    r = live_b3.run_live_b3({"chain": "ethereum", "entity": "0x1111111111111111111111111111111111111111"})
    assert any(e.provider == "blockaid" for e in r.evidence)
    assert r.risk_score >= 35
    assert any("point-in-time" in x for x in r.missing_data)
    blockaid = next(e for e in r.evidence if e.provider == "blockaid")
    assert blockaid.block_number is None
    assert blockaid.freshness == FreshnessStatus.UNKNOWN
    assert r.data_freshness["status"] == FreshnessStatus.UNKNOWN.value
    assert r.data_freshness["direct_state"] == FreshnessStatus.LIVE.value
    assert r.data_freshness["external_threat_intelligence"] == FreshnessStatus.UNKNOWN.value


def test_b3_rejects_empty_blockaid_payload_as_unavailable(monkeypatch):
    monkeypatch.setattr(live_b3, "select_rpc_client", lambda chain: _select())
    monkeypatch.setattr(
        live_b3,
        "resolve_provider",
        lambda *a, **k: Resolution(
            "threat", "blockaid", "RESOLVED", ["blockaid"]
        ),
    )

    class EmptyBlockaid:
        def scan_address(self, **kwargs):
            return ProviderCall(
                "blockaid",
                "ba-empty",
                "https://api.blockaid.io/v0/evm/address/scan",
                {},
                4.0,
            )

    monkeypatch.setattr(live_b3, "BlockaidClient", EmptyBlockaid)
    result = live_b3.run_live_b3(
        {
            "chain": "ethereum",
            "entity": "0x1111111111111111111111111111111111111111",
        }
    )

    assert not any(e.provider == "blockaid" for e in result.evidence)
    assert "Blockaid external threat intelligence" in result.missing_data
    assert any(
        row.get("provider_id") == "blockaid"
        and row.get("status") == "MALFORMED_RESPONSE"
        for row in result.provider_status
    )


def _b4_base(monkeypatch):
    monkeypatch.setattr(live_b4, "select_rpc_client", lambda chain: _select())

    class NoES:
        configured = False
    monkeypatch.setattr(live_b4, "EtherscanClient", NoES)


def test_b4_uses_nansen_label_with_provenance(monkeypatch):
    _b4_base(monkeypatch)

    class FakeNansen:
        configured = True
        def address_labels(self, **kwargs):
            return ProviderCall("nansen", "nan-1", "https://api.nansen.ai/api/v1/profiler/address/labels", {"data": [{"label": "Example Treasury", "category": "Fund"}]}, 5.0)

    class NoArkham:
        credentialed = False
        configured = False
        license_approved = False

    monkeypatch.setattr(live_b4, "NansenClient", FakeNansen)
    monkeypatch.setattr(live_b4, "ArkhamClient", NoArkham)
    r = live_b4.run_live_b4({"chain": "ethereum", "wallet": "0x1111111111111111111111111111111111111111"})
    assert r.metrics["entity_profile"]["identity"] == "Example Treasury"
    assert r.metrics["entity_profile"]["identity_provenance"][0]["provider"] == "nansen"
    assert any(e.provider == "nansen" for e in r.evidence)


def test_b4_surfaces_nansen_arkham_identity_conflict(monkeypatch):
    _b4_base(monkeypatch)

    class FakeNansen:
        configured = True
        def address_labels(self, **kwargs):
            return ProviderCall("nansen", "nan-2", "nansen", {"data": [{"label": "Entity A"}]}, 2.0)

    class FakeArkham:
        credentialed = True
        configured = True
        license_approved = True
        def address_intelligence(self, address):
            return ProviderCall("arkham", "ark-1", "arkham", {"entity": {"name": "Entity B", "id": "b"}, "label": "Entity B Hot"}, 2.0)

    monkeypatch.setattr(live_b4, "NansenClient", FakeNansen)
    monkeypatch.setattr(live_b4, "ArkhamClient", FakeArkham)
    r = live_b4.run_live_b4({"chain": "ethereum", "wallet": "0x1111111111111111111111111111111111111111"})
    assert r.metrics["entity_profile"]["identity"] == "CONFLICTING EXTERNAL LABELS"
    assert r.provider_consensus == "CONFLICTING"
    assert r.provider_conflicts and r.provider_conflicts[0].metric == "entity_identity"


def test_b4_arkham_credentials_do_not_bypass_license_gate(monkeypatch):
    _b4_base(monkeypatch)

    class NoNansen:
        configured = False

    class LicenseBlockedArkham:
        credentialed = True
        configured = False
        license_approved = False

    monkeypatch.setattr(live_b4, "NansenClient", NoNansen)
    monkeypatch.setattr(live_b4, "ArkhamClient", LicenseBlockedArkham)
    r = live_b4.run_live_b4({"chain": "ethereum", "wallet": "0x1111111111111111111111111111111111111111"})
    assert any(x.get("provider_id") == "arkham" and x.get("status") == "LICENSE_APPROVAL_REQUIRED" for x in r.provider_status)
    assert r.metrics["entity_profile"]["identity"] == "UNKNOWN ADDRESS"


def test_protocol_native_collects_verified_contract_proxy_and_declared_oracle(monkeypatch):
    from time import time
    from rivexis_api.services import protocol_native

    def word(v):
        return hex(v if v >= 0 else (1 << 256) + v)[2:].rjust(64, "0")

    updated = int(time())
    round_data = "0x" + "".join([word(10), word(2500_00000000), word(updated - 2), word(updated), word(10)])

    class NativeRpc:
        def call(self, method, params=None):
            if method == "eth_chainId": return ProviderCall("direct_rpc", "n-chain", "rpc", "0x1", 1)
            if method == "eth_blockNumber": return ProviderCall("direct_rpc", "n-block", "rpc", "0x64", 1)
            if method == "eth_getCode": return ProviderCall("direct_rpc", "n-code", "rpc", "0x6001600055", 1)
            if method == "eth_getStorageAt":
                slot = params[1]
                if slot == protocol_native.EIP1967_IMPLEMENTATION_SLOT:
                    return ProviderCall("direct_rpc", "n-impl", "rpc", "0x" + ("0" * 24) + ("9" * 40), 1)
                if slot == protocol_native.EIP1967_ADMIN_SLOT:
                    return ProviderCall("direct_rpc", "n-admin", "rpc", "0x" + ("0" * 24) + ("8" * 40), 1)
                return ProviderCall("direct_rpc", "n-slot", "rpc", "0x" + ("0" * 64), 1)
            if method == "eth_call":
                selector = params[0]["data"]
                if selector == protocol_native.DECIMALS_SELECTOR:
                    return ProviderCall("direct_rpc", "n-dec", "rpc", "0x" + word(8), 1)
                if selector == protocol_native.LATEST_ROUND_DATA_SELECTOR:
                    return ProviderCall("direct_rpc", "n-round", "rpc", round_data, 1)
            raise AssertionError((method, params))

    rpc = NativeRpc()
    monkeypatch.setattr(protocol_native, "select_rpc_client", lambda chain: ("direct_rpc", rpc, rpc.call("eth_chainId"), []))

    class FakeES:
        configured = True
        def get_source_code(self, chain, address):
            return ProviderCall("etherscan", "src", "etherscan", {"status":"1","result":[{"SourceCode":"contract P{}","ABI":"[]","ContractName":"P","Proxy":"1","Implementation":"0x9999999999999999999999999999999999999999"}]}, 2)
    monkeypatch.setattr(protocol_native, "EtherscanClient", FakeES)

    out = protocol_native.collect_protocol_native({
        "chain": "ethereum",
        "protocol_contracts": [{"address":"0x2222222222222222222222222222222222222222","role":"core_protocol"}],
        "protocol_oracle_feed": "0x3333333333333333333333333333333333333333",
    })
    assert out.metrics["declared_contracts"][0]["verified_source"] is True
    assert out.metrics["declared_contracts"][0]["proxy"] is True
    assert out.metrics["declared_contracts"][0]["eip1967"]["implementation"] == "0x" + ("9" * 40)
    assert out.metrics["declared_contracts"][0]["eip1967"]["admin"] == "0x" + ("8" * 40)
    assert out.metrics["declared_oracle"]["answer"] == 2500.0
    assert out.risk_delta >= 16
    assert {e.provider for e in out.evidence} == {"direct_rpc", "etherscan"}


def test_f2_incorporates_protocol_native_evidence(monkeypatch):
    from rivexis_api.services import live_f2
    from rivexis_api.services.protocol_native import ProtocolNativeResult
    from rivexis_api.chains import normalize_chain

    class FakeDL:
        def protocol(self, slug):
            return ProviderCall("defillama", "dl-p5", "defillama", {"name":"Protocol","chains":["Ethereum"],"audits":"1","tvl":[{"totalLiquidityUSD":50_000_000}]}, 2)
    monkeypatch.setattr(live_f2, "DefiLlamaClient", FakeDL)
    monkeypatch.setattr(live_f2, "has_protocol_native_input", lambda data: True)
    monkeypatch.setattr(live_f2, "collect_protocol_native", lambda data: ProtocolNativeResult(
        chain=normalize_chain("ethereum"), metrics={"declared_contracts":[{"role":"governance"}],"declared_oracle":{"answer":1}}, risk_delta=12, confidence=88,
        warnings=["proxy review"], missing_data=[], assumptions=["caller-declared roles"],
    ))
    r = live_f2.run_live_f2({"protocol":"protocol","chain":"ethereum","governance_contract":"0x2222222222222222222222222222222222222222"})
    assert "protocol_native" in r.metrics
    assert r.risk_score >= 32
    assert r.data_confidence >= 88
    assert any("governance concentration" not in x for x in r.missing_data)


def test_f4_incorporates_declared_protocol_native_evidence(monkeypatch):
    from rivexis_api.services import live_f4
    from rivexis_api.services.protocol_native import ProtocolNativeResult
    from rivexis_api.chains import normalize_chain

    class FakeYields:
        def pools(self):
            return ProviderCall("defillama_yields","yield-p5","yields",{"data":[{"pool":"p","project":"proto","chain":"Ethereum","symbol":"USDC","tvlUsd":10_000_000,"apy":4,"apyBase":4,"apyReward":0}]},2)
    monkeypatch.setattr(live_f4,"DefiLlamaYieldClient",FakeYields)
    monkeypatch.setattr(live_f4,"has_protocol_native_input",lambda data:True)
    monkeypatch.setattr(live_f4,"collect_protocol_native",lambda data:ProtocolNativeResult(chain=normalize_chain("ethereum"),metrics={"declared_contracts":[{"role":"vault"}],"declared_oracle":None},risk_delta=5,confidence=85))
    r=live_f4.run_live_f4({"protocol":"proto","asset":"USDC","chain":"Ethereum","vault_address":"0x2222222222222222222222222222222222222222"})
    assert "protocol_native" in r.metrics
    assert r.engine_version=="1.2.0"
    assert r.data_confidence>=85


def test_f5_incorporates_multiple_declared_protocol_native_checks(monkeypatch):
    from rivexis_api.services import live_f5
    from rivexis_api.services.protocol_native import ProtocolNativeResult
    from rivexis_api.chains import normalize_chain

    class FakeCG:
        def simple_price(self, ids, vs_currency="usd"):
            return ProviderCall("coingecko","cg-p5","cg",{"ethereum":{"usd":2500,"last_updated_at":1}},2)
    monkeypatch.setattr(live_f5,"CoinGeckoClient",FakeCG)
    monkeypatch.setattr(live_f5,"has_protocol_native_input",lambda data: bool(data.get("protocol_contracts")))
    monkeypatch.setattr(live_f5,"collect_protocol_native",lambda data:ProtocolNativeResult(chain=normalize_chain("ethereum"),metrics={"declared_contracts":[{"role":"dependency"}]},risk_delta=4,confidence=80))
    r=live_f5.run_live_f5({
        "allocations":[{"coingecko_id":"ethereum","symbol":"ETH","weight_pct":100}],
        "protocol_native_checks":[
            {"chain":"ethereum","protocol_contracts":["0x2222222222222222222222222222222222222222"]},
            {"chain":"ethereum","protocol_contracts":["0x3333333333333333333333333333333333333333"]},
        ],
    })
    assert len(r.metrics["protocol_native_checks"])==2
    assert r.engine_version=="1.2.0"
    assert r.data_confidence>=80


def _provision_monitor(client, email: str):
    signup = client.post('/api/v1/auth/signup', json={"email": email, "password": "correct-horse-battery", "role": "Analyst"})
    assert signup.status_code == 200
    headers = {"Authorization": "Bearer " + signup.json()["access_token"]}
    workspace = client.post('/api/v1/workspaces', headers=headers, json={"name": "Threat Desk", "role": "Analyst"})
    assert workspace.status_code == 200
    monitor = client.post('/api/v1/monitors', headers=headers, json={
        "workspace_id": workspace.json()["id"],
        "entity": "0x1111111111111111111111111111111111111111",
        "chain": "ethereum",
        "rules": ["external-threat"],
    })
    assert monitor.status_code == 200
    return headers, workspace.json(), monitor.json()


def test_hypernative_ingress_requires_rivexis_secret_and_persists_attributed_alert(client, monkeypatch):
    headers, workspace, monitor = _provision_monitor(client, "hypernative-owner@example.com")
    body = {
        "workspace_id": workspace["id"],
        "monitor_id": monitor["id"],
        "event_type": "customer_forwarded_threat_event",
        "severity": "high",
        "affected_entity": monitor["entity"],
        "confidence": 91,
        "observed_at": "2026-09-11T10:00:00Z",
        "provider_payload": {"source_event_id": "hn-demo-id", "classification": "anomaly"},
    }
    monkeypatch.delenv("HYPERNATIVE_WEBHOOK_SECRET", raising=False)
    assert client.post('/api/v1/integrations/hypernative/events', json=body).status_code == 503

    monkeypatch.setenv("HYPERNATIVE_WEBHOOK_SECRET", "staging-forwarder-secret")
    assert client.post('/api/v1/integrations/hypernative/events', json=body, headers={"X-Rivexis-Webhook-Secret": "wrong"}).status_code == 401

    accepted = client.post('/api/v1/integrations/hypernative/events', json=body, headers={"X-Rivexis-Webhook-Secret": "staging-forwarder-secret"})
    assert accepted.status_code == 202
    assert accepted.json()["provider_native_signature_verified"] is False
    alerts = client.get('/api/v1/alerts', headers=headers, params={"workspace_id": workspace["id"]})
    assert alerts.status_code == 200
    stored = next(x for x in alerts.json()["items"] if x["id"] == accepted.json()["alert_id"])
    assert stored["payload"]["provider"] == "hypernative"
    assert stored["payload"]["ingress_authentication"] == "rivexis_shared_secret"
    assert stored["severity"] == "high"


def test_hypernative_ingress_rejects_monitor_workspace_mismatch(client, monkeypatch):
    _, workspace_a, monitor_a = _provision_monitor(client, "hypernative-a@example.com")
    _, workspace_b, _ = _provision_monitor(client, "hypernative-b@example.com")
    monkeypatch.setenv("HYPERNATIVE_WEBHOOK_SECRET", "staging-forwarder-secret")
    body = {
        "workspace_id": workspace_b["id"],
        "monitor_id": monitor_a["id"],
        "event_type": "mismatched_workspace",
        "provider_payload": {},
    }
    r = client.post('/api/v1/integrations/hypernative/events', json=body, headers={"X-Rivexis-Webhook-Secret": "staging-forwarder-secret"})
    assert r.status_code == 404


def test_protocol_native_governance_declaration_is_low_confidence_and_risk_adjusting(monkeypatch):
    from rivexis_api.services import protocol_native

    class Rpc:
        def call(self, method, params=None):
            if method == "eth_chainId": return ProviderCall("direct_rpc", "g-chain", "rpc", "0x1", 1)
            if method == "eth_blockNumber": return ProviderCall("direct_rpc", "g-block", "rpc", "0x64", 1)
            raise AssertionError((method, params))

    rpc = Rpc()
    monkeypatch.setattr(protocol_native, "select_rpc_client", lambda chain: ("direct_rpc", rpc, rpc.call("eth_chainId"), []))
    class NoES:
        configured = False
    monkeypatch.setattr(protocol_native, "EtherscanClient", NoES)

    out = protocol_native.collect_protocol_native({
        "chain": "ethereum",
        "protocol_oracle_feed": None,
        "governance_metadata": {
            "timelock_seconds": 0,
            "upgrade_delay_seconds": 300,
            "multisig_threshold": 1,
            "multisig_signers": 3,
            "emergency_admin_count": 1,
            "can_pause": True,
        },
    })
    assert out.metrics["declared_governance"]["timelock_seconds"] == 0
    assert out.risk_delta >= 30
    assert out.confidence == 45
    assert "direct protocol-native contract/oracle evidence" in out.missing_data


def test_governance_declaration_applies_when_protocol_native_contract_is_declared(monkeypatch):
    from rivexis_api.services import protocol_native

    class Rpc:
        def call(self, method, params=None):
            if method == "eth_chainId": return ProviderCall("direct_rpc", "g2-chain", "rpc", "0x1", 1)
            if method == "eth_blockNumber": return ProviderCall("direct_rpc", "g2-block", "rpc", "0x64", 1)
            if method == "eth_getCode": return ProviderCall("direct_rpc", "g2-code", "rpc", "0x", 1)
            raise AssertionError((method, params))
    rpc=Rpc()
    monkeypatch.setattr(protocol_native,"select_rpc_client",lambda chain:("direct_rpc",rpc,rpc.call("eth_chainId"),[]))
    class NoES:
        configured=False
    monkeypatch.setattr(protocol_native,"EtherscanClient",NoES)
    out=protocol_native.collect_protocol_native({
        "chain":"ethereum",
        "governance_contract":"0x2222222222222222222222222222222222222222",
        "governance_metadata":{
            "timelock_seconds":0,
            "upgrade_delay_seconds":300,
            "multisig_threshold":1,
            "multisig_signers":3,
            "emergency_admin_count":1,
            "can_pause":True,
        },
    })
    assert out.metrics["declared_governance"]["timelock_seconds"] == 0
    assert out.risk_delta >= 30
    gov_evidence=[e for e in out.evidence if e.source_type=="declared_governance_metadata"]
    assert len(gov_evidence)==1
    assert gov_evidence[0].provider=="user_input"
    assert gov_evidence[0].confidence==45
    assert any("caller-declared" in x.lower() for x in out.assumptions)


def test_hypernative_ingress_is_idempotent_for_replayed_provider_event(client, monkeypatch):
    headers, workspace, monitor = _provision_monitor(client, "hypernative-replay@example.com")
    monkeypatch.setenv("HYPERNATIVE_WEBHOOK_SECRET", "staging-forwarder-secret")
    body = {
        "workspace_id": workspace["id"],
        "monitor_id": monitor["id"],
        "event_type": "customer_forwarded_threat_event",
        "severity": "critical",
        "affected_entity": monitor["entity"],
        "confidence": 99,
        "observed_at": "2026-09-11T10:05:00Z",
        "provider_payload": {"source_event_id": "hn-replay-001", "classification": "exploit"},
    }
    first = client.post('/api/v1/integrations/hypernative/events', json=body, headers={"X-Rivexis-Webhook-Secret": "staging-forwarder-secret"})
    second = client.post('/api/v1/integrations/hypernative/events', json=body, headers={"X-Rivexis-Webhook-Secret": "staging-forwarder-secret"})
    assert first.status_code == second.status_code == 202
    assert first.json()["duplicate"] is False
    assert second.json()["duplicate"] is True
    assert first.json()["alert_id"] == second.json()["alert_id"]
    alerts = client.get('/api/v1/alerts', headers=headers, params={"workspace_id": workspace["id"]})
    matching = [x for x in alerts.json()["items"] if x.get("external_event_key") == "hn-replay-001"]
    assert len(matching) == 1
    assert matching[0]["provider_id"] == "hypernative"
