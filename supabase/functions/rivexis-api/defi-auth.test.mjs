// Exercise the actual Edge request handler. Only Supabase identity/DB I/O is
// stubbed; request routing, cookie decoding, CSRF and DeFi preflight are real.
import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {readFileSync} from 'node:fs';
import {stripTypeScriptTypes} from 'node:module';
import {webcrypto} from 'node:crypto';
import {handleDefi} from './defi-http.mjs';
import {roleOrDefault} from './role.mjs';
const source=readFileSync(new URL('./index.ts',import.meta.url),'utf8').replace(/^import .*;\r?$/gm,'');
const compiled=stripTypeScriptTypes(source);
const wallet='0x'+'1'.repeat(40),csrf='test-csrf';
function harness({verified=true,refresh=false}={}){
  let handler,quotaCalls=0;
  const user={id:'test-owner',email:'test@example.invalid',email_confirmed_at:verified?'2026-10-10T00:00:00Z':null,user_metadata:{role:'Individual',email_verified:true}};
  const admin={rpc:async(name)=>{if(name==='rivexis_defi_quota'){quotaCalls++;return {data:false}}return {data:{role:'Individual'}}}};
  const identity={auth:{getUser:async(token)=>({data:{user:token==='test-access'?user:null}}),refreshSession:async()=>({data:refresh?{user,session:{access_token:'test-access',refresh_token:'new-test-refresh'}}:{user:null,session:null},error:refresh?null:{message:'invalid'}})}};
  const context=vm.createContext({Deno:{env:{get:()=>''},serve:fn=>{handler=fn}},createClient:()=>({...admin,...identity}),handleDefi,roleOrDefault,Response,Request,Headers,URL,TextEncoder,TextDecoder,Uint8Array,crypto:webcrypto,atob,btoa,console});
  new vm.Script(compiled).runInContext(context);
  const cookie=(access='test-access')=>'rvx_session='+Buffer.from(JSON.stringify({access_token:access,refresh_token:'test-refresh',csrf})).toString('base64url');
  const request=(path,{authenticated=false,token=csrf,access='test-access',method='POST'}={})=>new Request('https://example.com'+path,{method,headers:{...(authenticated?{cookie:cookie(access)}:{}),...(token?{'x-rivexis-csrf':token}:{})},...(method==='POST'?{body:JSON.stringify({wallet})}:{})});
  return {handler,request,quota:()=>quotaCalls};
}
test('public session status exposes two booleans, never identity or session tokens',async()=>{
  const h=harness();
  const guest=await h.handler(h.request('/api/v1/auth/session-status',{method:'GET'}));
  assert.equal(guest.status,200);assert.deepEqual(await guest.json(),{authenticated:false,email_verified:false});
  const member=await h.handler(h.request('/api/v1/auth/session-status',{method:'GET',authenticated:true}));
  assert.deepEqual(await member.json(),{authenticated:true,email_verified:true});assert.equal(h.quota(),0);
});
test('guest and forged sessions cannot reach live DeFi quota or RPC',async()=>{
  for(const path of ['/api/v1/defi/snapshot','/api/v1/defi/transaction']){
    const h=harness();
    assert.equal((await h.handler(h.request(path))).status,401);
    assert.equal((await h.handler(h.request(path,{authenticated:true,access:'forged-access'}))).status,401);
    assert.equal(h.quota(),0);
  }
});
test('user-editable metadata cannot bypass required email verification',async()=>{
  const h=harness({verified:false});
  for(const [path,method] of [['/api/v1/defi/snapshot','POST'],['/api/v1/defi-reports','GET'],['/api/v1/defi-reports','POST']]){
    const response=await h.handler(h.request(path,{authenticated:true,method}));
    assert.equal(response.status,403);assert.match((await response.json()).detail,/verification/);assert.equal(h.quota(),0);
  }
});
test('verified sessions still require the matching server CSRF token',async()=>{
  const h=harness();
  for(const token of [null,'wrong-csrf'])assert.equal((await h.handler(h.request('/api/v1/defi/snapshot',{authenticated:true,token}))).status,403);
  assert.equal(h.quota(),0);
});
test('verified CSRF-authenticated requests reach the unchanged distributed quota gate',async()=>{
  const h=harness();
  const response=await h.handler(h.request('/api/v1/defi/snapshot',{authenticated:true}));
  assert.equal(response.status,429);assert.equal(h.quota(),1);
});
test('refreshed sessions propagate the secure cookie through DeFi responses',async()=>{
  const h=harness({refresh:true});
  const response=await h.handler(h.request('/api/v1/defi/snapshot',{authenticated:true,access:'expired-access'}));
  assert.equal(response.status,429);assert.equal(h.quota(),1);
  const cookie=response.headers.get('set-cookie');assert.ok(cookie?.startsWith('rvx_session='));assert.match(cookie,/HttpOnly; Secure; SameSite=Lax/);
});
