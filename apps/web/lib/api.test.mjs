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
