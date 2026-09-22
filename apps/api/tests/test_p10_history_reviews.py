from __future__ import annotations
from rivexis_api.provider_clients import ProviderCall, ProviderError
from rivexis_api.services import protocol_history


def word(value:int)->str:return hex(value)[2:].rjust(64,'0')
def topic_address(address:str)->str:return '0x'+address[2:].lower().rjust(64,'0')


def test_history_adapts_chunk_size_and_hydrates_timestamp(monkeypatch):
    asset='0x2222222222222222222222222222222222222222'
    log={
        'address':'0x64b761d848206f447fe2dd461b0c635ec39ebb27',
        'topics':[protocol_history.event_topic('BorrowCapChanged(address,uint256,uint256)'),topic_address(asset)],
        'data':'0x'+word(1)+word(2),'blockNumber':'0x63','transactionHash':'0x'+'ab'*32,'logIndex':'0x1','removed':False,
    }
    class Rpc:
        def call(self,method,params=None):
            if method=='eth_blockNumber':return ProviderCall('direct_rpc','head','rpc','0x64',1)
            if method=='eth_getLogs':
                f=params[0]; a=int(f['fromBlock'],16); b=int(f['toBlock'],16)
                if b-a+1>3: raise ProviderError('too many blocks',provider_id='direct_rpc',code='RPC_-32005',retryable=True)
                rows=[log] if a<=99<=b else []
                return ProviderCall('direct_rpc',f'logs-{a}-{b}','rpc',rows,1)
            if method=='eth_getBlockByNumber':
                return ProviderCall('direct_rpc','block-99','rpc',{'timestamp':'0x66e2ff80'},1)
            raise AssertionError((method,params))
    rpc=Rpc(); monkeypatch.setenv('RIVEXIS_PROTOCOL_HISTORY_MIN_CHUNK_BLOCKS','1')
    monkeypatch.setattr(protocol_history,'select_rpc_client',lambda chain:('direct_rpc',rpc,ProviderCall('direct_rpc','probe','rpc','0x1',1),[]))
    out=protocol_history.protocol_event_timeline({'chain':'ethereum','protocol_adapter':'aave_v3','from_block':90,'to_block':100,'asset_address':asset,'log_chunk_blocks':8,'hydrate_timestamps':True})
    assert out['event_count']==1
    assert out['events'][0]['block_datetime'].endswith('+00:00')
    assert out['log_fetch']['targets'][0]['adaptive_reductions']>=1
    assert out['log_fetch']['timestamp_request_count']==1


def test_removed_history_log_excluded_by_default(monkeypatch):
    asset='0x2222222222222222222222222222222222222222'
    log={'address':'0x64b761d848206f447fe2dd461b0c635ec39ebb27','topics':[protocol_history.event_topic('BorrowCapChanged(address,uint256,uint256)'),topic_address(asset)],'data':'0x'+word(1)+word(2),'blockNumber':'0x63','transactionHash':'0x'+'cd'*32,'logIndex':'0x1','removed':True}
    class Rpc:
        def call(self,method,params=None):
            if method=='eth_blockNumber':return ProviderCall('direct_rpc','head','rpc','0x64',1)
            if method=='eth_getLogs':return ProviderCall('direct_rpc','logs','rpc',[log],1)
            raise AssertionError((method,params))
    rpc=Rpc();monkeypatch.setattr(protocol_history,'select_rpc_client',lambda chain:('direct_rpc',rpc,ProviderCall('direct_rpc','probe','rpc','0x1',1),[]))
    out=protocol_history.protocol_event_timeline({'chain':'ethereum','protocol_adapter':'aave_v3','from_block':99,'to_block':100})
    assert out['event_count']==0
    assert out['log_fetch']['targets'][0]['removed_log_count']==1


def test_protocol_review_lifecycle_and_render(client,monkeypatch):
    signup=client.post('/api/v1/auth/signup',json={'email':'p10@example.com','password':'correct-horse-battery','role':'Analyst'})
    headers={'Authorization':'Bearer '+signup.json()['access_token']}
    workspace=client.post('/api/v1/workspaces',headers=headers,json={'name':'P10 Desk','role':'Analyst'}).json()
    from rivexis_api import main
    review={'adapter':'aave_v3','chain':'ethereum','from_block':100,'to_block':200,'change_count':1,'materiality_counts':{'HIGH':1,'MEDIUM':0,'LOW':0},'changes':[{'path':'reserve_configuration.liquidation_threshold_bps','from':8000,'to':7800,'materiality':'HIGH'}],'before':{},'after':{}}
    monkeypatch.setattr(main,'compare_protocol_configuration',lambda data:review)
    body={'workspace_id':workspace['id'],'input':{'protocol_adapter':'aave_v3','from_block':100,'to_block':200}}
    created=client.post('/api/v1/protocol-config/reviews',headers=headers,json=body)
    assert created.status_code==200
    report=created.json(); assert report['status']=='draft' and report['payload']['change_count']==1
    rid=report['id']
    assert client.get(f'/api/v1/protocol-config/reviews/{rid}',headers=headers).status_code==200
    approved=client.post(f'/api/v1/protocol-config/reviews/{rid}/approve',headers=headers)
    assert approved.status_code==200 and approved.json()['status']=='approved'
    html=client.get(f'/api/v1/protocol-config/reviews/{rid}/render?format=html',headers=headers)
    assert html.status_code==200 and 'Protocol Configuration Review' in html.text
    pdf=client.get(f'/api/v1/protocol-config/reviews/{rid}/render?format=pdf',headers=headers)
    assert pdf.status_code==200 and pdf.content.startswith(b'%PDF')


def test_registry_source_attestations_exposed(client):
    payload=client.get('/api/v1/protocol-deployments').json()
    assert payload['items']
    pinned=[r for r in payload['items'] if r['source_attestation']['attestation_status']=='PINNED_UPSTREAM_REVISION']
    assert len(pinned)>=4
