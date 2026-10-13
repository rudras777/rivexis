// Certification only. eth_simulateV1 changes ephemeral provider state, never the chain.
// Observer calls are included in validation/fees; this is not a production gas quote.
import assert from 'node:assert/strict';
import {readFile,writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {parseAbi,encodeFunctionData,decodeFunctionResult,isAddress} from 'viem';

export const RPC_URL='https://ethereum.publicnode.com';
const POOL='0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2';
const USDT='0xdAC17F958D2ee523a2206206994597C13D831ec7';
const WETH='0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2';
const poolAbi=parseAbi([
 'function getUserEMode(address user) view returns(uint256)',
 'function getUserAccountData(address user) view returns (uint256,uint256,uint256,uint256,uint256,uint256)',
 'function repay(address asset,uint256 amount,uint256 interestRateMode,address onBehalfOf) returns(uint256)',
 'function withdraw(address asset,uint256 amount,address to) returns(uint256)',
 'function borrow(address asset,uint256 amount,uint256 interestRateMode,uint16 referralCode,address onBehalfOf)',
 'function supply(address asset,uint256 amount,address onBehalfOf,uint16 referralCode)',
]);
const tokenAbi=parseAbi(['function approve(address spender,uint256 amount) returns(bool)','function balanceOf(address user) view returns(uint256)']);
const methods=new Set(['eth_chainId','eth_getBlockByNumber','eth_call','eth_simulateV1']);
const quantity=v=>'0x'+BigInt(v).toString(16);
const hexQuantity=v=>typeof v==='string'&&/^0x(?:0|[1-9a-f][0-9a-f]*)$/i.test(v);
const lower=s=>s.toLowerCase();
export function validateRpcMethod(method){if(!methods.has(method))throw new Error('Only bounded read-only certification RPC methods are allowed')}

export function createRpc(fetcher=fetch){
 let requests=0,nextRequestAt=0;
 return async(method,params)=>{
  validateRpcMethod(method);const id=++requests;if(id>40)throw new Error('Certification RPC request limit exceeded');
  const body=JSON.stringify({jsonrpc:'2.0',id,method,params});if(body.length>100_000)throw new Error('Certification payload too large');
  // Pace real provider probes; fixtures remain deterministic and never make network calls.
  if(fetcher===fetch){const now=Date.now(),wait=Math.max(0,nextRequestAt-now);nextRequestAt=Math.max(now,nextRequestAt)+500;if(wait)await new Promise(done=>setTimeout(done,wait));}
  const response=await fetcher(RPC_URL,{method:'POST',headers:{'content-type':'application/json'},body,redirect:'error',signal:AbortSignal.timeout(25_000)});
  if(!response.ok)throw new Error(`Certification provider HTTP ${response.status}`);
  const json=await response.json();if(json.error)throw Object.assign(new Error(`Certification provider RPC error ${json.error.code}`),{rpcCode:json.error.code,rpcMethod:method,rpcMessage:typeof json.error.message==='string'?json.error.message.replace(/https?:\/\/\S+/g,'[endpoint]').slice(0,200):undefined});
  if(json.id!==id||json.jsonrpc!=='2.0'||!Object.hasOwn(json,'result'))throw new Error('Malformed certification RPC envelope');
  return json.result;
 };
}

export function buildCases(snapshot,maxFee){
 assert.ok(snapshot&&!snapshot.sample&&snapshot.status==='READY','A genuine supported receipt is required');
 assert.ok(isAddress(snapshot.wallet)&&BigInt(maxFee)>0n,'Invalid wallet or fee cap');
 assert.equal(snapshot.positions.length,1,'Certification is restricted to one validated Aave position');
 const position=snapshot.positions[0];assert.equal(position.protocol,'Aave V3');
 const eth=position.reserves.find(r=>lower(r.asset)===lower(WETH));
 const usdt=position.reserves.find(r=>lower(r.asset)===lower(USDT));
 assert.ok(eth?.collateralEnabled&&eth.ltBps==='8300'&&usdt&&usdt.decimals===6,'This drill requires the validated WETH/USDT reference');
 assert.ok(BigInt(usdt.walletRaw)>=3_000_000n&&BigInt(usdt.debtRaw)>3_000_000n&&BigInt(eth.collateralRaw)>1_000_000_000_000_000n,'Real balances must support the bounded cases; balances are never overridden');
 const wallet=snapshot.wallet;
 const call=(to,abi,name,args)=>({from:wallet,to,data:encodeFunctionData({abi,functionName:name,args}),gas:quantity(1_000_000),maxFeePerGas:quantity(maxFee),maxPriorityFeePerGas:'0x0'});
 const account=()=>call(POOL,poolAbi,'getUserAccountData',[wallet]);
 const balance=asset=>call(asset,tokenAbi,'balanceOf',[wallet]);
 const approve=(asset,amount)=>call(asset,tokenAbi,'approve',[POOL,amount]);
 const repay=amount=>call(POOL,poolAbi,'repay',[USDT,amount,2n,wallet]);
 const withdraw=amount=>call(POOL,poolAbi,'withdraw',[WETH,amount,wallet]);
 const borrow=amount=>call(POOL,poolAbi,'borrow',[USDT,amount,2n,0,wallet]);
 const supply=amount=>call(POOL,poolAbi,'supply',[WETH,amount,wallet,0]);
 const spec=(name,asset,actions,actionStatuses,check)=>({name,asset,calls:[account(),balance(asset),...actions,account(),balance(asset)],statuses:['0x1','0x1',...actionStatuses,'0x1','0x1'],check});
 const noChange=({before,after,tokenBefore,tokenAfter})=>{assert.deepEqual(after,before);assert.equal(tokenAfter,tokenBefore)};
 const repayment=amount=>({before,after,tokenBefore,tokenAfter})=>{assert.equal(tokenBefore-tokenAfter,amount);assert.ok(after[1]<before[1]);assert.ok(after[5]>before[5])};
 const withdrawal=({before,after,tokenBefore,tokenAfter})=>{assert.equal(tokenAfter-tokenBefore,1_000_000_000_000_000n);assert.ok(after[0]<before[0]);assert.ok(after[5]<before[5])};
 return [
  spec('baseline reads do not change token or lending state',USDT,[],[],noChange),
  spec('repayment without allowance reverts',USDT,[approve(USDT,0n),repay(1_000_000n)],['0x1','0x0'],noChange),
  spec('exact approval then one USDT repayment',USDT,[approve(USDT,0n),approve(USDT,1_000_000n),repay(1_000_000n)],['0x1','0x1','0x1'],repayment(1_000_000n)),
  spec('two repayments share approval and changing debt state',USDT,[approve(USDT,0n),approve(USDT,3_000_000n),repay(1_000_000n),repay(2_000_000n)],['0x1','0x1','0x1','0x1'],repayment(3_000_000n)),
  spec('repayment exceeding exact allowance reverts',USDT,[approve(USDT,0n),approve(USDT,1_000_000n),repay(2_000_000n)],['0x1','0x1','0x0'],noChange),
  spec('zero repayment reverts without changing exposure',USDT,[repay(0n)],['0x0'],noChange),
  spec('supported WETH withdrawal updates wallet and health',WETH,[withdraw(1_000_000_000_000_000n)],['0x1'],withdrawal),
  spec('withdrawal exceeding supplied balance reverts',WETH,[withdraw(BigInt(eth.collateralRaw)+10n**18n)],['0x0'],noChange),
  spec('one USDT borrow increases debt and wallet assets',USDT,[borrow(1_000_000n)],['0x1'],({before,after,tokenBefore,tokenAfter})=>{assert.equal(tokenAfter-tokenBefore,1_000_000n);assert.ok(after[1]>before[1]);assert.ok(after[5]<before[5])}),
  spec('borrowing beyond collateral capacity reverts',USDT,[borrow(1_000_000n*10n**6n)],['0x0'],noChange),
  spec('withdraw approval and resupply use evolving real token balances',WETH,[withdraw(1_000_000_000_000_000n),approve(WETH,0n),approve(WETH,1_000_000_000_000_000n),supply(1_000_000_000_000_000n)],['0x1','0x1','0x1','0x1'],({before,after,tokenBefore,tokenAfter})=>{assert.equal(tokenAfter,tokenBefore);assert.equal(after[1],before[1]);assert.ok(after[0]>=before[0]-1n&&after[0]<=before[0]+1n)}),
  spec('repeated explicit simulation starts from the unchanged parent state',USDT,[approve(USDT,0n),approve(USDT,1_000_000n),repay(1_000_000n)],['0x1','0x1','0x1'],repayment(1_000_000n)),
 ];
}

export function validateSimulation(result,spec,parent){
 assert.ok(Array.isArray(result)&&result.length===1,'Exactly one simulated block is required');
 const block=result[0];assert.equal(lower(block.parentHash),lower(parent.hash),'Simulation parent identity mismatch');
 assert.equal(BigInt(block.number),BigInt(parent.number)+1n,'Unexpected simulated block number');
 assert.equal(BigInt(block.timestamp),BigInt(parent.timestamp)+12n,'Unexpected simulation time progression');
 assert.ok(hexQuantity(block.baseFeePerGas)&&BigInt(block.baseFeePerGas)>0n,'Validation must retain a genuine nonzero derived base fee');
 assert.ok(Array.isArray(block.calls)&&block.calls.length===spec.calls.length,'Provider omitted a simulation call');
 for(let i=0;i<block.calls.length;i++){assert.equal(block.calls[i].status,spec.statuses[i],`Unexpected result for call ${i}`);assert.ok(hexQuantity(block.calls[i].gasUsed)&&BigInt(block.calls[i].gasUsed)>0n,'Missing gas evidence');}
 const last=block.calls.length-1;
 const before=decodeFunctionResult({abi:poolAbi,functionName:'getUserAccountData',data:block.calls[0].returnData});
 const after=decodeFunctionResult({abi:poolAbi,functionName:'getUserAccountData',data:block.calls[last-1].returnData});
 const tokenBefore=decodeFunctionResult({abi:tokenAbi,functionName:'balanceOf',data:block.calls[1].returnData});
 const tokenAfter=decodeFunctionResult({abi:tokenAbi,functionName:'balanceOf',data:block.calls[last].returnData});
 spec.check({before,after,tokenBefore,tokenAfter});
 return {name:spec.name,passed:true,simulatedBlockNumber:block.number,simulatedTimestamp:block.timestamp,baseFeePerGas:block.baseFeePerGas,statuses:block.calls.map(c=>c.status),gasUsedIncludingObservers:block.calls.reduce((sum,c)=>sum+BigInt(c.gasUsed),0n).toString(),before:before.map(String),after:after.map(String),tokenBefore:String(tokenBefore),tokenAfter:String(tokenAfter),rawCalls:block.calls,reverts:block.calls.flatMap((c,i)=>c.status==='0x0'?[{index:i,code:c.error?.code,revertData:c.error?.data??c.returnData}]:[])};
}

export async function certify(receipt,rpc=createRpc()){
 const snapshot=receipt.snapshot;assert.ok(/^\d+$/.test(snapshot?.blockNumber??'')&&/^0x[\da-f]{64}$/i.test(snapshot.blockHash),'Invalid parent identity');
 assert.equal(await rpc('eth_chainId',[]),'0x1','Ethereum mainnet parent state is required');
 const tag=quantity(snapshot.blockNumber),parent=await rpc('eth_getBlockByNumber',[tag,false]);assert.equal(lower(parent.hash),lower(snapshot.blockHash),'Captured parent no longer canonical');
 const modeData=await rpc('eth_call',[{to:POOL,data:encodeFunctionData({abi:poolAbi,functionName:'getUserEMode',args:[snapshot.wallet]})},tag]);
 assert.equal(decodeFunctionResult({abi:poolAbi,functionName:'getUserEMode',data:modeData}),0n,'Only Aave normal mode is certified');
 const fee=BigInt(parent.baseFeePerGas)*2n+1n,specs=buildCases(snapshot,fee),cases=[];
 for(const spec of specs){try{const payload={blockStateCalls:[{calls:spec.calls}],validation:true,traceTransfers:false,returnFullTransactions:false};assert.ok(!payload.blockStateCalls[0].stateOverrides&&!payload.blockStateCalls[0].blockOverrides);const result=await rpc('eth_simulateV1',[payload,tag]);cases.push(validateSimulation(result,spec,parent));}catch(error){error.certificationCase=spec.name;error.completedCases=cases;throw error;}}
 assert.equal(lower((await rpc('eth_getBlockByNumber',[tag,false])).hash),lower(parent.hash),'Parent identity changed during certification');
 assert.deepEqual(cases[2].before,cases[11].before);assert.deepEqual(cases[2].after,cases[11].after);assert.equal(cases[2].tokenBefore,cases[11].tokenBefore);
 return {classification:'HISTORICAL_PINNED_SEQUENTIAL_RPC_CERTIFICATION_NOT_EXECUTION',providerHost:new URL(RPC_URL).host,parentBlockNumber:snapshot.blockNumber,parentBlockHash:parent.hash,parentTimestamp:parent.timestamp,wallet:snapshot.wallet,validation:true,stateOverrides:false,blockOverrides:false,signaturesOrSubmissions:false,ownershipOrSignatureProof:false,passed:cases.length,cases,limitations:['Historical captured parent, not a current wallet risk report.','Provider validation skips signature checks and does not establish wallet ownership.','Simulated blocks and transaction hashes are ephemeral; they are not canonical chain artifacts.','Observer calls also consume simulation gas and nonces: totals are not production transaction fee quotes.','Only the WETH/USDT Aave normal-mode cases listed are certified; Morpho, arbitrary sequences, future inclusion and market shocks are not certified.','Production GasGuard continues to perform independent call previews, not this certification instrument.']};
}

export async function runCertification(receipt,outputPath,rpc){
 const startedAt=new Date().toISOString();
 // Invalidate a prior success artifact before any probe. A failed rerun must never look green.
 await writeFile(outputPath,JSON.stringify({status:'RUNNING',startedAt,passed:0},null,2));
 try{const input=typeof receipt==='function'?await receipt():receipt;const result={status:'PASSED',startedAt,...await certify(input,rpc),completedAt:new Date().toISOString()};await writeFile(outputPath,JSON.stringify(result,null,2));return result;}
 catch(error){await writeFile(outputPath,JSON.stringify({status:'FAILED',startedAt,completedAt:new Date().toISOString(),passed:0,failedCase:error.certificationCase??'parent/input validation',completedCases:error.completedCases??[],diagnostic:{message:error.message,rpcCode:error.rpcCode,rpcMethod:error.rpcMethod,rpcMessage:error.rpcMessage},signaturesOrSubmissions:false},null,2));throw error;}
}

if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const [receiptPath,outputPath]=process.argv.slice(2);if(!receiptPath||!outputPath)throw new Error('Usage: node scripts/certify_aave_sequence_rpc.mjs RECEIPT_JSON OUTPUT_JSON');
 assert.notEqual(resolve(receiptPath).toLowerCase(),resolve(outputPath).toLowerCase(),'Receipt and evidence output paths must differ');
 try{const result=await runCertification(async()=>{const text=await readFile(receiptPath,'utf8');try{return JSON.parse(text.replace(/^\uFEFF/,''))}catch{throw new Error('Receipt is not valid JSON')}},outputPath);console.log(JSON.stringify({status:result.status,passed:result.passed,parent:result.parentBlockNumber,classification:result.classification}));}catch(error){console.error(JSON.stringify({status:'FAILED',message:error.message,case:error.certificationCase,rpcCode:error.rpcCode,rpcMessage:error.rpcMessage}));process.exitCode=1;}
}
