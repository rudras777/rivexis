import {writeFile,mkdir} from 'node:fs/promises';
import {metrics,frontier} from '../supabase/functions/rivexis-api/defi-model.mjs';
const base=process.env.RIVEXIS_LIVE_URL||'https://rivexis-web.rudrasingh0718.workers.dev';
const expectedBuild=process.env.RIVEXIS_EXPECTED_BUILD_SHA||'';
if(expectedBuild&&!/^[0-9a-f]{40}$/i.test(expectedBuild))throw new Error('Expected deployed source must be a full Git SHA');
const results=[];
async function post(path,body){const start=Date.now(),r=await fetch(base+path,{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(body)});return {http:r.status,latencyMs:Date.now()-start,body:await r.json()}}
const wallet='0x6164eb38bADD2d7A8ab87CD9939ddAcfbB007f18'; // Public Borrow-event fixture, not an owned/test account.
const snapshot=await post('/api/v1/defi/snapshot',{wallet});
if(snapshot.http!==200||snapshot.body.status!=='READY')throw new Error('Live supported snapshot failed: '+JSON.stringify(snapshot));
const s=snapshot.body,m=metrics(s.positions[0]);
if(m.healthFactorRaw!==s.observedHealthFactorRaw)throw new Error('On-chain health factor disagreement');
results.push({test:'real_aave_account_reference',status:'PASS',latencyMs:snapshot.latencyMs,blockNumber:s.blockNumber,blockHash:s.blockHash,poolImplementation:s.poolImplementation,observedHF:s.observedHealthFactorRaw,modeledHF:m.healthFactorRaw});
const wbtc=await post('/api/v1/defi/snapshot',{wallet:'0x1FbcadCc4c250cF1f6da6b360263A6EBC3967aA9'}); // Public Borrow-event fixture, not an owned account.
if(wbtc.http!==200||wbtc.body.status!=='READY')throw new Error('Live WBTC-supported snapshot failed: '+JSON.stringify(wbtc));
const wm=metrics(wbtc.body.positions[0]),wr=wbtc.body.positions[0].reserves.find(r=>r.symbol==='WBTC');
if(wm.healthFactorRaw!==wbtc.body.observedHealthFactorRaw||wr?.oracleAdapter!=='WBTC_BTC_USD'||wr?.oracleComponents?.length!==2)throw new Error('WBTC model or composite provenance failed');
results.push({test:'real_wbtc_composite_reference',status:'PASS',latencyMs:wbtc.latencyMs,blockNumber:wbtc.body.blockNumber,blockHash:wbtc.body.blockHash,observedHF:wbtc.body.observedHealthFactorRaw,modeledHF:wm.healthFactorRaw,source:wr.oracleSource,codeHash:wr.oracleCodeHash,priceRaw:wr.priceRaw,components:wr.oracleComponents});
const alternatives=frontier(s,{budget:'3000',gasReserve:'25',target:'1.75',shocks:{[s.positions[0].reserves[0].asset.toLowerCase()]:-2000}});
results.push({test:'real_state_defense_frontier',status:alternatives.alternatives.length?'PASS':'FAIL',examined:alternatives.examined,alternatives:alternatives.alternatives.length,meetsTarget:alternatives.meetsTarget});
const tx=await post('/api/v1/defi/transaction',{wallet,asset:'0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',kind:'withdraw',amount:'0.001'});
if(tx.http!==200||tx.body.simulation!=='SUCCEEDED_AT_BLOCK')throw new Error('Supported live transaction preview failed: '+JSON.stringify(tx));
results.push({test:'real_withdraw_readonly_simulation',status:'PASS',latencyMs:tx.latencyMs,blockNumber:tx.body.blockNumber,gas:tx.body.gasRaw,feeReserveWei:tx.body.feeReserveWei,blockers:tx.body.blockers});
const wtx=await post('/api/v1/defi/transaction',{wallet:'0x1FbcadCc4c250cF1f6da6b360263A6EBC3967aA9',asset:'0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599',kind:'withdraw',amount:'0.00001'});
if(wtx.http!==200||wtx.body.simulation!=='SUCCEEDED_AT_BLOCK')throw new Error('Live WBTC transaction preview failed: '+JSON.stringify(wtx));
results.push({test:'real_wbtc_withdraw_readonly_simulation',status:'PASS',latencyMs:wtx.latencyMs,blockNumber:wtx.body.blockNumber,gas:wtx.body.gasRaw,beforeHF:wtx.body.before.healthFactorRaw,afterHF:wtx.body.after.healthFactorRaw,blockers:wtx.body.blockers});
const invalid=await post('/api/v1/defi/snapshot',{wallet:'bad'});results.push({test:'invalid_wallet_rejected',status:invalid.http===422?'PASS':'FAIL',http:invalid.http});
const protectedReport=await fetch(base+'/api/v1/defi-reports');results.push({test:'unauthenticated_reports_denied',status:protectedReport.status===401?'PASS':'FAIL',http:protectedReport.status});
const page=await fetch(base+'/?verify='+Date.now()),html=await page.text(),build=html.match(/name="rivexis-build" content="([^"]+)"/)?.[1];
results.push({test:'public_build_marker',status:page.ok&&build&&(!expectedBuild||build===expectedBuild)&&html.includes('Understand the risk')?'PASS':'FAIL',buildSha:build,expectedBuild:expectedBuild||null,transformed:html.includes('Understand the risk')});
const report={checkedAt:new Date().toISOString(),base,results};await mkdir('certification-reports',{recursive:true});await writeFile('certification-reports/defi-live-verification.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
if(results.some(r=>r.status==='FAIL'))process.exitCode=1;
