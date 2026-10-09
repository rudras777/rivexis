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
