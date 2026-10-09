// Staging validation only. Calls accrueInterest inside eth_call/Multicall3;
// no state persists, no account signs, no token transfer or paid API is used.
import {writeFile,mkdir} from 'node:fs/promises';
import {parseAbi,parseAbiItem,encodeAbiParameters,encodeFunctionData,decodeErrorResult,toHex,keccak256} from 'viem';
import {client} from '../supabase/functions/rivexis-api/defi-rpc.mjs';
import {accrueMorphoMarket,morphoRisk,morphoWithdrawalLimit} from '../supabase/functions/rivexis-api/defi-morpho-model.mjs';
const core='0xbbbbbbbbbb9cc5e90e3b3af64bdaf62c37eeffcb',irm='0x870ac11d48b15db9a138cf899d20f13f79ba00bc';
const expectedCoreHash='0xfa259fa317198f88f5fa3c119f06c066295dbcd47d715e0a30e1bcf94c02ef8c';
const fields=['totalSupplyAssetsRaw','totalSupplySharesRaw','totalBorrowAssetsRaw','totalBorrowSharesRaw','lastUpdateRaw','feeRaw'];
const paramsType='(address loanToken,address collateralToken,address oracle,address irm,uint256 lltv)',marketType='(uint128 totalSupplyAssets,uint128 totalSupplyShares,uint128 totalBorrowAssets,uint128 totalBorrowShares,uint128 lastUpdate,uint128 fee)';
const abi=parseAbi(['function idToMarketParams(bytes32) view returns(address,address,address,address,uint256)','function market(bytes32) view returns(uint128,uint128,uint128,uint128,uint128,uint128)','function position(bytes32,address) view returns(uint256,uint128,uint128)','function isIrmEnabled(address) view returns(bool)','function isLltvEnabled(uint256) view returns(bool)',`function accrueInterest(${paramsType} marketParams)`,`function withdrawCollateral(${paramsType} marketParams,uint256 assets,address onBehalf,address receiver)`,`function borrowRateView(${paramsType} marketParams,${marketType} market) view returns(uint256)`,'function MORPHO() view returns(address)','function price() view returns(uint256)']);
const rpc=client(),block=await rpc.getBlock({blockTag:'latest'}),blockNumber=block.number;
if(await rpc.getChainId()!==1)throw new Error('Not Ethereum');
const coreHash=keccak256(await rpc.getCode({address:core,blockNumber}));if(coreHash!==expectedCoreHash)throw new Error('Morpho core bytecode changed');
const event=parseAbiItem('event Borrow(bytes32 indexed id,address caller,address indexed onBehalf,address indexed receiver,uint256 assets,uint256 shares)');
const logs=await rpc.getLogs({address:core,event,fromBlock:blockNumber-250n,toBlock:blockNumber});
const pinned={id:'0x3a85e619751152991742810df6ec69ce473daef99e28a64ab2340d7b7ccfee49',user:'0x4D9bf9F734B817298A4c0bC250c30527379cbE34'};
const candidates=[pinned,...[...new Map(logs.reverse().map(l=>[l.args.id,{id:l.args.id,user:l.args.onBehalf}])).values()].filter(c=>c.id!==pinned.id).slice(0,5)];
const results=[];
for(const c of candidates){
  const read=(address,functionName,args=[])=>({address,abi,functionName,args});
  const [params,state,pos]=await rpc.multicall({allowFailure:false,blockNumber,contracts:[read(core,'idToMarketParams',[c.id]),read(core,'market',[c.id]),read(core,'position',[c.id,c.user])]});
  const calculatedId=keccak256(encodeAbiParameters([{type:'address'},{type:'address'},{type:'address'},{type:'address'},{type:'uint256'}],params));if(calculatedId!==c.id)throw new Error('Market ID mismatch');
  if(params[3].toLowerCase()!==irm){results.push({...c,status:'UNSUPPORTED_IRM'});continue;}
  const [enabled,lltvEnabled,binding,rate,price]=await rpc.multicall({allowFailure:false,blockNumber,contracts:[read(core,'isIrmEnabled',[irm]),read(core,'isLltvEnabled',[params[4]]),read(irm,'MORPHO'),read(irm,'borrowRateView',[params,state]),read(params[2],'price')]});
  if(!enabled||!lltvEnabled||binding.toLowerCase()!==core)throw new Error('Morpho/IRM binding failed');
  const stored=Object.fromEntries(fields.map((f,i)=>[f,state[i].toString()])),position={supplySharesRaw:pos[0].toString(),borrowSharesRaw:pos[1].toString(),collateralRaw:pos[2].toString()};
  const modeled=accrueMorphoMarket(stored,rate.toString(),block.timestamp.toString());
  // Actual contract's non-view accrual and its subsequent market getter run in
  // ONE non-persistent eth_call. This is independent of the JavaScript kernel.
  const [,after]=await rpc.multicall({allowFailure:false,blockNumber,contracts:[read(core,'accrueInterest',[params]),read(core,'market',[c.id])]});
  const reference=Object.fromEntries(fields.map((f,i)=>[f,after[i].toString()]));
  const agreement=fields.every(f=>reference[f]===modeled[f]);if(!agreement)throw new Error('Morpho actual accrual disagrees with model');
  let boundary=null;
  if(params[0].toLowerCase()==='0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48'&&params[1].toLowerCase()==='0x2260fac5e5542a773aa44fbcfedf7c193bc2c599'){
    const limit=BigInt(morphoWithdrawalLimit(modeled,position,price.toString(),params[4].toString()));
    if(limit>0n&&limit<BigInt(position.collateralRaw)){
      const call=assets=>({from:c.user,to:core,data:encodeFunctionData({abi,functionName:'withdrawCollateral',args:[params,assets,c.user,c.user]})});
      await rpc.request({method:'eth_call',params:[call(limit),toHex(blockNumber)]});
      let reason=null;
      try{await rpc.request({method:'eth_call',params:[call(limit+1n),toHex(blockNumber)]});throw new Error('Adjacent unhealthy withdrawal unexpectedly succeeded');}
      catch(e){for(let cause=e;cause;cause=cause.cause)if(typeof cause.data==='string'&&cause.data.startsWith('0x08c379a0')){reason=decodeErrorResult({abi:parseAbi(['error Error(string)']),data:cause.data}).args[0];break;}}
      if(reason!=='insufficient collateral')throw new Error('Expected specific unhealthy EVM revert, got '+reason);
      boundary={maximumWithdrawRaw:limit.toString(),healthyCall:'SUCCEEDED',nextUnitCall:'REVERTED_INSUFFICIENT_COLLATERAL',readOnly:true};
    }
  }
  const persisted=await rpc.readContract({address:core,abi,functionName:'market',args:[c.id],blockNumber});if(!persisted.every((v,i)=>v===state[i]))throw new Error('Unexpected stored-state change');
  results.push({...c,status:'ACCRUAL_REFERENCE_PASS',params,stored,position,rateRaw:rate.toString(),oraclePriceRaw:price.toString(),modeled,reference,boundary,risk:morphoRisk(modeled,position,price.toString(),params[4].toString()),oracleFreshness:'NOT_VALIDATED_FOR_PRODUCTION'});
}
if(!results.some(r=>r.status==='ACCRUAL_REFERENCE_PASS'))throw new Error('No Morpho reference case');
if((await rpc.getBlock({blockNumber})).hash!==block.hash)throw new Error('Reference block reorganized');
const report={classification:'STAGING_PROTOCOL_VALIDATION_NOT_PRODUCTION_SUPPORT',source:'https://github.com/morpho-org/morpho-blue/tree/8e26ca6a8dbc5089edcd67fb576248810fd2870a',checkedAt:new Date().toISOString(),blockNumber:blockNumber.toString(),blockHash:block.hash,blockTimestamp:block.timestamp.toString(),core,coreHash,irm,irmHash:keccak256(await rpc.getCode({address:irm,blockNumber})),method:'Actual accrueInterest followed by market in one non-persistent Multicall3 eth_call',results};
await mkdir('certification-reports',{recursive:true});await writeFile('certification-reports/morpho-accrual-reference.json',JSON.stringify(report,(_,v)=>typeof v==='bigint'?v.toString():v,2));
console.log(JSON.stringify({block:report.blockNumber,cases:results.map(r=>({id:r.id,status:r.status,healthFactorRaw:r.risk?.healthFactorRaw,interestRaw:r.modeled?.interestRaw})),productionSupport:false},null,2));
