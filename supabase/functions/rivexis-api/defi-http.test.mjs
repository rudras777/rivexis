import test from 'node:test';import assert from 'node:assert/strict';import {handleDefi,readRequestText} from './defi-http.mjs';
const endpoint='/api/v1/defi/snapshot';
const request=(data,method='POST')=>new Request('https://example.com'+endpoint,{method,body:method==='POST'?JSON.stringify(data):undefined});
test('public input validation happens before quota/RPC',async()=>{
  const db={rpc(){throw new Error('must not reach database')}};
  assert.equal((await handleDefi(request({wallet:'bad'}),endpoint,db)).status,422);
  assert.equal((await handleDefi(request({wallet:'0x'+'1'.repeat(40),coverage:'all-protocols'}),endpoint,db)).status,422);
  assert.equal((await handleDefi(request({},'GET'),endpoint,db)).status,405);
  assert.equal((await handleDefi(request({wallet:'0x'+'1'.repeat(40),padding:'x'.repeat(5000)}),endpoint,db)).status,413);
});
test('distributed quota exhaustion and outages fail closed before RPC',async()=>{
  const req=()=>request({wallet:'0x'+'1'.repeat(40)});
  assert.equal((await handleDefi(req(),endpoint,{rpc:async()=>({data:false})})).status,429);
  assert.equal((await handleDefi(req(),endpoint,{rpc:async()=>({error:{message:'outage'}})})).status,503);
});

for(const path of ['/api/v1/defi/snapshot','/api/v1/defi/transaction']){
 test(path+' distinguishes outage, exhaustion and unconfirmed quota without RPC or financial success',async()=>{
  const fetchBefore=globalThis.fetch;let rpcCalls=0;
  globalThis.fetch=async()=>{rpcCalls++;assert.fail('Quota denial must not reach Ethereum RPC')};
  try{
   const states=[
    {value:{data:false},status:429},
    {value:{data:null},status:503},{value:{},status:503},
    {value:null,status:503},{value:undefined,status:503},
    {value:{data:'true'},status:503},{value:{data:1},status:503},
    {value:{data:true,error:{message:'secret-internal-error'}},status:503},
    {throws:true,status:503},
   ];
   for(const state of states){
    let quotaCalls=0;
    const admin={rpc:async(name,args)=>{quotaCalls++;assert.equal(name,'rivexis_defi_quota');assert.equal(args.p_wallet,wallet.toLowerCase());if(state.throws)throw Error('secret-internal-error');return state.value}};
    const response=await handleDefi(request(path.endsWith('/transaction')?validTransaction:{wallet}),path,admin,'https://rpc.example.invalid');
    assert.equal(response.status,state.status);assert.equal(quotaCalls,1);
    const body=await response.json();assert.equal(body.snapshot,undefined);assert.equal(body.liquidation,undefined);assert.equal(body.positions,undefined);assert.equal(body.healthFactorRaw,undefined);
    assert.ok(!JSON.stringify(body).includes('secret-internal-error'));
    assert.equal(response.headers.get('cache-control'),'no-store');
    if(state.status===503)assert.match(body.detail,/unavailable; no RPC request was made/);
    else assert.match(body.detail,/quota reached/);
   }
   assert.equal(rpcCalls,0);
  }finally{globalThis.fetch=fetchBefore}
 });
 test(path+' rechecks the atomic quota after an outage and only then reaches the provider',async()=>{
  const originalFetch=globalThis.fetch;let providerCalls=0,quotaCalls=0;
  globalThis.fetch=async()=>{providerCalls++;throw Error('provider transport outage')};
  const admin={rpc:async()=>{quotaCalls++;if(quotaCalls===1)throw Error('quota outage');return {data:true}}};
  try{
   const input=path.endsWith('/transaction')?validTransaction:{wallet};
   const first=await handleDefi(request(input),path,admin,'https://rpc.example.invalid');
   assert.equal(first.status,503);assert.equal(providerCalls,0);
   const second=await handleDefi(request(input),path,admin,'https://rpc.example.invalid');
   assert.equal(second.status,503);assert.equal(quotaCalls,2);assert.ok(providerCalls>0);
   const body=await second.json();assert.equal(body.status,'UNKNOWN');assert.match(body.detail,/No financial result has been inferred/);
  }finally{globalThis.fetch=originalFetch}
 });
 test(path+' treats provider invalid-parameter and unsupported-method errors as unavailable evidence',async()=>{
  const originalFetch=globalThis.fetch;
  try{
   for(const code of [-32602,-32601]){
    let calls=0;
    globalThis.fetch=async(_url,init)=>{calls++;const input=JSON.parse(init.body);return Response.json({jsonrpc:'2.0',id:input.id,error:{code,message:'Invalid or Unsupported upstream method: secret-provider-detail'}})};
    const input=path.endsWith('/transaction')?validTransaction:{wallet};
    const response=await handleDefi(request(input),path,{rpc:async()=>({data:true})},'https://rpc.example.invalid');
    assert.equal(response.status,503);assert.ok(calls>0);
    const body=await response.json();assert.equal(body.status,'UNKNOWN');assert.match(body.detail,/No financial result has been inferred/);assert.ok(!JSON.stringify(body).includes('secret-provider-detail'));
   }
  }finally{globalThis.fetch=originalFetch}
 });
}

