import {writeFile,mkdir} from 'node:fs/promises';
import {metrics,frontier} from '../supabase/functions/rivexis-api/defi-model.mjs';
const base=process.env.RIVEXIS_LIVE_URL||'https://rivexis-web.rudrasingh0718.workers.dev';
const results=[];
async function post(path,body){const start=Date.now(),r=await fetch(base+path,{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(body)});return {http:r.status,latencyMs:Date.now()-start,body:await r.json()}}
const wallet='0x6164eb38bADD2d7A8ab87CD9939ddAcfbB007f18'; // Public Borrow-event fixture, not an owned/test account.
const snapshot=await post('/api/v1/defi/snapshot',{wallet});
if(snapshot.http!==200||snapshot.body.status!=='READY')throw new Error('Live supported snapshot failed: '+JSON.stringify(snapshot));
const s=snapshot.body,m=metrics(s.positions[0]);
if(m.healthFactorRaw!==s.observedHealthFactorRaw)throw new Error('On-chain health factor disagreement');
results.push({test:'real_aave_account_reference',status:'PASS',latencyMs:snapshot.latencyMs,blockNumber:s.blockNumber,blockHash:s.blockHash,poolImplementation:s.poolImplementation,observedHF:s.observedHealthFactorRaw,modeledHF:m.healthFactorRaw});
const alternatives=frontier(s,{budget:'3000',gasReserve:'25',target:'1.75',shocks:{[s.positions[0].reserves[0].asset.toLowerCase()]:-2000}});
results.push({test:'real_state_defense_frontier',status:alternatives.alternatives.length?'PASS':'FAIL',examined:alternatives.examined,alternatives:alternatives.alternatives.length,meetsTarget:alternatives.meetsTarget});
const tx=await post('/api/v1/defi/transaction',{wallet,asset:'0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',kind:'withdraw',amount:'0.001'});
if(tx.http!==200||tx.body.simulation!=='SUCCEEDED_AT_BLOCK')throw new Error('Supported live transaction preview failed: '+JSON.stringify(tx));
results.push({test:'real_withdraw_readonly_simulation',status:'PASS',latencyMs:tx.latencyMs,blockNumber:tx.body.blockNumber,gas:tx.body.gasRaw,feeReserveWei:tx.body.feeReserveWei,blockers:tx.body.blockers});
const invalid=await post('/api/v1/defi/snapshot',{wallet:'bad'});results.push({test:'invalid_wallet_rejected',status:invalid.http===422?'PASS':'FAIL',http:invalid.http});
const protectedReport=await fetch(base+'/api/v1/defi-reports');results.push({test:'unauthenticated_reports_denied',status:protectedReport.status===401?'PASS':'FAIL',http:protectedReport.status});
const page=await fetch(base+'/?verify='+Date.now()),html=await page.text(),build=html.match(/name="rivexis-build" content="([^"]+)"/)?.[1];
results.push({test:'public_build_marker',status:page.ok&&build?'PASS':'FAIL',buildSha:build,transformed:html.includes('Understand the risk')});
const report={checkedAt:new Date().toISOString(),base,results};await mkdir('certification-reports',{recursive:true});await writeFile('certification-reports/defi-live-verification.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
if(results.some(r=>r.status==='FAIL'))process.exitCode=1;
