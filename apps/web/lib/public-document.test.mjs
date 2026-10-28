import {test} from 'node:test';
import assert from 'node:assert/strict';
import {publicDocument,PUBLIC_DOCUMENT_ASSET} from './public-document.ts';
import {BASE_SECURITY_HEADERS} from './security-headers.mjs';
const origin='https://rivexis-web.rudrasingh0718.workers.dev';
function harness(status=200){const calls=[];return {calls,fetch:async request=>{calls.push(request);return new Response('<html>BUILD_ONLY</html>',{status,headers:{'set-cookie':'MUST_NOT_FORWARD','content-type':'text/html'}})}}}

test('public landing comes from the build artifact with unchanged security and no cookie',async()=>{
 const assets=harness();const r=await publicDocument(new Request(origin),assets);assert.equal(r.status,200);assert.equal(await r.text(),'<html>BUILD_ONLY</html>');assert.equal(r.headers.get('x-rivexis-document'),'build');assert.equal(r.headers.get('set-cookie'),null);
 for(const [name,value] of Object.entries(BASE_SECURITY_HEADERS))assert.equal(r.headers.get(name),value);
 assert.equal(r.headers.get('cache-control'),'public, max-age=0, must-revalidate');assert.equal(assets.calls[0].url,origin+PUBLIC_DOCUMENT_ASSET);
});
test('HEAD returns headers and never emits an HTML body',async()=>{const assets=harness();const r=await publicDocument(new Request(origin,{method:'HEAD'}),assets);assert.equal(r.status,200);assert.equal(await r.text(),'');assert.equal(assets.calls[0].method,'HEAD')});
test('sessions, credentials and conditional visitor headers never reach the static asset request',async()=>{
 const assets=harness();await publicDocument(new Request(origin+'/?utm_source=example',{headers:{cookie:'test-only-session',authorization:'Bearer test-only-token','if-none-match':'visitor-etag','x-rivexis-build-render':'1'}}),assets);
 assert.equal([...assets.calls[0].headers].length,0);assert.equal(new URL(assets.calls[0].url).search,'');
});
for(const [label,query,headers] of [
 ['Flight flag','',{RSC:'1'}],['Flight query','?_rsc=example',{}],['router state','',{'Next-Router-State-Tree':'[]'}],['prefetch','',{'Next-Router-Prefetch':'1'}],['Flight Accept','',{accept:'text/x-component'}],
])test(`${label} retains the framework response protocol`,async()=>{const assets=harness();assert.equal(await publicDocument(new Request(origin+'/'+query,{headers}),assets),null);assert.equal(assets.calls.length,0)});
for(const pathname of ['/api/v1/auth/session-status','/api/v1/account/settings','/api/v1/defi-reports','/workspace/overview','/workspace/settings','/login','/reset-password'])test(`${pathname} never uses a shared public document`,async()=>{const assets=harness();assert.equal(await publicDocument(new Request(origin+pathname),assets),null);assert.equal(assets.calls.length,0)});
for(const method of ['POST','PUT','PATCH','DELETE','OPTIONS'])test(`${method} stays with the framework and upstream security controls`,async()=>{const assets=harness();assert.equal(await publicDocument(new Request(origin,{method}),assets),null);assert.equal(assets.calls.length,0)});
for(const status of [404,500])test(`asset ${status} fails closed instead of repeatedly rendering under load`,async()=>{const r=await publicDocument(new Request(origin),harness(status));assert.equal(r.status,503);assert.equal(r.headers.get('cache-control'),'no-store');assert.equal(r.headers.get('set-cookie'),null);assert.equal(r.headers.has('x-rivexis-document'),false)});
test('asset-provider failure is an honest unavailable response without internal details',async()=>{const r=await publicDocument(new Request(origin),{fetch:async()=>{throw new Error('private diagnostic')}});assert.equal(r.status,503);assert.doesNotMatch(await r.text(),/private diagnostic/)});
