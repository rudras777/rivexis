import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {mkdtemp,writeFile,readFile,unlink,rmdir} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {buildCases,createRpc,validateSimulation,certify,runCertification} from './certify_aave_sequence_rpc.mjs';
const reference=JSON.parse(readFileSync(new URL('../certification-reports/aave-sequential-rpc-reference.json',import.meta.url),'utf8'));
const clone=x=>structuredClone(x);

test('RPC transport cannot broadcast, sign, unlock or change provider state',async()=>{
 let calls=0;const rpc=createRpc(async()=>{calls++;throw new Error('Unexpected network access')});
 for(const method of ['eth_sendTransaction','eth_sendRawTransaction','eth_sign','personal_sign','personal_unlockAccount','anvil_impersonateAccount','evm_setAccountBalance','admin_addPeer'])await assert.rejects(rpc(method,[]),/read-only/);
 assert.equal(calls,0);
});

test('transport retains each request identity with overlapping replies',async()=>{
 const pending=[];const rpc=createRpc(async(url,request)=>{assert.equal(url,'https://ethereum.publicnode.com');assert.equal(request.redirect,'error');assert.ok(request.signal);const body=JSON.parse(request.body);return new Promise(resolve=>pending.push(()=>resolve({ok:true,json:async()=>({jsonrpc:'2.0',id:body.id,result:body.id})})))});
 const first=rpc('eth_chainId',[]),second=rpc('eth_chainId',[]);pending[1]();pending[0]();assert.equal(await first,1);assert.equal(await second,2);
});

test('provider HTTP, RPC, wrong identity and incomplete envelopes cannot certify success',async()=>{
 for(const response of [{ok:false,status:429},{ok:true,json:async()=>({jsonrpc:'2.0',id:1,error:{code:-32601}})},{ok:true,json:async()=>({jsonrpc:'2.0',id:2,result:'0x1'})},{ok:true,json:async()=>({jsonrpc:'2.0',id:1})}])await assert.rejects(createRpc(async()=>response)('eth_chainId',[]));
});

test('oversized payloads and repeated requests are bounded before extra network access',async()=>{
 let calls=0;const rpc=createRpc(async(url,request)=>{calls++;return {ok:true,json:async()=>({jsonrpc:'2.0',id:JSON.parse(request.body).id,result:'0x1'})}});
 await assert.rejects(rpc('eth_call',['x'.repeat(100_000)]),/too large/);assert.equal(calls,0);
 for(let i=0;i<39;i++)await rpc('eth_chainId',[]);await assert.rejects(rpc('eth_chainId',[]),/limit exceeded/);assert.equal(calls,39);
});

test('wrong network or reorganized parent fails before any sequential simulation',async()=>{
 for(const chain of ['0x89','0x1']){const methods=[];await assert.rejects(certify({snapshot:reference.snapshot},async(method)=>{methods.push(method);return method==='eth_chainId'?chain:{...reference.parent,hash:'0x'+'f'.repeat(64)}}));assert.ok(!methods.includes('eth_simulateV1'));}
});

test('samples, unsupported protocol coverage and unfunded wallets cannot be relabeled genuine',()=>{
 const sample=clone(reference.snapshot);sample.sample=true;assert.throws(()=>buildCases(sample,1n));
 const morpho=clone(reference.snapshot);morpho.positions[0].protocol='Morpho Blue';assert.throws(()=>buildCases(morpho,1n));
 const empty=clone(reference.snapshot);empty.positions[0].reserves.find(r=>r.symbol==='USDT').walletRaw='0';assert.throws(()=>buildCases(empty,1n));
});

test('captured successful baseline replays with its exact historical parent identity',()=>{
 const spec=buildCases(reference.snapshot,1n)[0];assert.equal(validateSimulation(reference.result,spec,reference.parent).passed,true);
});

test('wrong parent, missing call, missing gas, altered time and false success fail closed',()=>{
 const spec=buildCases(reference.snapshot,1n)[0];
 for(const change of [r=>r[0].parentHash='0x'+'f'.repeat(64),r=>r[0].calls.pop(),r=>delete r[0].calls[0].gasUsed,r=>r[0].timestamp='0x1',r=>r[0].calls[0].status='0x0',r=>r[0].baseFeePerGas='0x0',r=>r[0].calls[0].returnData='0x']){const result=clone(reference.result);change(result);assert.throws(()=>validateSimulation(result,spec,reference.parent));}
});

test('a failed rerun replaces an old successful artifact with an explicit failure',async()=>{
 const directory=await mkdtemp(join(tmpdir(),'rivexis-sequence-evidence-')),path=join(directory,'result.json');
 try{for(const receipt of [{snapshot:reference.snapshot},async()=>{throw new Error('Receipt is not valid JSON')}]){await writeFile(path,JSON.stringify({status:'PASSED',passed:12}));await assert.rejects(runCertification(receipt,path,async()=> '0x89'));const saved=JSON.parse(await readFile(path,'utf8'));assert.equal(saved.status,'FAILED');assert.equal(saved.passed,0);assert.deepEqual(saved.completedCases,[]);assert.equal(saved.signaturesOrSubmissions,false);}}finally{await unlink(path);await rmdir(directory);}
});
