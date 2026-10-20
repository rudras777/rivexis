// Real Edge routing/financial receipt construction; only external identity, RPC
// and database services are fixtures. No live users, emails or data are changed.
import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {readFileSync} from 'node:fs';
import {stripTypeScriptTypes} from 'node:module';
import {webcrypto} from 'node:crypto';
import {accountSettings} from './defi-account-settings.mjs';
import {handleDefi,validWallet,readRequestText} from './defi-http.mjs';
import {handleOnChain} from './onchain-http.mjs';
import {parseRole,roleOrDefault} from './role.mjs';
import {frontier,validateSnapshot} from './defi-unified-model.mjs';
import {liquidationAnalysis} from './defi-liquidation.mjs';
import {sampleSnapshot} from './defi-sample.mjs';
const compiled=stripTypeScriptTypes(readFileSync(new URL('./index.ts',import.meta.url),'utf8').replace(/^import .*;\r?$/gm,''));
const csrf='fixture-csrf',wallet='0x'+'1'.repeat(40);
function harness(options={}){
 let handler;const calls=[];
 const user={id:'OWNER_A',email:'owner@example.invalid',email_confirmed_at:options.unverified?null:'2026-10-12',user_metadata:{email_verified:true,role:'Individual'}};
 const query={select:()=>query,eq:(key,value)=>{calls.push({key,value});return query},order:()=>query,limit:async()=>options.dbFail?{error:{}}:{data:[{id:'OWN_REPORT',receipt:{sample:true}}]}};
 const admin={from:()=>query,rpc:async(name,args)=>{calls.push({name,args});if(name==='rivexis_defi_quota'){if(options.quotaThrow)throw Error('private provider detail');return options.quotaFail?{error:{}}:{data:options.quotaMissing?null:!options.quotaDenied}}if(name==='rivexis_defi_save_report'){if(options.saveThrow)throw Error('private provider detail');return options.saveCap?{error:{code:'P0001',message:'Report limit reached: 20 per account'}}:options.saveFail?{error:{code:'08006',message:'private database detail'}}:{data:options.saveMissing?null:options.saveInvalid?'invalid-id':'11111111-1111-4111-8111-111111111111'}}return {data:{role:'Individual'}}}};
 const createClient=()=>({...admin,auth:{getUser:async(token)=>({data:{user:token==='ACCESS_A'?user:null},error:token==='ACCESS_A'?null:{status:401,code:'bad_jwt'}}),refreshSession:async()=>({data:{},error:{status:400,code:'refresh_token_not_found'}}),setSession:async()=>{if(options.establishThrow)throw Error('provider outage');return options.establishFail?{error:{}}:{data:{session:{access_token:'ACCESS_A'}}}},signOut:async(input)=>{calls.push({signOut:input});if(options.revokeThrow)throw Error('provider outage');return {error:options.revokeFail?{}:null}}}});
 const context=vm.createContext({Deno:{env:{get:()=>''},serve:fn=>{handler=fn}},createClient,handleDefi,handleOnChain,accountSettings,parseRole,roleOrDefault,validWallet,readRequestText,frontier,validateSnapshot,liquidationAnalysis,sampleSnapshot,COVERAGE:['aave','morpho'],snapshot:async()=>{calls.push({snapshot:true});if(options.state)return options.state;throw Error('private RPC detail')},client:()=>({}),Response,Request,Headers,URL,TextEncoder,TextDecoder,Uint8Array,crypto:webcrypto,atob,btoa,console});
 new vm.Script(compiled).runInContext(context);
 const request=(path,{method='GET',body,guest=false,token=csrf,access='ACCESS_A',raw}={})=>new Request('https://example.invalid'+path,{method,headers:{...(guest?{}:{cookie:'rvx_session='+Buffer.from(JSON.stringify({access_token:access,refresh_token:'REFRESH_A',csrf})).toString('base64url')}),'x-rivexis-csrf':token},...(method==='GET'?{}:{body:raw??JSON.stringify(body??{})})});
 return {handler,request,calls};
}
for(const [name,options,revoked] of [
 ['successful provider revocation',{},true],['establishment error',{establishFail:true},false],['establishment throws',{establishThrow:true},false],['revocation error',{revokeFail:true},false],['revocation throws',{revokeThrow:true},false],
])test('logout: '+name,async()=>{
 const h=harness(options),response=await h.handler(h.request('/api/v1/auth/logout',{method:'POST'})),body=await response.json();
 assert.equal(response.status,200);assert.equal(body.refreshSessionRevoked,revoked);assert.equal(body.status,revoked?'revoked':'browser_session_cleared');assert.equal(body.accessTokensMayRemainValidUntilExpiry,true);assert.match(response.headers.get('set-cookie'),/Max-Age=0; HttpOnly; Secure; SameSite=Lax/);
 assert.ok(!JSON.stringify(body).includes('ACCESS_A'));if(!options.establishFail&&!options.establishThrow)assert.equal(h.calls.find(c=>c.signOut)?.signOut.scope,'local');
});
for(const [name,input,status] of [['guest',{guest:true},401],['forged token',{access:'ATTACKER'},401],['wrong csrf',{token:'ATTACKER'},403],['missing csrf',{token:''},403]])test('logout rejects '+name,async()=>{
 const h=harness(),response=await h.handler(h.request('/api/v1/auth/logout',{method:'POST',...input}));assert.equal(response.status,status);assert.ok(!h.calls.some(c=>c.signOut));
});
test('logout repeated requests revoke only the current fixture session',async()=>{const h=harness();for(let i=0;i<3;i++)assert.equal((await h.handler(h.request('/api/v1/auth/logout',{method:'POST'}))).status,200);assert.equal(h.calls.filter(c=>c.signOut?.scope==='local').length,3)});
const report={sample:true,budget:'1000',target:'1.5',gasReserve:'25',objective:'max-min',shocks:{}};
test('report list queries only the authenticated owner',async()=>{const h=harness(),response=await h.handler(h.request('/api/v1/defi-reports?owner_id=OWNER_B'));assert.equal(response.status,200);assert.deepEqual(h.calls.find(c=>c.key==='owner_id'),{key:'owner_id',value:'OWNER_A'});assert.equal((await response.json()).items[0].id,'OWN_REPORT')});
test('report database failure never shows an empty successful list',async()=>{const h=harness({dbFail:true});assert.equal((await h.handler(h.request('/api/v1/defi-reports'))).status,503)});
test('sample report is clearly classified and rebuilt using real financial model',async()=>{const h=harness(),response=await h.handler(h.request('/api/v1/defi-reports',{method:'POST',body:report}));assert.equal(response.status,201);const body=await response.json();assert.equal(body.receipt.sample,true);assert.equal(body.receipt.classification,'MODEL_COMPARISON_NOT_EXECUTION');assert.equal(h.calls.find(c=>c.name==='rivexis_defi_save_report').args.p_owner,'OWNER_A');assert.ok(!h.calls.some(c=>c.name==='rivexis_defi_quota'))});
for(const [name,body,raw] of [['malformed JSON',null,'{'],['array',[]],['numeric capital',{...report,budget:1000}],['negative budget',{...report,budget:'-1'}],['fee exceeds capital',{...report,gasReserve:'1001'}],['unsupported objective',{...report,objective:'guarantee-safe'}],['invalid health target',{...report,target:'0.5'}],['oversized stream',null,'x'.repeat(8193)]])test('report rejects '+name,async()=>{const h=harness(),response=await h.handler(h.request('/api/v1/defi-reports',{method:'POST',body,raw}));assert.ok([413,422].includes(response.status));assert.ok(!h.calls.some(c=>c.name==='rivexis_defi_save_report'))});
for(const [name,options,status] of [['quota exhausted',{quotaDenied:true},429],['quota outage',{quotaFail:true},503],['RPC outage',{},503]])test('live report '+name+' never persists invented evidence',async()=>{const h=harness(options);assert.equal((await h.handler(h.request('/api/v1/defi-reports',{method:'POST',body:{...report,sample:false,wallet}}))).status,status);assert.ok(!h.calls.some(c=>c.name==='rivexis_defi_save_report'))});
test('confirmed report cap returns conflict rather than fake save',async()=>{const h=harness({saveCap:true});assert.equal((await h.handler(h.request('/api/v1/defi-reports',{method:'POST',body:report}))).status,409)});
test('report generation repeated operations remain owner-bound',async()=>{const h=harness();for(let i=0;i<3;i++)assert.equal((await h.handler(h.request('/api/v1/defi-reports',{method:'POST',body:{...report,owner_id:'OWNER_B'}}))).status,201);assert.equal(h.calls.filter(c=>c.name==='rivexis_defi_save_report'&&c.args.p_owner==='OWNER_A').length,3)});

