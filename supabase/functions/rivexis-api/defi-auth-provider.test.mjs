// Real Edge handler/routing/cookies with explicit Supabase fault fixtures.
// No live identity, credential, email, database row or provider is changed.
import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {LIVE_ORIGIN,PUBLIC_ORIGINS,authEmailOrigin} from './public-origin.mjs';
import {readFileSync} from 'node:fs';
import {stripTypeScriptTypes} from 'node:module';
import {webcrypto} from 'node:crypto';
import {parseRole,roleOrDefault} from './role.mjs';

const compiled=stripTypeScriptTypes(readFileSync(new URL('./index.ts',import.meta.url),'utf8').replace(/^import .*;\r?$/gm,''));
const user={id:'fixture-owner',email:'owner@example.invalid',email_confirmed_at:'2026-10-20',user_metadata:{role:'Individual'}};
const rejection=(code='bad_jwt',status=401)=>({name:'AuthApiError',code,status});
const validRead=()=>({data:{user},error:null});
const validRefresh=()=>({data:{user,session:{access_token:'fixture-new-access',refresh_token:'fixture-new-refresh'}},error:null});
function harness({read=validRead,refresh=validRefresh,databaseFailure=false}={}){
 let handler,reads=0,refreshes=0,dbCalls=0;
 const sdk={getUser:async()=>{reads++;return await read()},refreshSession:async()=>{refreshes++;return await refresh()}};
 const admin={rpc:async(_name,args)=>{dbCalls++;if(databaseFailure)return {data:null,error:{message:'fixture database unavailable'}};return {data:args?.p_action==='list_workspaces'?{items:[]}:{role:'Individual'},error:null}}};
 const createClient=()=>({...admin,auth:sdk});
 const context=vm.createContext({LIVE_ORIGIN,PUBLIC_ORIGINS,authEmailOrigin,Deno:{env:{get:()=>''},serve:fn=>{handler=fn}},createClient,parseRole,roleOrDefault,Response,Request,Headers,URL,TextEncoder,TextDecoder,Uint8Array,crypto:webcrypto,atob,btoa,console:{error:()=>{}}});
 new vm.Script(compiled).runInContext(context);
 const request=(path='/api/v1/auth/session-status',session={access_token:'fixture-access',refresh_token:'fixture-refresh',csrf:'fixture-csrf'})=>new Request('https://example.invalid'+path,{headers:session?{cookie:'rvx_session='+Buffer.from(JSON.stringify(session)).toString('base64url')}:{}});
 return {handler,request,calls:()=>({reads,refreshes,dbCalls})};
}
for(const path of ['/api/v1/auth/session-status','/api/v1/workspaces']){
 for(const status of [500,502,503,504,429])test(`${path}: provider${status} preserves session and never attempts refresh`,async()=>{
  const h=harness({read:async()=>({data:{user:null},error:{name:'AuthRetryableFetchError',status,code:'unexpected_failure'}}),refresh:async()=>({data:{user:null,session:null},error:{name:'AuthRetryableFetchError',status}})});
  const response=await h.handler(h.request(path));
  assert.equal(response.status,503);assert.equal(response.headers.get('set-cookie'),null);
  assert.deepEqual(h.calls(),{reads:1,refreshes:0,dbCalls:0});
  assert.ok(!JSON.stringify(await response.json()).includes('fixture-access'));
 });
}
for(const [name,read] of [
 ['transport exception',async()=>{throw new TypeError('fixture connection failure')}],
 ['malformed empty success',async()=>({data:{user:null},error:null})],
 ['malformed user',async()=>({data:{user:{id:42}},error:null})],
 ['unknown provider rejection',async()=>({data:{user:null},error:rejection('unknown_provider_configuration',401)})],
 ['provider404',async()=>({data:{user:null},error:rejection('not_found',404)})],
])test(`session read: ${name} is unavailable without clearing or refreshing`,async()=>{
 const h=harness({read});const r=await h.handler(h.request());assert.equal(r.status,503);assert.equal(r.headers.get('set-cookie'),null);assert.equal(h.calls().refreshes,0);assert.equal(h.calls().dbCalls,0);
});
test('healthy read grants only the server-verified session without rotation',async()=>{
 const h=harness();const r=await h.handler(h.request());assert.equal(r.status,200);assert.deepEqual(await r.json(),{authenticated:true,email_verified:true});assert.equal(r.headers.get('set-cookie'),null);assert.deepEqual(h.calls(),{reads:1,refreshes:0,dbCalls:1});
});
test('expired access renews once and returns the confirmed HttpOnly replacement',async()=>{
 const h=harness({read:async()=>({data:{user:null},error:rejection()})});const r=await h.handler(h.request());assert.equal(r.status,200);assert.equal((await r.json()).authenticated,true);assert.match(r.headers.get('set-cookie'),/^rvx_session=.+HttpOnly; Secure; SameSite=Lax$/);assert.deepEqual(h.calls(),{reads:1,refreshes:1,dbCalls:1});
});
for(const [name,refresh] of [
 ['provider503',async()=>({data:{user:null,session:null},error:{status:503,name:'AuthRetryableFetchError'}})],
 ['rate limit',async()=>({data:{user:null,session:null},error:{status:429,name:'AuthApiError',code:'over_request_rate_limit'}})],
 ['transport exception',async()=>{throw new TypeError('fixture refresh transport failure')}],
 ['malformed success',async()=>({data:{user,session:{access_token:42,refresh_token:'fixture-new-refresh'}},error:null})],
])test(`refresh: ${name} is unavailable without deleting the original session`,async()=>{
 const h=harness({read:async()=>({data:{user:null},error:rejection()}),refresh});const r=await h.handler(h.request());assert.equal(r.status,503);assert.equal(r.headers.get('set-cookie'),null);assert.deepEqual(h.calls(),{reads:1,refreshes:1,dbCalls:0});
});
for(const code of ['refresh_token_not_found','refresh_token_already_used','session_expired'])test(`confirmed ${code} still clears invalid session`,async()=>{
 const h=harness({read:async()=>({data:{user:null},error:rejection()}),refresh:async()=>({data:{user:null,session:null},error:rejection(code,400)})});const r=await h.handler(h.request('/api/v1/workspaces'));assert.equal(r.status,401);assert.match(r.headers.get('set-cookie'),/Max-Age=0/);assert.equal(h.calls().dbCalls,0);
});
test('a missing cookie remains signed out without provider calls',async()=>{
 const h=harness();const r=await h.handler(h.request('/api/v1/auth/session-status',null));assert.equal(r.status,200);assert.deepEqual(await r.json(),{authenticated:false,email_verified:false});assert.deepEqual(h.calls(),{reads:0,refreshes:0,dbCalls:0});
});
test('database failure after confirmed rotation retains the validated replacement cookie',async()=>{
 const h=harness({read:async()=>({data:{user:null},error:rejection()}),databaseFailure:true});const r=await h.handler(h.request());assert.equal(r.status,503);assert.match(r.headers.get('set-cookie'),/^rvx_session=/);assert.ok(!r.headers.get('set-cookie').includes('Max-Age=0'));assert.ok(!JSON.stringify(await r.json()).includes('fixture-new-refresh'));
});
for(const code of ['user_banned','session_not_found'])test(`confirmed ${code} never attempts to renew access`,async()=>{
 const h=harness({read:async()=>({data:{user:null},error:rejection(code,403)})});const r=await h.handler(h.request('/api/v1/workspaces'));assert.equal(r.status,401);assert.match(r.headers.get('set-cookie'),/Max-Age=0/);assert.deepEqual(h.calls(),{reads:1,refreshes:0,dbCalls:0});
});
for(const field of ['access_token','refresh_token','csrf'])test(`malformed cookie ${field} is denied before provider I/O`,async()=>{
 const h=harness();const session={access_token:'fixture-access',refresh_token:'fixture-refresh',csrf:'fixture-csrf',[field]:42};const r=await h.handler(h.request('/api/v1/workspaces',session));assert.equal(r.status,401);assert.deepEqual(h.calls(),{reads:0,refreshes:0,dbCalls:0});
});
test('repeated provider failures recover with the same cookie once the read is healthy',async()=>{
 let attempts=0;const h=harness({read:async()=>++attempts<3?{data:{user:null},error:{status:503,name:'AuthRetryableFetchError'}}:validRead()});
 for(let i=0;i<2;i++){const r=await h.handler(h.request());assert.equal(r.status,503);assert.equal(r.headers.get('set-cookie'),null)}
 const recovered=await h.handler(h.request());assert.equal(recovered.status,200);assert.equal((await recovered.json()).authenticated,true);assert.deepEqual(h.calls(),{reads:3,refreshes:0,dbCalls:1});
});
test('a failed refresh can be retried explicitly and publish only the confirmed replacement',async()=>{
 let attempts=0;const h=harness({read:async()=>({data:{user:null},error:rejection()}),refresh:async()=>++attempts===1?{data:{user:null,session:null},error:{status:503,name:'AuthRetryableFetchError'}}:validRefresh()});
 const first=await h.handler(h.request());assert.equal(first.status,503);assert.equal(first.headers.get('set-cookie'),null);
 const recovered=await h.handler(h.request());assert.equal(recovered.status,200);assert.equal((await recovered.json()).authenticated,true);assert.match(recovered.headers.get('set-cookie'),/HttpOnly; Secure/);assert.deepEqual(h.calls(),{reads:2,refreshes:2,dbCalls:1});
});
test('a rejection code on a provider503 cannot turn an outage into session deletion',async()=>{
 const h=harness({read:async()=>({data:{user:null},error:rejection('bad_jwt',503)})});const r=await h.handler(h.request());assert.equal(r.status,503);assert.equal(r.headers.get('set-cookie'),null);assert.equal(h.calls().refreshes,0);
});

