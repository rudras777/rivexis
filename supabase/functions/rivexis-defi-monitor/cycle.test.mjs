import test from 'node:test';import assert from 'node:assert/strict';
import {runMonitorCycle,monitorConfiguration,readBrevoResult} from './cycle.mjs';
import {sampleSnapshot} from '../rivexis-api/defi-sample.mjs';
const now=1800000000000,wallet='0x'+'a'.repeat(40);
function setup(){
 const calls=[],rule={id:'rule',version:1,lease_token:'lease',wallet,coverage:'aave',threshold_raw:'1400000000000000000',recovery_raw:'1500000000000000000',condition:'UNKNOWN'};
 const s={...sampleSnapshot(now),sample:false,chainId:1,wallet,coverage:'aave',blockNumber:'30000000',blockHash:'0x'+'a'.repeat(64)};
 return {calls,rule,s,config:{enabled:true,emailEnabled:true,now:()=>now,reserve:async()=>true,job:async(action,payload)=>{calls.push({action,payload});return action==='claim'?rule:action==='claim_delivery'?{id:'event',delivery_token:'delivery'}:{committed:true}},readSnapshot:async()=>s,verifyBlock:async()=>true,send:async()=>({status:201,body:{messageId:'receipt'}})}};
}
test('disabled configuration has no protocol reads, claims or sends',async()=>{const {config,calls}=setup();assert.deepEqual(await runMonitorCycle({...config,enabled:false}),{state:'INACTIVE',evaluated:0,attempted:0});assert.deepEqual(calls.map(c=>c.action),['heartbeat'])});
test('one bounded invocation commits one evaluation and one acceptance without claiming inbox delivery',async()=>{const {config,calls}=setup();assert.deepEqual(await runMonitorCycle(config),{state:'SCHEDULED',evaluated:1,attempted:1});assert.deepEqual(calls.map(c=>c.action),['heartbeat','claim','complete','claim_delivery','mark_delivery']);assert.equal(calls.at(-1).payload.state,'ACCEPTED')});
test('quota/provider/stale failures record unavailable, never a successful condition',async()=>{
 for(const readSnapshot of [async()=>{throw new Error('quota unavailable')},async()=>({...setup().s,blockTimestamp:1})]){const {config,calls}=setup();await runMonitorCycle({...config,emailEnabled:false,readSnapshot});assert.deepEqual(calls.map(c=>c.action),['heartbeat','claim','unavailable'])}
});
test('reorganized previous block invalidates evidence without sending a new risk inference',async()=>{const {config,calls,rule}=setup();Object.assign(rule,{block_number:'29999999',block_hash:'0x'+'b'.repeat(64)});let reads=0;await runMonitorCycle({...config,emailEnabled:false,verifyBlock:async()=>false,readSnapshot:async()=>{reads++;throw new Error('unexpected')}});assert.equal(reads,0);assert.deepEqual(calls.map(c=>c.action),['heartbeat','claim','reorg'])});
test('transport unknown is persisted once; a lost mark is not retried',async()=>{const {config,calls}=setup();await runMonitorCycle({...config,send:async()=>{throw new Error('timeout')}});assert.equal(calls.at(-1).payload.state,'UNKNOWN');let sends=0;await assert.rejects(runMonitorCycle({...config,send:async()=>{sends++;return {status:201,body:{messageId:'receipt'}}},job:async(action,payload)=>{if(action==='mark_delivery')throw new Error('unknown commit');return config.job(action,payload)}}));assert.equal(sends,1)});
test('monitor config requires explicit approval, fixed HTTPS RPC hosts and independent email activation',()=>{
 const env={ETHEREUM_RPC_URL:'https://eth-mainnet.g.alchemy.com/v2/server-secret',RIVEXIS_DEFI_MONITOR_ENABLED:'true',RIVEXIS_MONITOR_RPC_APPROVED:'true'};
 assert.equal(monitorConfiguration(k=>env[k]).enabled,true);assert.equal(monitorConfiguration(k=>env[k]).emailEnabled,false);
 for(const url of ['http://ethereum.publicnode.com','https://attacker.invalid','https://user:password@ethereum.publicnode.com','https://eth-mainnet.g.alchemy.com:8443/'])assert.equal(monitorConfiguration(k=>k==='ETHEREUM_RPC_URL'?url:env[k]).enabled,false);
 assert.equal(monitorConfiguration(k=>k==='RIVEXIS_MONITOR_RPC_APPROVED'?undefined:env[k]).enabled,false);
});
test('provider receipt bodies are streamed with a hard bound and malformed bodies remain unknown',async()=>{
 assert.deepEqual(await readBrevoResult(new Response('{"messageId":"test"}',{status:201})),{status:201,body:{messageId:'test'}});
 assert.deepEqual(await readBrevoResult(new Response('x'.repeat(16385),{status:201})),{status:201,body:null});
 assert.deepEqual(await readBrevoResult(new Response('not-json',{status:201})),{status:201,body:null});
});
test('unconfirmed or exhausted quota prevents prior-block validation and snapshot reads alike',async()=>{
 for(const reserve of [async()=>false,async()=>null,async()=>{throw new Error('quota transport')}]){
  const {config,calls,rule}=setup();Object.assign(rule,{block_number:'29999999',block_hash:'0x'+'b'.repeat(64)});let reads=0;
  await runMonitorCycle({...config,emailEnabled:false,reserve,verifyBlock:async()=>{reads++;return true},readSnapshot:async()=>{reads++;return setup().s}});
  assert.equal(reads,0);assert.deepEqual(calls.map(c=>c.action),['heartbeat','claim','unavailable']);
 }
});