for(const [name,options] of [['database error',{saveFail:true}],['database exception',{saveThrow:true}],['missing save confirmation',{saveMissing:true}],['invalid save confirmation',{saveInvalid:true}]])test('report '+name+' is recoverable and never claims the allowance is full',async()=>{const h=harness(options),r=await h.handler(h.request('/api/v1/defi-reports',{method:'POST',body:report})),b=await r.json();assert.equal(r.status,503);assert.match(b.detail,/Check saved reports before retrying/);assert.ok(!JSON.stringify(b).includes('private'));assert.equal(b.id,undefined);assert.equal(b.receipt,undefined)});
for(const [name,options] of [['quota exception',{quotaThrow:true}],['missing quota confirmation',{quotaMissing:true}]])test('report '+name+' blocks RPC and persistence',async()=>{const h=harness(options),r=await h.handler(h.request('/api/v1/defi-reports',{method:'POST',body:{...report,sample:false,wallet}}));assert.equal(r.status,503);assert.ok(!h.calls.some(c=>c.snapshot||c.name==='rivexis_defi_save_report'));assert.ok(!(await r.text()).includes('private'))});
for(const [name,mutate,status] of [['stale evidence',s=>{s.blockTimestamp=Math.floor(Date.now()/1000)-181},503],['invalid evidence',s=>{s.positions[0].reserves[0].priceRaw='0'},503],['unsupported coverage',s=>{s.status='UNSUPPORTED'},422]])test('report '+name+' cannot be persisted',async()=>{const state=sampleSnapshot();mutate(state);const h=harness({state}),r=await h.handler(h.request('/api/v1/defi-reports',{method:'POST',body:{...report,sample:false,wallet}}));assert.equal(r.status,status);assert.ok(!h.calls.some(c=>c.name==='rivexis_defi_save_report'));assert.equal((await r.json()).receipt,undefined)});
test('valid report after a provider recovery uses newly acquired evidence',async()=>{const h=harness({state:sampleSnapshot()});for(let i=0;i<3;i++){const r=await h.handler(h.request('/api/v1/defi-reports',{method:'POST',body:{...report,sample:false,wallet}}));assert.equal(r.status,201)}assert.equal(h.calls.filter(c=>c.snapshot).length,3)});
