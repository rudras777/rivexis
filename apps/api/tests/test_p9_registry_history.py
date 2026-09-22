from __future__ import annotations

from copy import deepcopy

import pytest

from rivexis_api.provider_clients import ProviderCall
from rivexis_api.services import protocol_history
from rivexis_api.services.protocol_adapters import ProtocolAdapterResult
from rivexis_api.services.registry_governance import (
    approve_update_plan, prepare_update_plan, registry_fingerprint, registry_payload, verify_approved_plan,
)


def word(value: int) -> str:
    return hex(value)[2:].rjust(64, "0")


def topic_address(address: str) -> str:
    return "0x" + address[2:].lower().rjust(64, "0")


def test_registry_update_requires_version_bump_and_explicit_approval():
    current = registry_payload()
    assert len(registry_fingerprint()) == 64
    no_change = prepare_update_plan(deepcopy(current))
    assert no_change["status"] == "NO_CHANGE"

    proposed = deepcopy(current)
    proposed["records"][0]["contracts"]["pool"] = "0x0000000000000000000000000000000000000001"
    with pytest.raises(ValueError, match="version was not bumped"):
        prepare_update_plan(proposed)

    proposed["registry_version"] = current["registry_version"] + "-reviewed-1"
    plan = prepare_update_plan(proposed)
    assert plan["status"] == "PENDING_APPROVAL"
    with pytest.raises(ValueError, match="not explicitly approved"):
        verify_approved_plan(plan)
    approved = approve_update_plan(plan, reviewer="security-reviewer", approval_id="RVX-REG-001")
    assert verify_approved_plan(approved) is True
    assert approved["approval"]["base_fingerprint"] == registry_fingerprint()


def test_registry_approval_detects_tampering():
    proposed = registry_payload()
    proposed["registry_version"] = proposed["registry_version"] + "-next"
    proposed["records"][0]["source"] = "Reviewed source metadata change"
    approved = approve_update_plan(prepare_update_plan(proposed), reviewer="reviewer", approval_id="A-1")
    approved["proposed"]["records"][0]["source"] = "tampered"
    with pytest.raises(ValueError, match="proposed fingerprint"):
        verify_approved_plan(approved)


def test_aave_history_decodes_borrow_cap_change(monkeypatch):
    asset = "0x2222222222222222222222222222222222222222"
    log = {
        "address": "0x64b761d848206f447fe2dd461b0c635ec39ebb27",
        "topics": [protocol_history.event_topic("BorrowCapChanged(address,uint256,uint256)"), topic_address(asset)],
        "data": "0x" + word(1000) + word(1500),
        "blockNumber": "0x63", "transactionHash": "0x" + "11" * 32, "logIndex": "0x2", "removed": False,
    }

    class Rpc:
        def call(self, method, params=None):
            if method == "eth_blockNumber": return ProviderCall("direct_rpc", "head", "rpc", "0x64", 1)
            if method == "eth_getLogs": return ProviderCall("direct_rpc", "logs", "rpc", [log], 1)
            raise AssertionError((method, params))

    rpc = Rpc()
    monkeypatch.setattr(protocol_history, "select_rpc_client", lambda chain: ("direct_rpc", rpc, ProviderCall("direct_rpc", "probe", "rpc", "0x1", 1), []))
    out = protocol_history.protocol_event_timeline({"chain":"ethereum","protocol_adapter":"aave_v3","from_block":90,"to_block":100,"asset_address":asset})
    assert out["event_count"] == 1
    assert out["events"][0]["event"] == "BorrowCapChanged"
    assert out["events"][0]["parameters"] == {"asset": asset, "old_borrow_cap": 1000, "new_borrow_cap": 1500}


