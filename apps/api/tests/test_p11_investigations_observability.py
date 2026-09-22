from __future__ import annotations

import re

import pytest

from rivexis_api.core.context import reset_trace_context, reset_workspace_id, set_trace_context, set_workspace_id
from rivexis_api.provider_clients import ProviderCall
from rivexis_api.services import protocol_adapters
from rivexis_api.services.evm_decode import function_selector
from rivexis_api.services.retention import apply_retention, policy
from rivexis_api.services.store import record_provider_request_event, trace_correlation


def word(value:int)->str:return hex(value & ((1<<256)-1))[2:].rjust(64,'0')
def address_word(address:str)->str:return address[2:].lower().rjust(64,'0')
def ret(*words:str)->str:return '0x'+''.join(words)


def auth_workspace(client,email='p11@example.com'):
    signup=client.post('/api/v1/auth/signup',json={'email':email,'password':'correct-horse-battery','role':'Analyst'})
    headers={'Authorization':'Bearer '+signup.json()['access_token']}
    workspace=client.post('/api/v1/workspaces',headers=headers,json={'name':'P11 Desk','role':'Analyst'}).json()
    return headers,workspace


def test_w3c_traceparent_is_preserved_and_audit_correlates(client):
    signup=client.post('/api/v1/auth/signup',json={'email':'trace@example.com','password':'correct-horse-battery','role':'Analyst'})
    headers={'Authorization':'Bearer '+signup.json()['access_token']}
    trace_id='1'*32;parent_span='2'*16;tp=f'00-{trace_id}-{parent_span}-01'
    created=client.post('/api/v1/workspaces',headers={**headers,'traceparent':tp},json={'name':'Trace Desk','role':'Analyst'})
    assert created.status_code==200
    assert created.headers['x-rivexis-trace-id']==trace_id
    assert re.fullmatch(rf'00-{trace_id}-[0-9a-f]{{16}}-01',created.headers['traceparent'])
    logs=client.get(f"/api/v1/workspaces/{created.json()['id']}/audit-logs",headers=headers).json()['items']
    event=next(x for x in logs if x['action']=='workspace.create')
    assert event['trace_id']==trace_id and len(event['span_id'])==16


def test_provider_request_trace_correlation_joins_audit_and_provider_events(client):
    headers,workspace=auth_workspace(client,'corr@example.com')
    from rivexis_api.services.store import audit
    wt=set_workspace_id(workspace['id']);tt=set_trace_context('a'*32,'b'*16)
    try:
        record_provider_request_event(workspace_id=workspace['id'],provider_key='direct_rpc',operation='eth_call',endpoint='rpc',status='SUCCESS',latency_ms=1.2,attempts=1,retries=0,estimated_cost_usd=0)
        audit('trace.test','workspace',workspace['id'],actor='corr@example.com',workspace_id=workspace['id'])
    finally:
        reset_trace_context(tt);reset_workspace_id(wt)
    out=trace_correlation(client.get('/api/v1/me',headers=headers).json()['id'],workspace['id'],'a'*32)
    assert len(out['provider_requests'])==1 and len(out['audit_events'])==1
    route=client.get(f"/api/v1/observability/traces/{'a'*32}?workspace_id={workspace['id']}",headers=headers)
    assert route.status_code==200 and route.json()['provider_requests'][0]['provider']=='direct_rpc'


def test_protocol_investigation_lifecycle_requires_disposition_and_attaches_review(client,monkeypatch):
    headers,workspace=auth_workspace(client,'investigate@example.com')
    from rivexis_api import main
    timeline={'adapter':'aave_v3','chain':'ethereum','from_block':100,'to_block':110,'event_count':1,'events':[{'block_number':105,'event':'BorrowCapChanged','category':'risk_parameter','transaction_hash':'0x'+'11'*32}]}
    review={'adapter':'aave_v3','chain':'ethereum','from_block':100,'to_block':110,'change_count':1,'materiality_counts':{'HIGH':1},'changes':[{'path':'reserve_configuration.borrow_cap','from':1,'to':2,'materiality':'HIGH'}],'before':{},'after':{}}
    monkeypatch.setattr(main,'protocol_event_timeline',lambda data:timeline)
    monkeypatch.setattr(main,'compare_protocol_configuration',lambda data:review)
    created=client.post('/api/v1/protocol-investigations',headers=headers,json={'workspace_id':workspace['id'],'title':'Borrow cap review','input':{'protocol_adapter':'aave_v3'},'notes':'investigate'})
    assert created.status_code==200 and created.json()['payload']['timeline']['event_count']==1
    case_id=created.json()['id']
    cfg=client.post('/api/v1/protocol-config/reviews',headers=headers,json={'workspace_id':workspace['id'],'input':{'protocol_adapter':'aave_v3'}}).json()
    attached=client.post(f"/api/v1/protocol-investigations/{case_id}/reviews/{cfg['id']}",headers=headers)
    assert attached.status_code==200 and cfg['id'] in attached.json()['payload']['review_ids']
    refused=client.patch(f'/api/v1/protocol-investigations/{case_id}',headers=headers,json={'status':'closed'})
    assert refused.status_code==422
    closed=client.patch(f'/api/v1/protocol-investigations/{case_id}',headers=headers,json={'status':'closed','disposition':'Parameter change reviewed; continue monitoring.','notes':'complete'})
    assert closed.status_code==200 and closed.json()['status']=='closed'
    pdf=client.get(f'/api/v1/protocol-investigations/{case_id}/render?format=pdf',headers=headers)
    assert pdf.status_code==200 and pdf.content.startswith(b'%PDF')


