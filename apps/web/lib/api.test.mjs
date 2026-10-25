import {test,afterEach} from 'node:test';
import assert from 'node:assert/strict';
import {api,apiBlob,ApiError,setCsrfToken,API_REQUEST_TIMEOUT_MS} from './api.ts';
const realFetch=globalThis.fetch;
afterEach(()=>{globalThis.fetch=realFetch;setCsrfToken(null)});
const pending=signal=>new Promise((_,reject)=>{
 if(signal.aborted)return reject(signal.reason);
 signal.addEventListener('abort',()=>reject(signal.reason),{once:true});
});
const settle=async()=>{for(let i=0;i<10;i++)await Promise.resolve()};
const deadline=async(t,request,pattern)=>{
 t.mock.timers.enable({apis:['setTimeout']});
 const result=assert.rejects(request(),e=>e instanceof ApiError&&e.status===504&&pattern.test(e.message));
 await settle();t.mock.timers.tick(API_REQUEST_TIMEOUT_MS);await result;
};
test('successful JSON preserves credentials, cache, content type and CSRF',async()=>{
 setCsrfToken('csrf');let calls=0;
 globalThis.fetch=async(_,init)=>{calls++;assert.equal(init.credentials,'include');assert.equal(init.cache,'no-store');assert.equal(init.headers.get('X-Rivexis-CSRF'),'csrf');assert.equal(init.headers.get('Content-Type'),'application/json');return Response.json({id:'confirmed'})};
 assert.deepEqual(await api('/reports',{method:'POST',body:'{}'}),{id:'confirmed'});assert.equal(calls,1);
});
test('read deadline aborts request and returns actionable timeout',async t=>{
 let signal;globalThis.fetch=(_,init)=>{signal=init.signal;return pending(signal)};
 await deadline(t,()=>api('/settings'),/Try again/);assert.equal(signal.aborted,true);
});
test('write deadline never retries and discloses unknown outcome',async t=>{
 setCsrfToken('csrf');let calls=0;globalThis.fetch=(_,init)=>{calls++;return pending(init.signal)};
 await deadline(t,()=>api('/reports',{method:'POST',body:'{}'}),/Check the saved record/);assert.equal(calls,1);
});
test('stalled CSRF recovery aborts before any write',async t=>{
 const paths=[];globalThis.fetch=(url,init)=>{paths.push(url);return pending(init.signal)};
 await deadline(t,()=>api('/reports',{method:'POST',body:'{}'}),/Try again/);assert.equal(paths.length,1);assert.match(paths[0],/\/auth\/web\/csrf$/);
});
test('one deadline spans CSRF recovery and the later write',async t=>{
 t.mock.timers.enable({apis:['setTimeout']});let calls=0;
 globalThis.fetch=async(_,init)=>{calls++;if(calls===1){t.mock.timers.tick(30_000);return Response.json({csrf_token:'csrf'})}return pending(init.signal)};
 const result=assert.rejects(api('/reports',{method:'POST',body:'{}'}),e=>e.status===504&&/outcome/.test(e.message));
 await settle();assert.equal(calls,2);t.mock.timers.tick(5_000);await result;
});
test('deadline covers a JSON body stalled after headers',async t=>{
 globalThis.fetch=async(_,init)=>({ok:true,status:200,json:()=>pending(init.signal)});
 await deadline(t,()=>api('/settings'),/Try again/);
});
test('deadline covers a stalled binary export body',async t=>{
 globalThis.fetch=async(_,init)=>({ok:true,status:200,blob:()=>pending(init.signal)});
 await deadline(t,()=>apiBlob('/export'),/Try again/);
});
test('caller cancellation survives and prevents CSRF or writes',async()=>{
 let calls=0;globalThis.fetch=async()=>{calls++;return Response.json({})};const controller=new AbortController();controller.abort(new DOMException('Cancelled','AbortError'));
 await assert.rejects(api('/reports',{method:'POST',body:'{}',signal:controller.signal}),e=>e.name==='AbortError');assert.equal(calls,0);
});
test('caller cancellation also aborts an in-flight request',async()=>{
 globalThis.fetch=(_,init)=>pending(init.signal);const controller=new AbortController();const result=assert.rejects(api('/settings',{signal:controller.signal}),e=>e.name==='AbortError');controller.abort();await result;
});
test('malformed CSRF confirmation fails closed before mutation',async()=>{
 let calls=0;globalThis.fetch=async()=>{calls++;return Response.json({csrf_token:''})};await assert.rejects(api('/settings',{method:'PATCH',body:'{}'}),e=>e.status===503);assert.equal(calls,1);
});
test('error status and validated server explanation remain intact',async()=>{
 globalThis.fetch=async()=>Response.json({detail:'Reports are temporarily unavailable'},{status:503});await assert.rejects(api('/reports'),e=>e.status===503&&e.message==='Reports are temporarily unavailable');
});
test('204 and binary success complete without timeout failures',async()=>{
 globalThis.fetch=async()=>new Response(null,{status:204});assert.equal(await api('/empty'),undefined);
 globalThis.fetch=async()=>new Response('receipt');assert.equal(await (await apiBlob('/export')).text(),'receipt');
});