def test_compound_history_decodes_governor_change(monkeypatch):
    comet = "0xc3d688b66703497daa19211eedff47f25384cdc3"
    old = "0x1111111111111111111111111111111111111111"
    new = "0x2222222222222222222222222222222222222222"
    config_log = {
        "address":"0x316f9708bb98af7da9c68c1c3b5e79039cd336e3",
        "topics":[protocol_history.event_topic("SetGovernor(address,address,address)"), topic_address(comet), topic_address(old), topic_address(new)],
        "data":"0x", "blockNumber":"0x62", "transactionHash":"0x"+"22"*32, "logIndex":"0x0", "removed":False,
    }
    class Rpc:
        def call(self, method, params=None):
            if method == "eth_blockNumber": return ProviderCall("direct_rpc","head","rpc","0x64",1)
            if method == "eth_getLogs":
                address = params[0]["address"].lower()
                rows = [config_log] if address == config_log["address"] else []
                return ProviderCall("direct_rpc","logs-"+address[-4:],"rpc",rows,1)
            raise AssertionError((method,params))
    rpc=Rpc()
    monkeypatch.setattr(protocol_history,"select_rpc_client",lambda chain:("direct_rpc",rpc,ProviderCall("direct_rpc","probe","rpc","0x1",1),[]))
    out=protocol_history.protocol_event_timeline({"chain":"ethereum","protocol_adapter":"compound_v3","compound_market":"usdc","from_block":90,"to_block":100})
    assert out["event_count"] == 1
    assert out["events"][0]["event"] == "SetGovernor"
    assert out["events"][0]["parameters"]["new_governor"] == new


def test_configuration_compare_marks_liquidation_change_high(monkeypatch):
    class Rpc:
        def call(self, method, params=None):
            if method == "eth_blockNumber": return ProviderCall("direct_rpc","head","rpc","0xc8",1)
            raise AssertionError((method,params))
    rpc=Rpc()
    monkeypatch.setattr(protocol_history,"select_rpc_client",lambda chain:("direct_rpc",rpc,ProviderCall("direct_rpc","probe","rpc","0x1",1),[]))
    def fake_collect(data, **kwargs):
        block=int(data["at_block"])
        threshold=8000 if block==100 else 7800
        return ProtocolAdapterResult(adapter="aave_v3",metrics={"adapter":"aave_v3","reserve_configuration":{"liquidation_threshold_bps":threshold,"ltv_bps":7500},"block_tag":hex(block),"read_block_number":block},confidence=99)
    monkeypatch.setattr(protocol_history,"collect_protocol_adapter",fake_collect)
    out=protocol_history.compare_protocol_configuration({"chain":"ethereum","protocol_adapter":"aave_v3","from_block":100,"to_block":150})
    row=next(r for r in out["changes"] if r["path"].endswith("liquidation_threshold_bps"))
    assert row["from"] == 8000 and row["to"] == 7800 and row["materiality"] == "HIGH"
    assert out["materiality_counts"]["HIGH"] == 1


def test_protocol_operational_endpoints_require_auth_and_workspace(client, monkeypatch):
    assert client.post("/api/v1/protocol-history/timeline", json={"input":{}}).status_code == 401
    signup=client.post('/api/v1/auth/signup',json={"email":"p9@example.com","password":"correct-horse-battery","role":"Analyst"})
    headers={"Authorization":"Bearer "+signup.json()["access_token"]}
    workspace=client.post('/api/v1/workspaces',headers=headers,json={"name":"P9 Desk","role":"Analyst"}).json()
    from rivexis_api import main
    monkeypatch.setattr(main,"protocol_event_timeline",lambda data:{"event_count":0,"events":[]})
    monkeypatch.setattr(main,"compare_protocol_configuration",lambda data:{"change_count":0,"changes":[]})
    body={"workspace_id":workspace["id"],"input":{"protocol_adapter":"aave_v3"}}
    assert client.post("/api/v1/protocol-history/timeline",headers=headers,json=body).status_code == 200
    assert client.post("/api/v1/protocol-config/compare",headers=headers,json=body).status_code == 200
