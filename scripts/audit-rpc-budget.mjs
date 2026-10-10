// Read-only operator audit of public reference wallets. No sessions, signing or submission.
import {writeFile,readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {snapshot,gasguard} from '../supabase/functions/rivexis-api/defi-portfolio-rpc.mjs';
import {validateSnapshot,metrics} from '../supabase/functions/rivexis-api/defi-unified-model.mjs';

const originalFetch=globalThis.fetch;
let active=null;
globalThis.fetch=async(input,init)=>{
  const start=Date.now(),entry={methods:[],status:null,elapsedMs:null};
  if(active)active.requests.push(entry);
  try{
    const body=JSON.parse(init?.body??'null');
    entry.methods=(Array.isArray(body)?body:[body]).filter(Boolean).map(x=>x.method);
  }catch{/* Record transport counts without storing request payloads. */}
  try{const response=await originalFetch(input,init);entry.status=response.status;return response;}
  finally{entry.elapsedMs=Date.now()-start;}
};
const report={checkedAt:new Date().toISOString(),sourceSha:execFileSync('git',['rev-parse','HEAD'],{encoding:'utf8'}).trim(),
  protocolReaderHashes:Object.fromEntries(await Promise.all(['defi-rpc.mjs','defi-portfolio-rpc.mjs'].map(async name=>[name,createHash('sha256').update(await readFile(new URL('../supabase/functions/rivexis-api/'+name,import.meta.url))).digest('hex')]))),
  endpoint:'https://ethereum.publicnode.com',classification:'DIRECT_PUBLIC_RPC_READ_AUDIT_NOT_AUTHENTICATED_CAPACITY_CERTIFICATION',
  retryCount:0,transportTimeoutMs:12000,results:[],
  limitations:['Two sequential public-wallet samples do not certify concurrent capacity, provider allowance or infrastructure billing.',
    'RPC/contract failures are recorded without retry or substituting fabricated evidence.',
    'Requests bypass the application only to audit its unchanged protocol readers; this does not prove production authentication.']};
try{
  for(const fixture of [
    {operation:'snapshot',coverage:'aave',wallet:'0x6164eb38bADD2d7A8ab87CD9939ddAcfbB007f18'},
    {operation:'snapshot',coverage:'combined',wallet:'0x4D9bf9F734B817298A4c0bC250c30527379cbE34'},
    {operation:'transaction',coverage:'aave',wallet:'0x6164eb38bADD2d7A8ab87CD9939ddAcfbB007f18',kind:'withdraw',asset:'0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2',amount:'0.001'},
    {operation:'transaction',coverage:'combined',wallet:'0x4D9bf9F734B817298A4c0bC250c30527379cbE34',kind:'withdraw',asset:'0x2260fac5e5542a773aa44fbcfedf7c193bc2c599',amount:'0.00001'},
  ]){
    active={...fixture,publicReferenceWalletNotUserOwned:true,requests:[]};
    report.results.push(active);const start=Date.now();
    try{
      const state=fixture.operation==='transaction'?await gasguard(fixture):await snapshot(fixture.wallet,undefined,fixture.coverage);
      if(fixture.operation==='snapshot')validateSnapshot(state);
      active.status=state.status;active.blockNumber=state.blockNumber;active.blockHash=state.blockHash;
      if(fixture.operation==='snapshot'){
        active.positions=state.positions.map(p=>({protocol:p.protocol,healthFactorRaw:metrics(p).healthFactorRaw}));
        active.observedHealthFactorRaw=state.observedHealthFactorRaw;
      }else{
        active.simulation=state.simulation;active.nonceAtBlock=state.nonceAtBlock;active.gasRaw=state.gasRaw;
        active.beforeHealthFactorRaw=state.before.healthFactorRaw;active.afterHealthFactorRaw=state.after.healthFactorRaw;
      }
    }catch(error){active.status='FAILED_CLOSED';active.errorName=error.name;}
    active.elapsedMs=Date.now()-start;active.httpRequests=active.requests.length;
    active.rpcCalls=active.requests.reduce((n,r)=>n+r.methods.length,0);
  }
}finally{
  globalThis.fetch=originalFetch;
  await writeFile('certification-reports/rpc-budget-audit.json',JSON.stringify(report,null,2)+'\n');
}
console.log(JSON.stringify({classification:report.classification,results:report.results.map(({requests,...r})=>r)},null,2));
if(report.results.some(r=>r.operation==='snapshot'?r.status!=='READY':r.status!=='PREVIEW_ONLY'||r.simulation!=='SUCCEEDED_AT_BLOCK'))process.exitCode=1;