for(const path of ['/api/v1/auth/session-status','/api/v1/workspaces'])test(`${path}: actual invalid refresh contract ends the rejected session`,async()=>{
 const h=harness({read:async()=>({data:{user:null},error:rejection('bad_jwt',403)}),refresh:async()=>({data:{user:null,session:null},error:rejection('validation_failed',400)})});
 const r=await h.handler(h.request(path));assert.equal(r.status,path.endsWith('session-status')?200:401);assert.match(r.headers.get('set-cookie'),/Max-Age=0/);assert.deepEqual(h.calls(),{reads:1,refreshes:1,dbCalls:0});
 if(path.endsWith('session-status'))assert.equal((await r.json()).authenticated,false);
});
test('validation_failed on a user read is not interpreted as refresh-token rejection',async()=>{
 const h=harness({read:async()=>({data:{user:null},error:rejection('validation_failed',400)})});const r=await h.handler(h.request());assert.equal(r.status,503);assert.equal(r.headers.get('set-cookie'),null);assert.equal(h.calls().refreshes,0);
});
test('validation_failed on a refresh provider503 preserves the original session',async()=>{
 const h=harness({read:async()=>({data:{user:null},error:rejection('bad_jwt',403)}),refresh:async()=>({data:{user:null,session:null},error:rejection('validation_failed',503)})});
 const r=await h.handler(h.request());assert.equal(r.status,503);assert.equal(r.headers.get('set-cookie'),null);assert.equal(h.calls().dbCalls,0);
});