for(const method of ['POST','PUT','PATCH','DELETE'])test(`${method}: lost response warns of an unconfirmed write without retrying`,async()=>{
 setCsrfToken('csrf');let calls=0;globalThis.fetch=async()=>{calls++;throw new TypeError('test-only internal address')};
 await assert.rejects(api('/settings',{method,body:'{}'}),e=>e instanceof ApiError&&e.status===502&&/Check the saved record/.test(e.message)&&!e.message.includes('internal address'));assert.equal(calls,1);
});

test('a malformed successful write response is not confirmation or a reason to replay',async()=>{
 setCsrfToken('csrf');let calls=0;globalThis.fetch=async()=>{calls++;return new Response('{',{headers:{'content-type':'application/json'}})};
 await assert.rejects(api('/reports',{method:'POST',body:'{}'}),e=>e.status===502&&/outcome could not be confirmed/.test(e.message));assert.equal(calls,1);
});

test('binary write body transfer failure also discloses an unknown outcome',async()=>{
 setCsrfToken('csrf');let calls=0;globalThis.fetch=async()=>{calls++;return {ok:true,status:200,blob:async()=>{throw new TypeError('truncated download')}}};
 await assert.rejects(apiBlob('/export',{method:'POST',body:'{}'}),e=>e.status===502&&/Check the saved record/.test(e.message));assert.equal(calls,1);
});

for(const status of [500,502,503,504])test(`HTTP ${status} after a write retains its explanation and warns before retry`,async()=>{
 setCsrfToken('csrf');let calls=0;globalThis.fetch=async()=>{calls++;return Response.json({detail:'Provider unavailable'},{status})};
 await assert.rejects(api('/settings',{method:'PATCH',body:'{}'}),e=>e.status===status&&e.message.startsWith('Provider unavailable')&&/Check the saved record/.test(e.message));assert.equal(calls,1);
});

test('proxy unknown-outcome guidance is not duplicated by the browser client',async()=>{
 setCsrfToken('csrf');const detail='The request outcome could not be confirmed. Check the saved record or current settings before retrying.';
 globalThis.fetch=async()=>Response.json({detail},{status:502});await assert.rejects(api('/settings',{method:'PATCH',body:'{}'}),e=>e.status===502&&e.message===detail);
});

for(const status of [400,401,403,409,422,429])test(`HTTP ${status} remains an explicit write rejection`,async()=>{
 setCsrfToken('csrf');globalThis.fetch=async()=>Response.json({detail:'Explicit rejection'},{status});
 await assert.rejects(api('/settings',{method:'PATCH',body:'{}'}),e=>e.status===status&&e.message==='Explicit rejection');
});

test('CSRF transport failure never starts a write or falsely warns that one was sent',async()=>{
 let calls=0;globalThis.fetch=async()=>{calls++;throw new TypeError('CSRF connection lost')};await assert.rejects(api('/settings',{method:'PATCH',body:'{}'}),e=>e instanceof TypeError&&e.message==='CSRF connection lost');assert.equal(calls,1);
});

test('read transport failure is not misreported as an uncertain save',async()=>{
 globalThis.fetch=async()=>{throw new TypeError('read connection lost')};await assert.rejects(api('/settings'),e=>e instanceof TypeError&&e.message==='read connection lost');
});

test('caller cancellation after a write starts remains cancellation without a retry',async()=>{
 setCsrfToken('csrf');let calls=0;globalThis.fetch=(_,init)=>{calls++;return pending(init.signal)};
 const controller=new AbortController();const result=assert.rejects(api('/settings',{method:'PATCH',body:'{}',signal:controller.signal}),e=>e.name==='AbortError');await settle();controller.abort();await result;assert.equal(calls,1);
});
