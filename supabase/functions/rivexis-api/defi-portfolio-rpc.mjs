// Bounded coverage is explicit; other Morpho markets are never implied discovered.
import {getAddress,isAddress,encodeFunctionData} from 'viem';
import {snapshot as aaveSnapshot,client,POOL,poolAbi} from './defi-rpc.mjs';
import {MODEL,validateSnapshot,metrics,scenario} from './defi-unified-model.mjs';
import {decimal,integer} from './defi-model.mjs';
import {readMorphoPosition,MORPHO,morphoAbi} from './defi-morpho-rpc.mjs';
import {morphoRepaymentForBudget,morphoRepayShares} from './defi-morpho-model.mjs';
export const COVERAGE=['aave','morpho-wbtc','combined'];
export async function snapshot(wallet,rpc=client(),coverage='aave'){
  if(!COVERAGE.includes(coverage))throw new Error('Unsupported coverage');
  if(coverage==='aave')return {...await aaveSnapshot(wallet,rpc),coverage};
  if(!isAddress(wallet,{strict:true})||/^0x0{40}$/i.test(wallet))throw new Error('Enter a valid Ethereum address');wallet=getAddress(wallet);
  if(await rpc.getChainId()!==1)throw new Error('RPC is not Ethereum');
  const block=await rpc.getBlock({blockTag:'latest'});
  if(!block.number||!block.hash||Date.now()/1000-Number(block.timestamp)>180||Number(block.timestamp)>Date.now()/1000+30)throw new Error('Latest Ethereum block is stale');
  const aave=coverage==='combined'?await aaveSnapshot(wallet,rpc,block):null;
  const morpho=await readMorphoPosition(rpc,block,wallet,aave?.positions.flatMap(p=>p.reserves)??[]);
  const positions=[...(aave?.positions??[]),...(morpho?[morpho]:[])];
  const summaries=positions.map(p=>metrics(p));
  const minimum=summaries.reduce((m,o)=>o.healthFactorRaw===null?m:m===null||BigInt(o.healthFactorRaw)<m?BigInt(o.healthFactorRaw):m,null);
  if((await rpc.getBlock({blockNumber:block.number})).hash!==block.hash)throw new Error('Block changed during portfolio read');
  return {model:MODEL,status:aave?.status==='UNSUPPORTED'?'UNSUPPORTED':'READY',coverage,wallet,chainId:1,blockNumber:block.number.toString(),blockHash:block.hash,blockTimestamp:Number(block.timestamp),nativeBalanceRaw:aave?.nativeBalanceRaw??(await rpc.getBalance({address:wallet,blockNumber:block.number})).toString(),positions,
    observedCollateralRaw:summaries.reduce((n,o)=>n+BigInt(o.collateralRaw),0n).toString(),observedDebtRaw:summaries.reduce((n,o)=>n+BigInt(o.debtRaw),0n).toString(),observedHealthFactorRaw:minimum?.toString()??null,
    source:'Ethereum / protocol contracts',rpcHost:new URL(rpc.transport.url||'https://ethereum.publicnode.com').host,fetchedAt:new Date().toISOString(),warnings:aave?.warnings??[],limitations:[
      coverage==='combined'?'Ethereum Aave V3 normal mode plus one Morpho WBTC/USDC 86% LLTV market.':'One Ethereum Morpho WBTC/USDC 86% LLTV market only.',
      'Other Morpho markets and chains are not discovered. Loan supply shares are observable but excluded from collateral/borrow risk.',
      'Minimum health is across independent positions, not a netted protocol health factor. Morpho health is computed in native loan units.',
      'Capital prices share one per-token reference across positions; liquidation health uses each protocol oracle.',
      ...(aave?.limitations??[]).filter(x=>!x.startsWith('Single Ethereum Aave')),
    ]};
}
export async function gasguard(input,rpc=client()){
  const s=await snapshot(input.wallet,rpc,input.coverage??'aave');validateSnapshot(s);
  const eligible=s.positions.filter(p=>p.reserves.some(r=>r.asset.toLowerCase()===String(input.asset).toLowerCase()));
  const p=input.positionId?s.positions.find(p=>p.id===input.positionId):eligible.length===1?eligible[0]:null;
  if(!p)throw new Error('Select a supported transaction position');
  const r=p.reserves.find(r=>r.asset.toLowerCase()===String(input.asset).toLowerCase());
  if(!r||!['repay','supply','withdraw','borrow'].includes(input.kind))throw new Error('Unsupported transaction');
  let amount=decimal(input.amount,r.decimals);if(!amount)throw new Error('Amount must be greater than zero');
  const blockers=[],action={positionId:p.id,asset:r.asset,kind:input.kind,amountRaw:amount.toString()};let data,to;
  if(p.protocol==='Morpho Blue'){
    const params=[...p.marketParams.slice(0,4),BigInt(p.marketParams[4])];
    if(input.kind==='repay'){
      if(r.asset!==p.loanToken)throw new Error('Repayment requires the Morpho loan token');
      const prepared=input.sharesRaw?morphoRepayShares(p.market,p.morphoPosition,input.sharesRaw):morphoRepaymentForBudget(p.market,p.morphoPosition,amount.toString());
      if(!prepared)throw new Error('Amount cannot repay a Morpho share');
      if(!input.sharesRaw&&integer(prepared.assetsRaw)>amount)throw new Error('Repayment exceeds selected amount');
      if(input.sharesRaw&&integer(prepared.assetsRaw)>amount)blockers.push('Current share repayment cost exceeds the entered token amount; review the updated cost');
      amount=integer(prepared.assetsRaw);action.amountRaw=amount.toString();action.sharesRaw=prepared.sharesRaw;
      data=encodeFunctionData({abi:morphoAbi,functionName:'repay',args:[params,0n,BigInt(prepared.sharesRaw),s.wallet,'0x']});
    }else{
      if((input.kind==='borrow'&&r.asset!==p.loanToken)||(input.kind!=='borrow'&&r.asset!==p.collateralToken))throw new Error('Unsupported Morpho action asset');
      const fn=input.kind==='supply'?'supplyCollateral':input.kind==='withdraw'?'withdrawCollateral':'borrow';
      const args=input.kind==='supply'?[params,amount,s.wallet,'0x']:input.kind==='withdraw'?[params,amount,s.wallet,s.wallet]:[params,amount,0n,s.wallet,s.wallet];
      data=encodeFunctionData({abi:morphoAbi,functionName:fn,args});
    }
    to=MORPHO;
  }else{
    if(input.kind==='supply'&&!r.supplyAllowed)throw new Error('Reserve cannot accept supply');if(input.kind==='borrow'&&!r.borrowAllowed)throw new Error('Reserve borrowing disabled');
    const args=input.kind==='repay'?[r.asset,amount,2n,s.wallet]:input.kind==='supply'?[r.asset,amount,s.wallet,0]:input.kind==='withdraw'?[r.asset,amount,s.wallet]:[r.asset,amount,2n,0,s.wallet];
    data=encodeFunctionData({abi:poolAbi,functionName:input.kind,args});to=POOL;
  }
  if(['repay','supply'].includes(input.kind)){if(amount>integer(r.walletRaw))blockers.push('Insufficient wallet token balance');if(amount>integer(r.allowanceRaw))blockers.push('Protocol allowance is insufficient; a separate approval is required');}
  const before=metrics(p),after=metrics(p,{},[action]),effects=scenario(s,{},[action]);
  if(after.liquidatable)blockers.push('Modeled position is below its liquidation threshold');
  const blockNumber=BigInt(s.blockNumber),call={account:s.wallet,to,data,blockNumber};let gas=null,fees=null,simulation='NOT_RUN';
  try{await rpc.call(call);gas=await rpc.estimateGas(call);fees=await rpc.estimateFeesPerGas();simulation='SUCCEEDED_AT_BLOCK';}catch{simulation='REVERTED_OR_RPC_UNAVAILABLE';blockers.push('RPC call or gas estimate failed; execution remains unverified');}
  const maxFee=fees?.maxFeePerGas??fees?.gasPrice??null,cost=gas!==null&&maxFee!==null?gas*maxFee*120n/100n:null;
  if(cost!==null&&cost>integer(s.nativeBalanceRaw))blockers.push('Insufficient native ETH for gas reserve');
  if((await rpc.getBlock({blockNumber})).hash!==s.blockHash)throw new Error('Block changed during preview');
  return {model:s.model,coverage:s.coverage,blockNumber:s.blockNumber,blockHash:s.blockHash,wallet:s.wallet,to,data,nonceAtBlock:await rpc.getTransactionCount({address:s.wallet,blockNumber}),action,before,after,positionEffects:effects,simulation,gasRaw:gas?.toString()??null,maxFeePerGasRaw:maxFee?.toString()??null,feeReserveWei:cost?.toString()??null,nativeBalanceRaw:s.nativeBalanceRaw,allowanceRaw:r.allowanceRaw,tokenBalanceRaw:r.walletRaw,blockers,status:blockers.length?'BLOCKED':'PREVIEW_ONLY',warnings:[
    'Read-only eth_call and eth_estimateGas; no signing or submission. Multi-action sequences are not simulated as a state fork.',
    'Morpho repayment is specified in shares; displayed token cost is recomputed from current accrued state. Future interest can change the cost.',
    'Network fee estimate includes a 20% gas reserve; future inclusion cost and approvals can differ.',
    'Pending transactions, swaps, MEV and other markets are not simulated. Every other modeled position remains independent.',
  ]};
}