def test_retention_is_non_destructive_by_default(monkeypatch):
    monkeypatch.delenv('RIVEXIS_RETENTION_ALLOW_DELETE',raising=False)
    monkeypatch.delenv('RIVEXIS_RETENTION_ALLOW_REPORT_DELETE',raising=False)
    assert policy()['reports_days']==0
    with pytest.raises(PermissionError,match='disabled'):
        apply_retention()


def test_morpho_deep_dependency_economics_and_code_fingerprints():
    market_id='0x'+'ab'*32;loan='0x'+'11'*20;collateral='0x'+'22'*20;oracle='0x'+'33'*20
    irm='0x870ac11d48b15db9a138cf899d20f13f79ba00bc';feed='0x'+'44'*20;morpho='0xbbbbbbbbbb9cc5e90e3b3af64bdaf62c37eeffcb'
    class Rpc:
        def call(self,method,params=None):
            if method=='eth_getCode':return ProviderCall('direct_rpc','code','rpc','0x6001600055',1)
            if method=='eth_getBlockByNumber':return ProviderCall('direct_rpc','block','rpc',{'timestamp':'0x1000'},1)
            assert method=='eth_call';selector=params[0]['data'][:10]
            if selector==function_selector('idToMarketParams(bytes32)'):return ProviderCall('direct_rpc','p','rpc',ret(address_word(loan),address_word(collateral),address_word(oracle),address_word(irm),word(int(.86*10**18))),1)
            if selector==function_selector('market(bytes32)'):return ProviderCall('direct_rpc','m','rpc',ret(word(1000),word(1000),word(900),word(900),word(100),word(0)),1)
            if selector==function_selector('price()'):return ProviderCall('direct_rpc','price','rpc',ret(word(2*10**36)),1)
            if selector==function_selector('isIrmEnabled(address)'):return ProviderCall('direct_rpc','ie','rpc',ret(word(1)),1)
            if selector==function_selector('isMorphoChainlinkOracleV2(address)'):return ProviderCall('direct_rpc','of','rpc',ret(word(1)),1)
            if selector==function_selector('rateAtTarget(bytes32)'):return ProviderCall('direct_rpc','rat','rpc',ret(word(1268391679)),1)
            if selector==function_selector('MORPHO()'):return ProviderCall('direct_rpc','binding','rpc',ret(address_word(morpho)),1)
            if selector==function_selector('borrowRateView((address,address,address,address,uint256),(uint128,uint128,uint128,uint128,uint128,uint128))'):return ProviderCall('direct_rpc','br','rpc',ret(word(1268391679)),1)
            if selector==function_selector('decimals()'):return ProviderCall('direct_rpc','dec','rpc',ret(word(8)),1)
            if selector==function_selector('latestRoundData()'):return ProviderCall('direct_rpc','round','rpc',ret(word(1),word(2000_00000000),word(0),word(0x0ff0),word(1)),1)
            addr={function_selector('BASE_VAULT()'):'0x'+'00'*20,function_selector('BASE_FEED_1()'):feed,function_selector('BASE_FEED_2()'):'0x'+'00'*20,function_selector('QUOTE_VAULT()'):'0x'+'00'*20,function_selector('QUOTE_FEED_1()'):'0x'+'00'*20,function_selector('QUOTE_FEED_2()'):'0x'+'00'*20}
            if selector in addr:return ProviderCall('direct_rpc','addr','rpc',ret(address_word(addr[selector])),1)
            if selector in {function_selector('BASE_VAULT_CONVERSION_SAMPLE()'),function_selector('QUOTE_VAULT_CONVERSION_SAMPLE()')}:return ProviderCall('direct_rpc','sample','rpc',ret(word(1)),1)
            if selector==function_selector('SCALE_FACTOR()'):return ProviderCall('direct_rpc','scale','rpc',ret(word(10**36)),1)
            raise AssertionError((method,params))
    out=protocol_adapters.collect_protocol_adapter({'protocol_adapter':'morpho_blue','morpho_market_id':market_id},rpc=Rpc(),chain_id=1,block_number=100)
    dep=out.metrics['dependency_provenance']
    assert dep['irm_runtime_code']['code_present'] is True
    assert dep['oracle_runtime_code']['runtime_code_sha256']
    assert dep['irm_morpho_binding']['matches'] is True
    assert 3.9 < dep['borrow_rate_apr_percent'] < 4.1
    assert out.metrics['oracle_composition']['feed_health']['base_feed_1']['answer_raw']>0
