import test from 'node:test';import assert from 'node:assert/strict';import {handleDefi} from './defi-http.mjs';
const endpoint='/api/v1/defi/snapshot';
const request=(data,method='POST')=>new Request('https://example.com'+endpoint,{method,body:method==='POST'?JSON.stringify(data):undefined});
test('public input validation happens before quota/RPC',async()=>{
  const db={rpc(){throw new Error('must not reach database')}};
  assert.equal((await handleDefi(request({wallet:'bad'}),endpoint,db)).status,422);
  assert.equal((await handleDefi(request({},'GET'),endpoint,db)).status,405);
  assert.equal((await handleDefi(request({wallet:'0x'+'1'.repeat(40),padding:'x'.repeat(5000)}),endpoint,db)).status,413);
});
test('distributed quota exhaustion and outages fail closed before RPC',async()=>{
  const req=()=>request({wallet:'0x'+'1'.repeat(40)});
  assert.equal((await handleDefi(req(),endpoint,{rpc:async()=>({data:false})})).status,429);
  assert.equal((await handleDefi(req(),endpoint,{rpc:async()=>({error:{message:'outage'}})})).status,503);
});
