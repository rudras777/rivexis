import {test,afterEach} from 'node:test';
import assert from 'node:assert/strict';
import {proxyEdgeApi} from './edge-api-proxy.ts';

const origin='https://rivexis-web.rudrasingh0718.workers.dev';
const realFetch=globalThis.fetch;
afterEach(()=>{globalThis.fetch=realFetch;delete process.env.RIVEXIS_E2E_BLOCK_EXTERNAL_UPSTREAM});
function harness(){
 const calls=[];
 globalThis.fetch=async(url,init)=>{calls.push({url:String(url),init});return new Response('{"upstream":true}',{headers:{'set-cookie':'test-only-cookie','content-encoding':'gzip','content-length':'17'}})};
 return calls;
}
function request({path='/api/v1/auth/web/login',method='POST',headers={},body='{}'}={}){
 return new Request(origin+path,{method,headers,...(!['GET','HEAD'].includes(method)?{body,...(body instanceof ReadableStream?{duplex:'half'}:{})}:{})});
}
for(const method of ['POST','PUT','PATCH','DELETE'])test(`${method}: foreign origin is denied before upstream or cookie creation`,async()=>{
 const calls=harness();const result=await proxyEdgeApi(request({method,headers:{origin:'https://untrusted.example'}}),'/api/v1/auth/web/login');
 assert.equal(result.status,403);assert.equal(calls.length,0);assert.equal(result.headers.get('set-cookie'),null);assert.equal(result.headers.get('cache-control'),'no-store');
});
for(const supplied of ['null',origin+'.untrusted.example','http://rivexis-web.rudrasingh0718.workers.dev',origin+':444'])test(`origin ${supplied} is not the exact request origin`,async()=>{
 const calls=harness();assert.equal((await proxyEdgeApi(request({headers:{origin:supplied}}),'/api/v1/auth/web/login')).status,403);assert.equal(calls.length,0);
});
test('cross-site fetch metadata is rejected even without Origin',async()=>{
 const calls=harness();assert.equal((await proxyEdgeApi(request({headers:{'sec-fetch-site':'cross-site'}}),'/api/v1/auth/web/signup')).status,403);assert.equal(calls.length,0);
});
test('fetch metadata cannot override a foreign Origin',async()=>{
 const calls=harness();assert.equal((await proxyEdgeApi(request({headers:{origin:'https://untrusted.example','sec-fetch-site':'same-origin'}}),'/api/v1/auth/password-reset/request')).status,403);assert.equal(calls.length,0);
});
test('same-origin write preserves bytes, CSRF, cookie and response semantics',async()=>{
 const calls=harness();const payload='{"displayName":"Owner Δ"}';
 const result=await proxyEdgeApi(request({body:payload,headers:{origin,'x-rivexis-csrf':'test-csrf',cookie:'test-only-session','x-rivexis-forwarded-origin':'https://untrusted.example'}}),'/api/v1/account/settings');
 assert.equal(result.status,200);assert.equal(new TextDecoder().decode(calls[0].init.body),payload);assert.equal(calls[0].init.headers.get('x-rivexis-csrf'),'test-csrf');assert.equal(calls[0].init.headers.get('cookie'),'test-only-session');assert.equal(calls[0].init.headers.get('x-rivexis-forwarded-origin'),origin);assert.equal(result.headers.get('cache-control'),'no-store');assert.equal(result.headers.get('set-cookie'),'test-only-cookie');assert.equal(result.headers.get('content-encoding'),null);assert.equal(result.headers.get('content-length'),null);assert.equal(calls[0].init.redirect,'manual');
});
test('non-browser request without origin retains upstream authentication and CSRF responsibility',async()=>{
 const calls=harness();await proxyEdgeApi(request(),'/api/v1/defi/snapshot');assert.equal(calls.length,1);
});
test('foreign-origin GET does not become a local authorization bypass',async()=>{
 const calls=harness();await proxyEdgeApi(request({method:'GET',headers:{origin:'https://untrusted.example'}}),'/api/v1/account/settings');assert.equal(calls.length,1);assert.equal(calls[0].init.body,undefined);
});
test('same-origin local development uses the actual request origin',async()=>{
 const calls=harness();await proxyEdgeApi(new Request('http://127.0.0.1:3019/api/v1/auth/web/login',{method:'POST',headers:{origin:'http://127.0.0.1:3019'},body:'{}'}),'/api/v1/auth/web/login');assert.equal(calls.length,1);
});
test('declared oversized body is refused without forwarding',async()=>{
 const calls=harness();assert.equal((await proxyEdgeApi(request({headers:{'content-length':'131073'}}),'/api/v1/auth/web/login')).status,413);assert.equal(calls.length,0);
});
test('streamed size is enforced when Content-Length is absent',async()=>{
 const calls=harness();let cancelled=false;let chunks=0;
 const body=new ReadableStream({pull(c){if(chunks++<3)c.enqueue(new Uint8Array(65536));else c.close()},cancel(){cancelled=true}});
 const result=await proxyEdgeApi(request({body}),'/api/v1/auth/web/signup');assert.equal(result.status,413);assert.equal(calls.length,0);assert.equal(cancelled,true);
});
test('understated Content-Length cannot bypass the streamed byte limit',async()=>{
 const calls=harness();assert.equal((await proxyEdgeApi(request({headers:{'content-length':'2'},body:'a'.repeat(131073)}),'/api/v1/auth/web/login')).status,413);assert.equal(calls.length,0);
});
test('exact 128KiB boundary is forwarded byte-for-byte',async()=>{
 const calls=harness();await proxyEdgeApi(request({body:'a'.repeat(131072)}),'/api/v1/auth/web/login');assert.equal(calls.length,1);assert.equal(calls[0].init.body.byteLength,131072);
});
test('UTF-8 bytes rather than string characters determine the limit',async()=>{
 const calls=harness();assert.equal((await proxyEdgeApi(request({body:'€'.repeat(43691)}),'/api/v1/auth/web/login')).status,413);assert.equal(calls.length,0);
});
test('failed request stream produces an honest error without an upstream write',async()=>{
 const calls=harness();const body=new ReadableStream({start(c){c.error(new Error('test-only failure'))}});assert.equal((await proxyEdgeApi(request({body}),'/api/v1/account/settings')).status,400);assert.equal(calls.length,0);
});
test('empty write remains supported',async()=>{
 const calls=harness();await proxyEdgeApi(new Request(origin+'/api/v1/auth/web/logout',{method:'POST'}),'/api/v1/auth/web/logout');assert.equal(calls.length,1);assert.equal(calls[0].init.body,undefined);
});
test('sample-address protection still precedes forwarding',async()=>{
 const calls=harness();const result=await proxyEdgeApi(request({body:JSON.stringify({demo:false,input:{wallet:'0x1111111111111111111111111111111111111111'}})}),'/api/v1/analysis/portfolio');assert.equal(result.status,422);assert.equal(calls.length,0);
});
test('malformed JSON keeps the upstream canonical validation',async()=>{
 const calls=harness();await proxyEdgeApi(request({body:'{'}),'/api/v1/analysis/portfolio');assert.equal(calls.length,1);
});
test('local E2E blockade remains fail-closed after request validation',async()=>{
 const calls=harness();process.env.RIVEXIS_E2E_BLOCK_EXTERNAL_UPSTREAM='1';assert.equal((await proxyEdgeApi(request(),'/api/v1/auth/web/login')).status,503);assert.equal(calls.length,0);
});
test('report routing, query parameters and no-redirect behavior are retained',async()=>{
 const calls=harness();await proxyEdgeApi(new Request(origin+'/api/v1/history?limit=20'),'/api/v1/history');assert.equal(calls[0].url,'https://ivszvufdonfgwjpfgwii.supabase.co/functions/v1/rivexis-decision-reports/api/v1/history?limit=20');
});