const wallet='0x'+'1'.repeat(40),asset='0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2';
const noQuota={rpc(){assert.fail('Malformed input must not consume quota or reach RPC')}};
const transaction='/api/v1/defi/transaction';
const validTransaction={wallet,asset,kind:'repay',amount:'1',positionId:`aave-v3:1:${wallet}`};

test('zero and bad-checksum wallets are rejected before consuming global quota',async()=>{
  for(const invalid of ['0x'+'0'.repeat(40),'0x52908400098527886E0F7030069857D2E4169Ee7']){
    assert.equal((await handleDefi(request({wallet:invalid}),endpoint,noQuota)).status,422);
  }
});
test('invalid transaction shape and monetary forms cannot consume quota or RPC',async()=>{
  for(const changed of [{kind:'swap'},{asset:'bad'},{asset:'0x'+'0'.repeat(40)},{amount:1},{amount:'1e18'},{amount:'0'},{amount:'0.0000000000000000001'},{positionId:123},{positionId:'unrelated'},{sharesRaw:'0'},{sharesRaw:(2n**256n).toString()},{kind:'supply',sharesRaw:'1'}]){
    assert.equal((await handleDefi(request({...validTransaction,...changed}),transaction,noQuota)).status,422,JSON.stringify(changed));
  }
});
test('supported Aave and Morpho transaction inputs still pass to the distributed quota',async()=>{
  let calls=0;const quota={rpc:async()=>{calls++;return {data:false}}};
  for(const kind of ['repay','supply','borrow','withdraw']){
    assert.equal((await handleDefi(request({...validTransaction,kind}),transaction,quota)).status,429);
  }
  const morpho={...validTransaction,coverage:'combined',positionId:`morpho-blue:1:0x${'2'.repeat(64)}:${wallet}`,sharesRaw:'1000000'};
  assert.equal((await handleDefi(request(morpho),transaction,quota)).status,429);
  assert.equal(calls,5);
});
test('UTF-8 byte limit applies without Content-Length and oversized streams are cancelled',async()=>{
  const unicode={wallet,padding:'é'.repeat(2100)};
  assert.ok(JSON.stringify(unicode).length<4096);
  assert.equal((await handleDefi(request(unicode),endpoint,noQuota)).status,413);
  let cancelled=false;
  const stream=new ReadableStream({start(c){c.enqueue(new Uint8Array(4097));},cancel(){cancelled=true}});
  const req=new Request('https://example.com'+endpoint,{method:'POST',body:stream,duplex:'half'});
  assert.equal((await handleDefi(req,endpoint,noQuota)).status,413);
  assert.equal(cancelled,true);
});
test('body reader preserves exact UTF-8 boundaries and the report-specific byte limit',async()=>{
  const text='é'.repeat(2048);
  assert.equal(await readRequestText(new Request('https://example.com',{method:'POST',body:text})),text);
  await assert.rejects(readRequestText(new Request('https://example.com',{method:'POST',body:text+'x'})),/too large/);
  assert.equal((await readRequestText(new Request('https://example.com',{method:'POST',body:'x'.repeat(8192)}),8192)).length,8192);
  await assert.rejects(readRequestText(new Request('https://example.com',{method:'POST',body:'x'.repeat(8193)}),8192),/too large/);
  assert.equal((await handleDefi(new Request('https://example.com'+endpoint,{method:'POST',body:new Uint8Array([0xff])}),endpoint,noQuota)).status,422);
});

const sequence='/api/v1/defi/sequence',validSequence={wallet,coverage:'aave',actions:[{kind:'repay',asset,amount:'1'}]};
test('sequence malformed actions fail before quota or RPC',async()=>{
 for(const changed of [{actions:[]},{actions:Array(3).fill(validSequence.actions[0])},{actions:[{...validSequence.actions[0],data:'0x1234'}]},{actions:[{...validSequence.actions[0],amount:'0'}]},{coverage:'combined'}])assert.equal((await handleDefi(request({...validSequence,...changed}),sequence,noQuota)).status,422);
});
test('sequence atomic quota exhaustion, errors and unconfirmed replies fail closed',async()=>{
 const original=globalThis.fetch;let calls=0;globalThis.fetch=async()=>{calls++;assert.fail('Denied quota must never reach RPC')};
 try{for(const value of [{data:false},{data:null},{data:true,error:{}},{}]){const r=await handleDefi(request(validSequence),sequence,{rpc:async()=>value});assert.equal(r.status,value.data===false?429:503)}assert.equal(calls,0)}finally{globalThis.fetch=original}
});
test('sequence unsupported provider method cannot be labelled a user mistake or success',async()=>{
 const original=globalThis.fetch;globalThis.fetch=async(_url,init)=>{const request=JSON.parse(init.body);return Response.json({jsonrpc:'2.0',id:request.id,error:{code:-32601,message:'secret provider diagnostic'}})};
 try{const r=await handleDefi(request(validSequence),sequence,{rpc:async()=>({data:true})});assert.equal(r.status,503);const body=await r.json();assert.equal(body.status,'UNKNOWN');assert.ok(!JSON.stringify(body).includes('secret provider diagnostic'))}finally{globalThis.fetch=original}
});
