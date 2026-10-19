import {test} from 'node:test';
import assert from 'node:assert/strict';
import {mayReleaseStrandedNavigation as allowed,runGuardedNavigation} from './navigation-driver-policy.mjs';
const ready={browserName:'firefox',expectedOrigin:'http://127.0.0.1:3000',target:'http://127.0.0.1:3000/workspace',href:'http://127.0.0.1:3000/workspace',previousHref:'about:blank',previousTimeOrigin:1,timeOrigin:2,readyState:'complete',mainPresent:true,buildPresent:true,documentStatus:200,pending:0,pageErrors:0,resourceFailures:0,serverFailures:0};
test('exact successful new-document driver signature permits one read-only release',()=>assert.equal(allowed(ready),true));
for(const [name,change] of [
 ['another engine',{browserName:'webkit'}],['invalid target',{target:'not a URL'}],['non-http target',{target:'file:///workspace',href:'file:///workspace'}],
 ['query-bearing target',{target:ready.target+'?code=secret',href:ready.href+'?code=secret'}],['fragment-bearing target',{target:ready.target+'#token',href:ready.href+'#token'}],
 ['different destination',{href:'http://127.0.0.1:3000/login'}],['different origin',{href:'https://example.invalid/workspace'}],['unexpected target origin',{expectedOrigin:'https://example.invalid'}],['unapproved route',{target:'http://127.0.0.1:3000/logout',href:'http://127.0.0.1:3000/logout'}],
 ['uncommitted old document',{previousHref:ready.href,previousTimeOrigin:2}],['loading document',{readyState:'loading'}],['missing main',{mainPresent:false}],['missing app identity',{buildPresent:false}],
 ['failed document',{documentStatus:500}],['redirect response',{documentStatus:302}],['invalid timing',{timeOrigin:NaN}],
 ['unfinished requests',{pending:1}],['JavaScript error',{pageErrors:1}],['failed resource',{resourceFailures:1}],['server failure',{serverFailures:1}],
])test('never release navigation with '+name,()=>assert.equal(allowed({...ready,...change}),false));
test('same URL requires independently changed document timing',()=>assert.equal(allowed({...ready,previousHref:ready.href,previousTimeOrigin:1}),true));
const timeout=()=>Object.assign(new Error('controlled driver timeout'),{name:'TimeoutError'});
test('successful first navigation is returned without inspection, log or replay',async()=>{
  const result=await runGuardedNavigation({initial:async()=>17,inspect:async()=>assert.fail('unexpected inspection'),release:async()=>assert.fail('unexpected release'),record:()=>assert.fail('unexpected log')});
  assert.equal(result,17);
});
test('non-timeout error is preserved without inspection or replay',async()=>{
  const error=new Error('real navigation failure');
  await assert.rejects(runGuardedNavigation({initial:async()=>{throw error},inspect:async()=>assert.fail('unexpected inspection'),release:async()=>assert.fail('unexpected release'),record:()=>assert.fail('unexpected log')}),e=>e===error);
});
for(const [name,evidence] of [['incomplete', {...ready,pending:1}],['real page error',{...ready,pageErrors:1}],['unknown',null],['credential URL',{...ready,target:ready.target+'?code=secret',href:ready.href+'?code=secret'}]])test('original timeout retained for '+name,async()=>{
  const error=timeout();await assert.rejects(runGuardedNavigation({initial:async()=>{throw error},inspect:async()=>evidence,release:async()=>assert.fail('unsafe replay'),record:()=>assert.fail('unsafe log')}),e=>e===error);
});
test('verified driver signature logs once and releases exactly once',async()=>{
  let attempts=0,releases=0,logs=0;
  assert.equal(await runGuardedNavigation({initial:async()=>{attempts++;throw timeout()},inspect:async()=>ready,release:async()=>{releases++;return 23},record:e=>{logs++;assert.equal(e,ready)}}),23);
  assert.deepEqual({attempts,releases,logs},{attempts:1,releases:1,logs:1});
});
test('release failure propagates without a second release or recursive retry',async()=>{
  const error=timeout();let releases=0;
  await assert.rejects(runGuardedNavigation({initial:async()=>{throw timeout()},inspect:async()=>ready,release:async()=>{releases++;throw error},record:()=>{}}),e=>e===error);
  assert.equal(releases,1);
});
