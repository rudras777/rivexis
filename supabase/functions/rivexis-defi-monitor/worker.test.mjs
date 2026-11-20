import test from 'node:test';import assert from 'node:assert/strict';import vm from 'node:vm';
import {readFileSync} from 'node:fs';import {stripTypeScriptTypes} from 'node:module';
import {runMonitorCycle,monitorConfiguration,readBrevoResult} from './cycle.mjs';
const compiled=stripTypeScriptTypes(readFileSync(new URL('./index.ts',import.meta.url),'utf8').replace(/^import .*;\r?$/gm,''));
function harness(){
 let handler,deadline,clients=0,reads=0,cleared=0;
 const token='fixture-monitor-token'.padEnd(40,'x'),settings={RIVEXIS_DEFI_MONITOR_TOKEN:token,SUPABASE_URL:'https://fixture.invalid',SUPABASE_SERVICE_ROLE_KEY:'fixture-service'};
 const fetcher=async(_url,init)=>{reads++;assert.ok(init.signal);return new Promise((_,reject)=>{const stop=()=>reject(new DOMException('Aborted','AbortError'));if(init.signal.aborted)stop();else init.signal.addEventListener('abort',stop,{once:true})})};
 const context=vm.createContext({Deno:{env:{get:key=>settings[key]},serve:fn=>{handler=fn}},createClient:(_url,_key,options)=>{clients++;return {rpc:async()=>{await options.global.fetch('https://fixture.invalid/rest/v1/rpc/job',{method:'POST'});return {data:{},error:null}}}},
  client:()=>({getBlock:()=>assert.fail('Unexpected provider read')}),snapshot:()=>assert.fail('Unexpected snapshot'),runMonitorCycle,monitorConfiguration,readBrevoResult,fetch:fetcher,
  Request,Response,Headers,AbortController,AbortSignal,URL,console,setTimeout:(fn,ms)=>{assert.equal(ms,55000);deadline=fn;return 1},clearTimeout:()=>{cleared++}});
 new vm.Script(compiled).runInContext(context);
 return {handler,token,expire:()=>deadline(),counts:()=>({clients,reads,cleared})};
}
test('worker authentication rejects requests before database creation or provider access',async()=>{
 const h=harness();assert.equal((await h.handler(new Request('https://fixture.invalid/monitor',{method:'POST'}))).status,401);assert.equal((await h.handler(new Request('https://fixture.invalid/monitor'))).status,405);assert.deepEqual(h.counts(),{clients:0,reads:0,cleared:0});
});
test('the actual worker deadline aborts stalled database I/O and never reports a successful cycle',async()=>{
 const h=harness(),pending=h.handler(new Request('https://fixture.invalid/monitor',{method:'POST',headers:{'x-rivexis-monitor-token':h.token}}));
 assert.equal(h.counts().reads,1);h.expire();const response=await pending;assert.equal(response.status,503);assert.match((await response.json()).detail,/could not be confirmed/);assert.deepEqual(h.counts(),{clients:1,reads:1,cleared:1});
});
