import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {sampleSnapshot} from './defi-sample.mjs';
import {metrics} from './defi-unified-model.mjs';
import {monitorInput,evaluateMonitor,deliveryOutcome} from './defi-monitor-policy.mjs';
import {handleDefiMonitor} from './defi-monitor-http.mjs';

const wallet='0x'+'a'.repeat(40),now=1800000000000;
const settings={wallet,coverage:'aave',threshold:'1.20',recovery:'1.30',enabled:true,emailOptIn:false};
const rule=()=>({...monitorInput(settings),condition:'UNKNOWN'});
function evidence(){const s=sampleSnapshot(now);delete s.sample;return {...s,chainId:1,wallet,coverage:'aave',blockNumber:'30000000',blockHash:'0x'+'a'.repeat(64)}}

test('monitor configuration preserves all 18 decimal threshold digits and rejects ambient authority',()=>{
 assert.equal(monitorInput({...settings,threshold:'1.200000000000000001'}).threshold_raw,'1200000000000000001');
 for(const input of [{...settings,owner:'other'},{...settings,recipient:'a@example.invalid'},{...settings,coverage:'all'},{...settings,emailOptIn:undefined},{...settings,threshold:'1e0'},{...settings,recovery:'1.21'},{...settings,threshold:'0.99'},{...settings,wallet:'0x'+'0'.repeat(40)}])assert.throws(()=>monitorInput(input));
});
test('monitor uses protocol accounting and exact adjacent integer thresholds, ignores display prices',()=>{
 const s=evidence(),actual=metrics(s.positions[0]).healthFactorRaw;
 s.observedHealthFactorRaw='0';s.marketPrice='999999999';
 assert.equal(evaluateMonitor({...rule(),threshold_raw:actual,recovery_raw:(BigInt(actual)+10n**17n).toString()},s,now).condition,'BREACH');
 assert.equal(evaluateMonitor({...rule(),threshold_raw:(BigInt(actual)-1n).toString(),recovery_raw:(BigInt(actual)+10n**17n).toString()},s,now).condition,'CLEAR');
 assert.equal(evaluateMonitor(rule(),s,now).health_raw,actual);
});
test('monitor hysteresis holds a breach in the band and debt-free recovery has no invented finite health',()=>{
 const s=evidence(),r={...rule(),threshold_raw:'1300000000000000000',recovery_raw:'1400000000000000000'};
 assert.equal(evaluateMonitor({...r,condition:'BREACH'},s,now).condition,'BREACH');
 assert.equal(evaluateMonitor(r,s,now).condition,'CLEAR');
 s.positions[0].reserves[1].debtRaw='0';const result=evaluateMonitor({...r,condition:'BREACH'},s,now);assert.equal(result.condition,'CLEAR');assert.equal(result.health_raw,null);
});
test('monitor rejects stale/future/wrong-owner/restored/sample/unsupported/oracle-invalid evidence',()=>{
 for(const mutate of [s=>s.blockTimestamp-=181,s=>s.blockTimestamp+=31,s=>s.wallet='0x'+'b'.repeat(40),s=>s.coverage='combined',s=>s.sample=true,s=>s.restoredReport=true,s=>s.chainId=137,s=>s.blockHash='bad',s=>s.positions[0].eMode=1,s=>s.positions[0].reserves[0].oracleState='STALE']){const s=evidence();mutate(s);assert.throws(()=>evaluateMonitor(rule(),s,now))}
});
test('dated combined Aave/Morpho reference evaluates the minimum independent health with original evidence clock',()=>{
 const {snapshot:s}=JSON.parse(readFileSync(new URL('../../../certification-reports/morpho-portfolio-reference.json',import.meta.url)));
 const r={...rule(),wallet:s.wallet.toLowerCase(),coverage:'combined'};
 const result=evaluateMonitor(r,s,s.blockTimestamp*1000);
 assert.equal(result.health_raw,s.positions.map(p=>metrics(p).healthFactorRaw).filter(Boolean).map(BigInt).reduce((a,b)=>a<b?a:b).toString());
 const changed=structuredClone(s);changed.positions.find(p=>p.protocol==='Morpho Blue').oracleEvidence.codeHash='bad';assert.throws(()=>evaluateMonitor(r,changed,s.blockTimestamp*1000));
});
test('delivery acceptance needs a receipt; duplicate, timeout and 5xx cannot be blindly retried',()=>{
 assert.deepEqual(deliveryOutcome(201,{messageId:'receipt'}),{state:'ACCEPTED',message_id:'receipt'});
 for(const [status,body] of [[201,{}],[400,{code:'duplicate_parameter'}],[408,{}],[500,{}]])assert.equal(deliveryOutcome(status,body).state,'UNKNOWN');
 assert.equal(deliveryOutcome(429,{}).state,'RETRY');assert.equal(deliveryOutcome(400,{code:'invalid_parameter'}).state,'FAILED');
});
test('inactive monitoring performs no DB or provider operation and refuses writes',async()=>{
 const admin={rpc:()=>{throw new Error('Unexpected database access')}};
 const response=await handleDefiMonitor(new Request('https://rivexis.rvea.info/api/v1/defi/monitor'),wallet,admin);assert.equal((await response.json()).runtime.state,'INACTIVE');
 assert.equal((await handleDefiMonitor(new Request('https://rivexis.rvea.info/api/v1/defi/monitor',{method:'PATCH',body:'{}'}),wallet,admin)).status,503);
 assert.equal((await handleDefiMonitor(new Request('https://rivexis.rvea.info/'),null,admin,true)).status,401);
});
test('monitor API validates before storage and always supplies server-verified owner, without retrying unknown saves',async()=>{
 let calls=0;const admin={rpc:async(name,args)=>{calls++;assert.equal(name,'rivexis_defi_monitor_manage');assert.equal(args.p_owner,'VERIFIED_OWNER');return {error:{code:'lost'}}}};
 const request=body=>new Request('https://rivexis.rvea.info/api/v1/defi/monitor',{method:'PATCH',body:JSON.stringify(body)});
 assert.equal((await handleDefiMonitor(request({...settings,owner:'attacker'}),'VERIFIED_OWNER',admin,true)).status,422);assert.equal(calls,0);
 const response=await handleDefiMonitor(request(settings),'VERIFIED_OWNER',admin,true);assert.equal(response.status,503);assert.match((await response.json()).detail,/Reload/);assert.equal(calls,1);
});
