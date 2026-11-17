import {test} from 'node:test';
import assert from 'node:assert/strict';
import {auditCloudflare,accountId} from './audit-rvea-cloudflare.mjs';

const pagesToken='PAGES_FIXTURE_'.padEnd(48,'x'),workerToken='WORKER_FIXTURE_'.padEnd(48,'y');
const secret='MUST_NEVER_APPEAR_IN_REPORT';
const configuration=()=>({services:{RIVEXIS_WEB:{service:'rivexis-web',environment:'production'}},fail_open:false,compatibility_date:'2026-10-28',env_vars:{SECRET:{value:secret}}});
function fixtures(){return {
  project:{name:'rvea-rivexis-gateway',production_branch:'main',canonical_deployment:{id:'pages-id',deployment_trigger:{metadata:{commit_hash:'gateway-sha'}},env_vars:{SECRET:{value:secret}}},deployment_configs:{production:configuration(),preview:configuration()},build_config:{web_analytics_token:secret}},
  domains:[{name:'rivexis.rvea.info',status:'active',certificate_authority:'google',verification_data:{txt_value:secret}}],
  worker:{deployments:[{id:'deployment-id',created_on:'2026-11-13T10:40:00Z',versions:[{version_id:'version-id',percentage:100}],author_email:secret,annotations:{'workers/message':secret}}]},
}}
function fetchFixture(data,requests=[]){return async(url,options)=>{
  requests.push({url,options});
  const value=url.endsWith('/domains')?data.domains:url.endsWith('/deployments')?data.worker:data.project;
  return {ok:true,status:200,json:async()=>({success:true,result:value})};
}}
const run=(data,fetcher=fetchFixture(data))=>auditCloudflare({pagesToken,workerToken,fetcher,now:()=>new Date('2026-11-17T00:00:00Z')});

test('only fixed account GET endpoints receive the corresponding existing token; redirects are refused',async()=>{
  const requests=[];await run(fixtures(),fetchFixture(fixtures(),requests));
  assert.deepEqual(requests.map(row=>row.url),[`https://api.cloudflare.com/client/v4/accounts/${accountId}/pages/projects/rvea-rivexis-gateway`,`https://api.cloudflare.com/client/v4/accounts/${accountId}/pages/projects/rvea-rivexis-gateway/domains`,`https://api.cloudflare.com/client/v4/accounts/${accountId}/workers/scripts/rivexis-web/deployments`]);
  for(const [index,row] of requests.entries()){assert.equal(row.options.method,'GET');assert.equal(row.options.redirect,'error');assert.equal(row.options.headers.Authorization,`Bearer ${index===2?workerToken:pagesToken}`);assert.equal(row.options.body,undefined)}
});
test('report excludes credentials, arbitrary provider data, author identity and environment values',async()=>{
  const result=await run(fixtures());assert.equal(result.passed,true);
  const serialized=JSON.stringify(result);for(const value of [pagesToken,workerToken,secret,'env_vars','web_analytics_token','author_email'])assert.equal(serialized.includes(value),false);
  assert.equal(result.worker.versions[0].percentage,100);assert.equal(result.pages.production_deployment_id,'pages-id');
});
for(const [label,change] of [
  ['wrong binding',data=>data.project.deployment_configs.production.services.RIVEXIS_WEB.service='another-worker'],
  ['fail-open ingress',data=>data.project.deployment_configs.production.fail_open=true],
  ['pending domain',data=>data.domains[0].status='pending'],
  ['missing deployment',data=>data.worker.deployments=[]],
  ['incomplete traffic',data=>data.worker.deployments[0].versions[0].percentage=80],
])test(`audit fails for ${label}`,async()=>{const data=fixtures();change(data);assert.equal((await run(data)).passed,false)});
test('provider and transport errors cannot reflect secrets into diagnostic messages',async()=>{
  await assert.rejects(run(fixtures(),async()=>({ok:false,status:403,json:async()=>({success:false,errors:[{code:10000,message:secret}]})})),error=>error.message==='Cloudflare read failed (HTTP 403; codes 10000)');
  await assert.rejects(run(fixtures(),async()=>{throw new Error(secret)}),error=>error.message==='Cloudflare read transport failed');
});
test('malformed credentials are rejected before any request',async()=>{
  await assert.rejects(auditCloudflare({pagesToken:`Bearer ${pagesToken}`,workerToken,fetcher:async()=>assert.fail('Unexpected request')}),/raw deployment tokens/);
});
