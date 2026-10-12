import test from 'node:test';
import assert from 'node:assert/strict';
import {handleOnChain} from './onchain-http.mjs';
const address='0x'+'1'.repeat(40), hash='0x'+'2'.repeat(64);
const block={number:42n,hash,timestamp:BigInt(Math.floor(Date.now()/1000))};
const quota={rpc:async()=>({data:true})};
const request=(input)=>new Request('https://example.invalid/api/v1/on-chain/contract',{method:'POST',body:JSON.stringify(input)});
function rpc(overrides={}){return {getChainId:async()=>1,getBlock:async()=>block,getCode:async()=> '0x60006000',getStorageAt:async()=> '0x'+'0'.repeat(64),readContract:async({functionName})=>functionName==='name'?'Token':functionName==='symbol'?'TKN':functionName==='decimals'?18:100n,getBalance:async()=>123n,call:async()=>({data:'0x'+'0'.repeat(63)+'1'}),...overrides}}
const run=(input,path='contract',provider=rpc(),db=quota)=>handleOnChain(request(input),'/api/v1/on-chain/'+path,db,'https://rpc.invalid',()=>provider);
test('on-chain malformed input and client-selected RPC or actor fields fail before quota',async()=>{
 const db={rpc:()=>assert.fail('must not consume quota')};
 for(const body of [{chainId:2,address},{chainId:1,address:'bad'},{chainId:1,address:'0x'+'0'.repeat(40)},{chainId:1,address,rpcUrl:'http://localhost'},{chainId:1,address,from:address},{chainId:1,address:'0x52908400098527886E0F7030069857D2E4169Ee7'}])assert.equal((await run(body,'contract',undefined,db)).status,422);
 for(const data of ['0x','0xZZZZZZZZ','0x'+ 'a'.repeat(4100)])assert.equal((await run({chainId:1,address,data},'read',undefined,db)).status,422);
});
test('inspection quota exhaustion and outages cannot reach RPC',async()=>{
 for(const [result,status] of [[{data:false},429],[{error:{}},503]])assert.equal((await run({chainId:1,address},'contract',{getChainId:()=>assert.fail('no RPC')},{rpc:async()=>result})).status,status);
});
test('contract evidence is pinned and source/ABI verification is not invented',async()=>{
 const seen=[];const provider=rpc({getCode:async args=>{seen.push(args);return '0x60006000'},readContract:async args=>{seen.push(args);return args.functionName==='name'?'Token':18n},getStorageAt:async args=>{seen.push(args);return '0x'+'0'.repeat(64)}});
 const response=await run({chainId:1,address},'contract',provider),body=await response.json();assert.equal(response.status,200);assert.equal(body.codeBytes,4);assert.equal(body.sourceVerified,false);assert.equal(body.abiVerified,false);assert.equal(body.blockHash,hash);assert.ok(seen.every(item=>item.blockNumber===42n));assert.equal(body.proxy.implementation,null);
});
test('EOA, nonstandard metadata and malformed proxy slots remain explicit',async()=>{
 const empty=await (await run({chainId:1,address},'contract',rpc({getCode:async()=> '0x'}))).json();assert.equal(empty.status,'NO_CONTRACT_CODE');assert.equal(empty.codeDetected,false);
 const unknown=await (await run({chainId:1,address},'contract',rpc({readContract:async()=>{throw Error('revert')},getStorageAt:async()=> '0x'+'1'.repeat(64)}))).json();assert.equal(unknown.metadata.decimals.status,'UNKNOWN');assert.equal(unknown.proxy.implementation,'UNKNOWN');assert.equal(unknown.proxy.implementationCodeHash,null);
});
test('stale, reorganized and wrong-network evidence fail closed',async()=>{
 let count=0;for(const provider of [rpc({getChainId:async()=>137}),rpc({getBlock:async()=>({...block,timestamp:block.timestamp-181n})}),rpc({getBlock:async()=>({...block,hash:count++? '0x'+'3'.repeat(64):hash})})]){const result=await run({chainId:1,address},'contract',provider);assert.equal(result.status,503);assert.equal((await result.json()).status,'UNKNOWN')}
});
test('reads have bounded gas, no caller/value overrides, and reject failed or oversized outputs',async()=>{
 let params;const provider=rpc({call:async args=>{params=args;return {data:'0x1234'}}});const result=await run({chainId:1,address,data:'0x12345678'},'read',provider);assert.equal(result.status,200);assert.equal(params.gas,500000n);assert.equal(params.blockNumber,42n);assert.equal(params.account,undefined);assert.equal(params.value,undefined);
 for(const call of [async()=>{throw Error('revert')},async()=>({data:'0x'+'a'.repeat(32770)})])assert.equal((await run({chainId:1,address,data:'0x12345678'},'read',rpc({call}))).status,503);
});
test('wallet and network evidence preserve observed raw amounts and block identity',async()=>{
 const wallet=await (await run({chainId:1,address},'wallet')).json();assert.equal(wallet.balanceWei,'123');assert.equal(wallet.blockNumber,'42');
 const network=await (await run({chainId:1},'network')).json();assert.equal(network.chainId,1);assert.equal(network.blockHash,hash);
});
