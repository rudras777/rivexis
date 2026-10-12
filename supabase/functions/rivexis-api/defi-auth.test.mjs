// Exercise the actual Edge request handler. Only Supabase identity/DB I/O is
// stubbed; request routing, cookie decoding, CSRF and DeFi preflight are real.
import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {readFileSync} from 'node:fs';
import {stripTypeScriptTypes} from 'node:module';
import {webcrypto} from 'node:crypto';
import {accountSettings} from './defi-account-settings.mjs';
import {DEFAULT_PREFERENCES} from './account-preferences.mjs';
import {handleDefi} from './defi-http.mjs';
import {handleOnChain} from './onchain-http.mjs';
import {parseRole,roleOrDefault} from './role.mjs';
const source=readFileSync(new URL('./index.ts',import.meta.url),'utf8').replace(/^import .*;\r?$/gm,'');
const compiled=stripTypeScriptTypes(source);
const wallet='0x'+'1'.repeat(40),csrf='test-csrf';
function harness({verified=true,refresh=false,otpError=false,otpSession=true,updateError=false,revokeError=false}={}){
  let handler,quotaCalls=0,updates=0;const revocations=[];
  const user={id:'test-owner',email:'test@example.invalid',email_confirmed_at:verified?'2026-10-10T00:00:00Z':null,user_metadata:{role:'Individual',email_verified:true}};
  const reports={select:()=>reports,eq:()=>reports,order:()=>reports,limit:async()=>({data:[]})};
  const admin={from:()=>reports,rpc:async(name)=>{if(name==='rivexis_defi_quota'){quotaCalls++;return {data:false}}return {data:{role:'Individual'}}}};
  const identity={auth:{admin:{updateUserById:async(id,payload)=>({data:{user:{...user,id,user_metadata:payload.user_metadata}}}),signOut:async()=>({error:null})},verifyOtp:async()=>({data:{user,session:otpSession?{access_token:'test-access',refresh_token:'test-refresh'}:null},error:otpError?{message:'invalid'}:null}),signUp:async()=>({data:{user,session:{access_token:'test-access',refresh_token:'test-refresh'}},error:null}),getUser:async(token)=>({data:{user:token==='test-access'?user:null}}),refreshSession:async()=>({data:refresh?{user,session:{access_token:'test-access',refresh_token:'new-test-refresh'}}:{user:null,session:null},error:refresh?null:{message:'invalid'}})}};
  const createClient=()=>{
    let established=false;
    return {...admin,auth:{...identity.auth,
      verifyOtp:async(input)=>{const result=await identity.auth.verifyOtp(input);established=Boolean(!result.error&&result.data.session);return result},
      setSession:async(input)=>{established=input.access_token==='test-access'&&input.refresh_token==='test-refresh';return {data:{session:established?input:null},error:established?null:{message:'invalid'}}},
      updateUser:async()=>{if(!established)return {error:{message:'Auth session missing'}};updates++;return {error:updateError?{message:'provider failed'}:null}},
      signOut:async(input)=>{if(!established)return {error:{message:'Auth session missing'}};revocations.push(input.scope);return {error:revokeError?{message:'provider failed'}:null}},
    }};
  };
  const context=vm.createContext({Deno:{env:{get:()=>''},serve:fn=>{handler=fn}},createClient,handleDefi,handleOnChain,accountSettings,parseRole,roleOrDefault,Response,Request,Headers,URL,TextEncoder,TextDecoder,Uint8Array,crypto:webcrypto,atob,btoa,console});
  new vm.Script(compiled).runInContext(context);
  const cookie=(access='test-access')=>'rvx_session='+Buffer.from(JSON.stringify({access_token:access,refresh_token:'test-refresh',csrf})).toString('base64url');
  const request=(path,{authenticated=false,token=csrf,access='test-access',method='POST',body={wallet}}={})=>new Request('https://example.com'+path,{method,headers:{...(authenticated?{cookie:cookie(access)}:{}),...(token?{'x-rivexis-csrf':token}:{})},...(method==='POST'?{body:JSON.stringify(body)}:{})});
  return {handler,request,quota:()=>quotaCalls,updates:()=>updates,revocations};
}
test('public session status exposes two booleans, never identity or session tokens',async()=>{
  const h=harness();
  const guest=await h.handler(h.request('/api/v1/auth/session-status',{method:'GET'}));
  assert.equal(guest.status,200);assert.deepEqual(await guest.json(),{authenticated:false,email_verified:false});
  const member=await h.handler(h.request('/api/v1/auth/session-status',{method:'GET',authenticated:true}));
  assert.deepEqual(await member.json(),{authenticated:true,email_verified:true});assert.equal(h.quota(),0);
  assert.equal(member.headers.get('set-cookie'),null,'A valid unrefreshed session must keep its existing cookie');
  const forged=await h.handler(h.request('/api/v1/auth/session-status',{method:'GET',authenticated:true,access:'forged-access'}));
  assert.deepEqual(await forged.json(),{authenticated:false,email_verified:false});assert.match(forged.headers.get('set-cookie'),/Max-Age=0/);
  const refreshed=harness({refresh:true});const refreshedStatus=await refreshed.handler(refreshed.request('/api/v1/auth/session-status',{method:'GET',authenticated:true,access:'expired-access'}));
  assert.deepEqual(await refreshedStatus.json(),{authenticated:true,email_verified:true});assert.match(refreshedStatus.headers.get('set-cookie'),/HttpOnly; Secure; SameSite=Lax/);assert.ok(!refreshedStatus.headers.get('set-cookie').includes('Max-Age=0'));
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
  for(const [path,method] of [['/api/v1/defi/snapshot','POST'],['/api/v1/defi-reports','GET'],['/api/v1/defi-reports','POST'],['/api/v1/workspaces','GET'],['/api/v1/reports','GET']]){
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

const authPost=(path)=>new Request('https://example.com'+path,{method:'POST',body:JSON.stringify({email:'test@example.invalid',token:'test-only-code',password:'test-only-password',role:'Individual'})});
test('signup cannot issue a workspace session for an unconfirmed trusted identity',async()=>{
 const h=harness({verified:false});const response=await h.handler(authPost('/api/v1/auth/web/signup'));
 assert.equal(response.status,200);assert.equal((await response.json()).verification_required,true);assert.equal(response.headers.get('set-cookie'),null);
});

test('recovery updates the same established client session for hash, code and implicit contracts',async()=>{
 for(const credential of [{token_hash:'test-hash'},{email:'test@example.invalid',token:'test-code'},{access_token:'test-access',refresh_token:'test-refresh'}]){
  const h=harness();const response=await h.handler(new Request('https://example.com/functions/v1/rivexis-api/api/v1/auth/password-reset/confirm',{method:'POST',body:JSON.stringify({...credential,password:'new-test-password'})}));
  assert.equal(response.status,200);assert.deepEqual(await response.json(),{status:'updated',sessions_revoked:true,access_tokens_may_remain_valid_until_expiry:true});
  assert.equal(h.updates(),1);assert.deepEqual(h.revocations,['global']);assert.match(response.headers.get('set-cookie'),/Max-Age=0; HttpOnly; Secure/);
 }
});
test('invalid recovery and failed password updates cannot claim success or revoke sessions',async()=>{
 for(const options of [{otpError:true},{otpSession:false},{updateError:true}]){
  const h=harness(options);const response=await h.handler(authPost('/api/v1/auth/password-reset/confirm'));
  assert.equal(response.status,400);assert.deepEqual(h.revocations,[]);assert.equal(response.headers.get('set-cookie'),null);
 }
});
test('successful recovery reports incomplete revocation truthfully without claiming password failure',async()=>{
 const h=harness({revokeError:true});const response=await h.handler(authPost('/api/v1/auth/password-reset/confirm'));
 assert.equal(response.status,200);assert.equal((await response.json()).sessions_revoked,false);assert.equal(h.updates(),1);assert.deepEqual(h.revocations,['global']);
});
test('verified signup OTP issues an HttpOnly session and CSRF without exposing bearer tokens',async()=>{
 const h=harness();const response=await h.handler(authPost('/api/v1/auth/email-verification/confirm'));
 const result=await response.json();assert.equal(result.authenticated,true);assert.ok(result.csrf_token);assert.equal(result.status,'verified');assert.ok(!JSON.stringify(result).includes('test-access'));assert.match(response.headers.get('set-cookie'),/HttpOnly; Secure; SameSite=Lax/);
 for(const options of [{verified:false},{otpError:true}]){const invalid=await harness(options).handler(authPost('/api/v1/auth/email-verification/confirm'));assert.equal(invalid.status,400);assert.equal(invalid.headers.get('set-cookie'),null)}
 const fallback=await harness({otpSession:false}).handler(authPost('/api/v1/auth/email-verification/confirm'));assert.equal((await fallback.json()).authenticated,false);assert.equal(fallback.headers.get('set-cookie'),null);
});


test('actual Edge routing normalizes Supabase function prefixes for every account endpoint',async()=>{
 const h=harness(),prefix='/functions/v1/rivexis-api/api/v1/account';
 const headers=h.request('/api/v1/account/settings',{authenticated:true,method:'GET'}).headers;
 const get=await h.handler(new Request('https://example.com'+prefix+'/settings',{headers}));assert.equal(get.status,200);assert.equal((await get.json()).profile.emailVerified,true);
 const patch=await h.handler(new Request('https://example.com'+prefix+'/settings',{method:'PATCH',headers,body:JSON.stringify({displayName:'Prefixed owner',preferences:DEFAULT_PREFERENCES})}));assert.equal(patch.status,200);assert.equal((await patch.json()).profile.displayName,'Prefixed owner');
 const exported=await h.handler(new Request('https://example.com'+prefix+'/export',{headers}));assert.equal(exported.status,200);assert.deepEqual((await exported.json()).reports,[]);
 const others=await h.handler(new Request('https://example.com'+prefix+'/sessions/others',{method:'POST',headers,body:JSON.stringify({confirm:true})}));assert.equal(others.status,200);assert.equal((await others.json()).accessTokensMayRemainValidUntilExpiry,true);assert.equal(h.quota(),0);
 for(const path of ['/settings','/export','/sessions/others'])assert.equal((await h.handler(new Request('https://example.com'+prefix+path))).status,401);
 const unverified=harness({verified:false});assert.equal((await unverified.handler(new Request('https://example.com'+prefix+'/settings',{headers}))).status,403);
 const noCsrf=new Headers(headers);noCsrf.delete('x-rivexis-csrf');assert.equal((await h.handler(new Request('https://example.com'+prefix+'/settings',{method:'PATCH',headers:noCsrf,body:'{}'}))).status,403);
});

test('on-chain routes require verified identity and matching CSRF before quota',async()=>{
 for(const path of ['/api/v1/on-chain/contract','/api/v1/on-chain/read','/api/v1/on-chain/wallet','/api/v1/on-chain/network']){const h=harness();assert.equal((await h.handler(h.request(path))).status,401);assert.equal((await h.handler(h.request(path,{authenticated:true,token:'wrong'}))).status,403);const unverified=harness({verified:false});assert.equal((await unverified.handler(unverified.request(path,{authenticated:true}))).status,403);assert.equal(h.quota(),0);assert.equal(unverified.quota(),0)}
 const h=harness();assert.equal((await h.handler(h.request('/api/v1/on-chain/contract',{authenticated:true,body:{chainId:1,address:wallet}}))).status,429);assert.equal(h.quota(),1);
});
