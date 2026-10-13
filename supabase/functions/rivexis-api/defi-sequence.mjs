// Bounded Aave defense preview. No raw client calldata, signing or chain writes.
import {parseAbi,encodeFunctionData,decodeFunctionResult,isAddress} from 'viem';
import {snapshot,client,POOL,poolAbi} from './defi-rpc.mjs';
import {validateSnapshot,decimal,integer} from './defi-model.mjs';
const tokenAbi=parseAbi(['function approve(address spender,uint256 amount) returns(bool)','function balanceOf(address user) view returns(uint256)']);
const quantity=v=>'0x'+BigInt(v).toString(16);
const validQuantity=v=>typeof v==='string'&&/^0x(?:0|[1-9a-f][0-9a-f]*)$/i.test(v);
const hash=v=>typeof v==='string'&&/^0x[0-9a-f]{64}$/i.test(v);
export function sequenceInputError(input){
 if(input.coverage!==undefined&&input.coverage!=='aave')return 'Sequence previews support Aave normal mode only';
 if(!Array.isArray(input.actions)||input.actions.length<1||input.actions.length>2)return 'Select one or two supported defense actions';
 for(const action of input.actions){
  if(!action||typeof action!=='object'||Array.isArray(action)||Object.keys(action).some(k=>!['kind','asset','amount','positionId'].includes(k)))return 'Invalid defense action';
  if(!['repay','supply'].includes(action.kind)||typeof action.asset!=='string'||!isAddress(action.asset,{strict:true})||/^0x0{40}$/i.test(action.asset))return 'Only supported repayment and supply actions can be sequenced';
  if(action.positionId!==undefined&&(typeof action.positionId!=='string'||action.positionId.toLowerCase()!==`aave-v3:1:${String(input.wallet).toLowerCase()}`))return 'Sequence actions must belong to this Aave account';
  try{if(decimal(action.amount,18)===0n)return 'Amount must be greater than zero'}catch{return 'Enter a positive decimal token amount with at most 18 decimal places'}
 }
 return null;
}
export function buildDefenseSequence(input,s,parent,now=Date.now()){
 const error=sequenceInputError(input);if(error)throw new Error(error);
 validateSnapshot(s,now);
 if(s.sample||s.restoredReport||s.wallet.toLowerCase()!==String(input.wallet).toLowerCase()||s.chainId!==1||s.positions.length!==1||s.positions[0].protocol!=='Aave V3'||s.positions[0].eMode!==0)throw new Error('A fresh supported Aave account is required');
 if(!hash(parent.hash)||parent.hash.toLowerCase()!==s.blockHash.toLowerCase()||BigInt(parent.number)!==BigInt(s.blockNumber)||Number(parent.timestamp)!==s.blockTimestamp||typeof parent.baseFeePerGas!=='bigint'||parent.baseFeePerGas<=0n)throw new Error('Sequence parent evidence mismatch');
 const p=s.positions[0],maxFee=parent.baseFeePerGas*2n+1n,actions=[],totals=new Map(),repayments=new Map();
 for(const x of input.actions){const r=p.reserves.find(r=>r.asset.toLowerCase()===x.asset.toLowerCase());if(!r)throw new Error('Unsupported sequence asset');const amount=decimal(x.amount,r.decimals);if(!amount)throw new Error('Amount must be greater than zero');
  if(x.kind==='supply'&&(!r.supplyAllowed||!r.collateralEnabled))throw new Error('Sequence supply requires existing eligible collateral');
  const key=r.asset.toLowerCase();totals.set(key,(totals.get(key)??0n)+amount);
  if(x.kind==='repay'){repayments.set(key,(repayments.get(key)??0n)+amount);if(repayments.get(key)>integer(r.debtRaw))throw new Error('Sequence repayment exceeds observed debt')}
  if(totals.get(key)>integer(r.walletRaw))throw new Error('Sequence exceeds observed wallet token balance');
  actions.push({kind:x.kind,asset:r.asset,amountRaw:amount.toString(),positionId:p.id,symbol:r.symbol});
 }
 const call=(to,abi,name,args,label)=>({label,call:{from:s.wallet,to,data:encodeFunctionData({abi,functionName:name,args}),gas:quantity(1_000_000n),maxFeePerGas:quantity(maxFee),maxPriorityFeePerGas:'0x0'}});
 const steps=[];
 // Zero then exact aggregate approval supports USDT; never unlimited approvals.
 for(const [asset,total] of totals){const r=p.reserves.find(r=>r.asset.toLowerCase()===asset);if(integer(r.allowanceRaw)<total){steps.push(call(r.asset,tokenAbi,'approve',[POOL,0n],`Reset ${r.symbol} allowance`));steps.push(call(r.asset,tokenAbi,'approve',[POOL,total],`Approve exact ${r.symbol} amount`))}}
 for(const x of actions)steps.push(call(POOL,poolAbi,x.kind,x.kind==='repay'?[x.asset,BigInt(x.amountRaw),2n,s.wallet]:[x.asset,BigInt(x.amountRaw),s.wallet,0],`${x.kind==='repay'?'Repay':'Supply'} ${x.symbol}`));
 const observer=()=>call(POOL,poolAbi,'getUserAccountData',[s.wallet],'Observe lending account');
 const assets=[...totals.keys()].map(asset=>p.reserves.find(r=>r.asset.toLowerCase()===asset));
 const balances=()=>assets.map(r=>call(r.asset,tokenAbi,'balanceOf',[s.wallet],`Observe ${r.symbol} balance`));
 const observerCount=1+assets.length,calls=[observer(),...balances(),...steps,observer(),...balances()];
 const gasLimitReserve=BigInt(calls.length)*1_000_000n*maxFee;
 if(gasLimitReserve>integer(s.nativeBalanceRaw))throw new Error('Insufficient native ETH for the bounded simulation gas reserve');
 return {snapshot:s,actions,steps,calls,maxFee,gasLimitReserve,observerCount,assets};
}
export function decodeDefenseSequence(result,prepared,parent){
 if(!Array.isArray(result)||result.length!==1)throw new Error('Incomplete sequence block');const b=result[0];
 if(!hash(b.parentHash)||b.parentHash.toLowerCase()!==parent.hash.toLowerCase()||!validQuantity(b.number)||BigInt(b.number)!==BigInt(parent.number)+1n||!validQuantity(b.timestamp)||BigInt(b.timestamp)!==BigInt(parent.timestamp)+12n||!validQuantity(b.baseFeePerGas)||BigInt(b.baseFeePerGas)<=0n||!Array.isArray(b.calls)||b.calls.length!==prepared.calls.length)throw new Error('Invalid sequence parent or call evidence');
 for(const c of b.calls)if(!['0x0','0x1'].includes(c.status)||!validQuantity(c.gasUsed)||BigInt(c.gasUsed)<=0n||BigInt(c.gasUsed)>1_000_000n||typeof c.returnData!=='string'||!/^0x(?:[0-9a-f]{2})*$/i.test(c.returnData))throw new Error('Invalid sequence result evidence');
 const afterIndex=prepared.observerCount+prepared.steps.length;
 if([...b.calls.slice(0,prepared.observerCount),...b.calls.slice(afterIndex)].some(c=>c.status!=='0x1'))throw new Error('Sequence account observation failed');
 const account=c=>{const v=decodeFunctionResult({abi:poolAbi,functionName:'getUserAccountData',data:c.returnData});return {collateralRaw:v[0].toString(),debtRaw:v[1].toString(),healthFactorRaw:v[1]===0n?null:v[5].toString(),liquidationThresholdBps:v[3].toString()}};
 const failed=b.calls.slice(prepared.observerCount,afterIndex).some(c=>c.status==='0x0');
 const steps=prepared.steps.map((s,i)=>({label:s.label,to:s.call.to,data:s.call.data,status:b.calls[i+prepared.observerCount].status==='0x1'?'SUCCEEDED':'REVERTED',gasRaw:BigInt(b.calls[i+prepared.observerCount].gasUsed).toString(),revertData:b.calls[i+prepared.observerCount].status==='0x0'?b.calls[i+prepared.observerCount].returnData:null}));
 const walletAssets=prepared.assets.map((r,i)=>({asset:r.asset,symbol:r.symbol,decimals:r.decimals,beforeRaw:decodeFunctionResult({abi:tokenAbi,functionName:'balanceOf',data:b.calls[i+1].returnData}).toString(),afterRaw:decodeFunctionResult({abi:tokenAbi,functionName:'balanceOf',data:b.calls[afterIndex+i+1].returnData}).toString()}));
 for(const asset of walletAssets){const reserve=prepared.assets.find(r=>r.asset===asset.asset);if(BigInt(asset.beforeRaw)!==integer(reserve.walletRaw))throw new Error('Sequence baseline token balance does not reconcile');if(!failed){const spent=prepared.actions.filter(a=>a.asset===asset.asset).reduce((n,a)=>n+BigInt(a.amountRaw),0n);if(BigInt(asset.beforeRaw)-BigInt(asset.afterRaw)!==spent)throw new Error('Sequence token effects do not reconcile')}}
 return {classification:'EPHEMERAL_AAVE_NORMAL_MODE_DEFENSE_SEQUENCE',model:prepared.snapshot.model,chainId:1,coverage:'aave',rpcHost:prepared.snapshot.rpcHost,fetchedAt:new Date().toISOString(),oracleInputs:prepared.assets.map(r=>({asset:r.asset,decimals:r.decimals,priceRaw:r.priceRaw,ltBps:r.ltBps,oracleSource:r.oracleSource,oracleUpdatedAt:r.oracleUpdatedAt})),status:failed?'BLOCKED':'SEQUENCE_PREVIEW_ONLY',simulation:failed?'SEQUENCE_CONTAINS_REVERT':'SEQUENTIAL_CALLS_SUCCEEDED',wallet:prepared.snapshot.wallet,blockNumber:prepared.snapshot.blockNumber,blockHash:parent.hash,simulatedBlockNumber:BigInt(b.number).toString(),simulatedTimestamp:Number(BigInt(b.timestamp)),actions:prepared.actions,steps,before:account(b.calls[0]),observedAfter:account(b.calls[afterIndex]),walletAssets,gasRaw:steps.reduce((n,s)=>n+BigInt(s.gasRaw),0n).toString(),gasIncludingObserversRaw:b.calls.reduce((n,c)=>n+BigInt(c.gasUsed),0n).toString(),maxFeePerGasRaw:prepared.maxFee.toString(),simulationGasLimitReserveWei:prepared.gasLimitReserve.toString(),validation:true,stateOverrides:false,blockOverrides:false,blockers:failed?['At least one sequence step reverted; successful later calls do not establish the intended plan.']:[],warnings:['Ephemeral next-block simulation at current oracle prices; it does not execute your market stress scenario.','No signature, wallet ownership proof, submission or inclusion guarantee.','Account-observation calls consume simulation gas and nonces; the simulation reserve includes their full gas limits and is not an execution fee quote.','Approvals use exact aggregate amounts. Review every step; no approval is signed or submitted.','State changes accrue protocol interest at the simulated timestamp. Pending transactions, MEV and future prices are excluded.','Observed final state may include partial effects when a step reverts; it is not a successful defense plan.']};
}
export async function defenseSequence(input,rpc=client()){
 const error=sequenceInputError(input);if(error)throw new Error(error);
 const s=await snapshot(input.wallet,rpc),parent=await rpc.getBlock({blockNumber:BigInt(s.blockNumber)}),prepared=buildDefenseSequence(input,s,parent);
 const result=await rpc.request({method:'eth_simulateV1',params:[{blockStateCalls:[{calls:prepared.calls.map(c=>c.call)}],validation:true,traceTransfers:false,returnFullTransactions:false},quantity(s.blockNumber)]});
 const decoded=decodeDefenseSequence(result,prepared,parent);
 if((await rpc.getBlock({blockNumber:BigInt(s.blockNumber)})).hash!==s.blockHash)throw new Error('Block changed during sequence preview');
 return decoded;
}
