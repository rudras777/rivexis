// Real bounded probes only; no funding overrides, private keys or transactions.
import assert from 'node:assert/strict';
import {writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {parseAbi,encodeFunctionData} from 'viem';
import {snapshot} from '../supabase/functions/rivexis-api/defi-portfolio-rpc.mjs';
import {client} from '../supabase/functions/rivexis-api/defi-rpc.mjs';
import {buildMorphoSequence,decodeMorphoSequence} from '../supabase/functions/rivexis-api/defi-morpho-sequence.mjs';
import {MORPHO_WBTC as config} from '../supabase/functions/rivexis-api/defi-morpho-oracle.mjs';
import {MORPHO} from '../supabase/functions/rivexis-api/defi-morpho-rpc.mjs';
import {format} from '../supabase/functions/rivexis-api/defi-model.mjs';
const tokenAbi=parseAbi(['function approve(address spender,uint256 amount) returns(bool)']);
const wallet='0xbdc3c47122d033ccd1Ad7b986071187Be597fF72';
export async function certifyMorphoSequence(outputPath){
 const startedAt=new Date().toISOString();await writeFile(outputPath,JSON.stringify({status:'RUNNING',startedAt,passed:0}));const cases=[];
 try{
  const rpc=client(),s=await snapshot(wallet,rpc,'morpho-wbtc'),parent=await rpc.getBlock({blockNumber:BigInt(s.blockNumber)});
  const repay=amount=>({kind:'repay',asset:config.loanToken,amount}),supply=amount=>({kind:'supply',asset:config.collateralToken,amount});
  const specs=[['one partial asset repayment',[repay('0.001')]],['one collateral supply',[supply('0.00001')]],['two repayments share allowance and evolving shares',[repay('0.001'),repay('0.002')]],['two supplies share allowance and evolving collateral',[supply('0.00001'),supply('0.00002')]],['repay then supply',[repay('0.001'),supply('0.00001')]],['supply then repay',[supply('0.00001'),repay('0.001')]],['approval failure preserves a blocked result',[repay('0.001')],'BLOCKED'],['repeated simulation starts from unchanged parent',[repay('0.001')]]];
  for(const [name,actions,status='SEQUENCE_PREVIEW_ONLY'] of specs){
   const prepared=buildMorphoSequence({wallet,coverage:'morpho-wbtc',actions},s,parent);
   if(status==='BLOCKED'){assert.equal(prepared.steps[1].label,'Approve exact USDC amount');prepared.calls[prepared.stepStart+1].call.data=encodeFunctionData({abi:tokenAbi,functionName:'approve',args:[MORPHO,0n]})}
   const raw=await rpc.request({method:'eth_simulateV1',params:[{blockStateCalls:[{calls:prepared.calls.map(c=>c.call)}],validation:true,traceTransfers:false,returnFullTransactions:false},'0x'+BigInt(s.blockNumber).toString(16)]});
   const result=decodeMorphoSequence(raw,prepared,parent);assert.equal(result.status,status);cases.push({name,status:'PASSED',result});
   if(name==='one partial asset repayment')cases.at(-1).replay={snapshot:s,parent:{hash:parent.hash,number:parent.number.toString(),timestamp:parent.timestamp.toString(),baseFeePerGas:parent.baseFeePerGas.toString()},input:{wallet,coverage:'morpho-wbtc',actions},raw};
  }
  assert.deepEqual(cases[0].result.walletAssets,cases[7].result.walletAssets);assert.deepEqual(cases[0].result.afterState,cases[7].result.afterState);
  const loan=s.positions[0].reserves.find(r=>r.asset===config.loanToken);
  const rejects=[['aggregate real wallet balance bound',[repay(format((BigInt(loan.walletRaw)+1n).toString(),6,6))],s,Date.now()],['full closure withheld',[repay(format(loan.debtRaw,6,6))],s,Date.now()],['sample withheld',[repay('0.001')],{...s,sample:true},Date.now()],['stale evidence withheld',[repay('0.001')],s,(s.blockTimestamp+181)*1000]];
  for(const [name,actions,state,now] of rejects){assert.throws(()=>buildMorphoSequence({wallet,coverage:'morpho-wbtc',actions},state,parent,now));cases.push({name,status:'PASSED',classification:'LOCAL_VALIDATION_AGAINST_ACTUAL_PARENT_NO_SIMULATION_SUBMITTED'})}
  assert.equal((await rpc.getBlock({blockNumber:BigInt(s.blockNumber)})).hash,s.blockHash);
  const result={status:'PASSED',classification:'ACTUAL_BOUNDED_MORPHO_SEQUENCE_CERTIFICATION_NOT_EXECUTION_OR_OWNERSHIP_PROOF',startedAt,completedAt:new Date().toISOString(),parentBlock:s.blockNumber,parentHash:s.blockHash,passed:cases.length,actualSimulations:8,localGuardsAgainstActualSnapshot:4,stateOverrides:false,blockOverrides:false,signaturesOrSubmissions:false,cases};await writeFile(outputPath,JSON.stringify(result,null,2));return result;
 }catch(error){await writeFile(outputPath,JSON.stringify({status:'FAILED',startedAt,completedAt:new Date().toISOString(),passed:0,completedCases:cases,message:error.message},null,2));throw error}
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){const output=process.argv[2];if(!output)throw Error('Usage: node scripts/certify_morpho_defense_sequence.mjs OUTPUT_JSON');const result=await certifyMorphoSequence(output);console.log(JSON.stringify({status:result.status,passed:result.passed,actualSimulations:result.actualSimulations,parentBlock:result.parentBlock}))}