for(const [service,path] of [['rivexis-decision-reports','/api/v1/history'],['rivexis-alerts','/api/v1/alerts']]){
 const source=stripTypeScriptTypes(readFileSync(new URL(`../${service}/index.ts`,import.meta.url),'utf8').replace(/^import .*;\r?$/gm,''));
 function isolated({read=validRead,refresh=validRefresh,session={access_token:'fixture-access',refresh_token:'fixture-refresh',csrf:'fixture-csrf'}}={}){
  let handler,reads=0,refreshes=0,dbCalls=0;const actors=[];
  const createClient=()=>({auth:{getUser:async()=>{reads++;return await read()},refreshSession:async()=>{refreshes++;return await refresh()}},rpc:async(_name,args)=>{dbCalls++;if(args?.p_actor_user_id)actors.push(args.p_actor_user_id);return {data:{items:[]},error:null}}});
  const context=vm.createContext({LIVE_ORIGIN,PUBLIC_ORIGINS,authEmailOrigin,Deno:{env:{get:()=>''},serve:fn=>{handler=fn}},createClient,Response,Request,Headers,URL,TextEncoder,TextDecoder,Uint8Array,atob,btoa,console:{error:()=>{}}});
  new vm.Script(source).runInContext(context);
  return {actors,send:()=>handler(new Request('https://example.invalid'+path,{headers:session?{cookie:'rvx_session='+Buffer.from(JSON.stringify(session)).toString('base64url')}:{}})),calls:()=>({reads,refreshes,dbCalls})};
 }
 for(const [label,read] of [
  ...[500,502,503,504,429].map(status=>[`provider${status}`,async()=>({data:{user:null},error:{status,name:'AuthRetryableFetchError'}})]),
  ['transport exception',async()=>{throw new TypeError('private provider detail')}],
  ['malformed success',async()=>({data:{user:null},error:null})],
  ['unknown rejection',async()=>({data:{user:null},error:rejection('unknown_configuration',401)})],
 ])test(`${service}: ${label} preserves cookie and blocks database access`,async()=>{
  const h=isolated({read});const r=await h.send();assert.equal(r.status,503);assert.equal(r.headers.get('set-cookie'),null);assert.deepEqual(h.calls(),{reads:1,refreshes:0,dbCalls:0});assert.ok(!(await r.text()).includes('private provider detail'));
 });
 test(`${service}: healthy verified identity reaches owner-bound read`,async()=>{const h=isolated(),r=await h.send();assert.equal(r.status,200);assert.equal(h.calls().reads,1);assert.equal(h.calls().refreshes,0);assert.ok(h.calls().dbCalls>0);assert.deepEqual(h.actors,['fixture-owner']);assert.equal(r.headers.get('set-cookie'),null)});
 test(`${service}: confirmed renewal retains HttpOnly cookie`,async()=>{const h=isolated({read:async()=>({data:{user:null},error:rejection('bad_jwt',403)})}),r=await h.send();assert.equal(r.status,200);assert.equal(h.calls().refreshes,1);assert.match(r.headers.get('set-cookie'),/HttpOnly; Secure; SameSite=Lax/)});
 test(`${service}: rejected refresh ends invalid session`,async()=>{const h=isolated({read:async()=>({data:{user:null},error:rejection('bad_jwt',403)}),refresh:async()=>({data:{user:null,session:null},error:rejection('validation_failed',400)})}),r=await h.send();assert.equal(r.status,401);assert.match(r.headers.get('set-cookie'),/Max-Age=0/);assert.equal(h.calls().dbCalls,0)});
 test(`${service}: refresh outage preserves original cookie`,async()=>{const h=isolated({read:async()=>({data:{user:null},error:rejection('bad_jwt',403)}),refresh:async()=>({data:{user:null,session:null},error:{status:503,name:'AuthRetryableFetchError'}})}),r=await h.send();assert.equal(r.status,503);assert.equal(r.headers.get('set-cookie'),null);assert.equal(h.calls().dbCalls,0)});
 test(`${service}: malformed replacement cannot grant access`,async()=>{const h=isolated({read:async()=>({data:{user:null},error:rejection('bad_jwt',403)}),refresh:async()=>({data:{user,session:{access_token:42,refresh_token:'fixture-refresh'}},error:null})}),r=await h.send();assert.equal(r.status,503);assert.equal(r.headers.get('set-cookie'),null);assert.equal(h.calls().dbCalls,0)});
 test(`${service}: no cookie never accesses provider or database`,async()=>{const h=isolated({session:null}),r=await h.send();assert.equal(r.status,401);assert.deepEqual(h.calls(),{reads:0,refreshes:0,dbCalls:0})});
 for(const field of ['access_token','refresh_token','csrf'])test(`${service}: malformed ${field} denied before provider access`,async()=>{const h=isolated({session:{access_token:'fixture-access',refresh_token:'fixture-refresh',csrf:'fixture-csrf',[field]:42}}),r=await h.send();assert.equal(r.status,401);assert.deepEqual(h.calls(),{reads:0,refreshes:0,dbCalls:0})});
 test(`${service}: repeated outages recover with original session`,async()=>{let n=0;const h=isolated({read:async()=>++n<3?{data:{user:null},error:{status:503,name:'AuthRetryableFetchError'}}:validRead()});for(let i=0;i<2;i++){const r=await h.send();assert.equal(r.status,503);assert.equal(r.headers.get('set-cookie'),null)}assert.equal((await h.send()).status,200);assert.equal(h.calls().refreshes,0)});
}
