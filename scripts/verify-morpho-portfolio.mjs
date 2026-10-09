// Actual public reference wallet, not user-owned. Direct staging RPC only.
import {writeFile} from 'node:fs/promises';
import {snapshot,gasguard} from '../supabase/functions/rivexis-api/defi-portfolio-rpc.mjs';
import {validateSnapshot,frontier,scenario} from '../supabase/functions/rivexis-api/defi-unified-model.mjs';
const wallet='0x4D9bf9F734B817298A4c0bC250c30527379cbE34';
const state=await snapshot(wallet,undefined,'combined');validateSnapshot(state);
if(state.positions.length!==2||!state.positions.some(p=>p.protocol==='Aave V3')||!state.positions.some(p=>p.protocol==='Morpho Blue'))throw new Error('Dual-protocol reference positions missing');
const constraints={budget:'25000',gasReserve:'2',target:'1.50',shocks:{'0x2260fac5e5542a773aa44fbcfedf7c193bc2c599':-1000}};
const result=frontier(state,constraints),outcomes=scenario(state,constraints.shocks);
const transaction=await gasguard({wallet,coverage:'combined',positionId:state.positions.find(p=>p.protocol==='Morpho Blue').id,asset:'0x2260fac5e5542a773aa44fbcfedf7c193bc2c599',kind:'withdraw',amount:'0.00001'});
if(transaction.simulation!=='SUCCEEDED_AT_BLOCK'||transaction.positionEffects.length!==2)throw new Error('Actual Morpho transaction reference failed');
const report={classification:'STAGING_MULTIPROTOCOL_VALIDATION_NOT_PRODUCTION_SUPPORT',checkedAt:new Date().toISOString(),walletOwnership:'PUBLIC_REFERENCE_NOT_USER_OWNED',snapshot:state,constraints,result,outcomes,transaction};
await writeFile('certification-reports/morpho-portfolio-reference.json',JSON.stringify(report,null,2));
console.log(JSON.stringify({status:'STAGING_MULTIPROTOCOL_REFERENCE_PASS',positions:state.positions.map(p=>p.protocol),block:state.blockNumber,alternatives:result.alternatives.length,simulation:transaction.simulation,gasRaw:transaction.gasRaw,productionSupport:false},null,2));
