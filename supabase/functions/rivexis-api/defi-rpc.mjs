import {createPublicClient, http, parseAbi, encodeFunctionData, isAddress, getAddress, keccak256} from 'viem';
import {mainnet} from 'viem/chains';
import {MODEL, WAD, metrics, integer, decimal, validateSnapshot} from './defi-model.mjs';
import {WBTC_ORACLE,validateWbtcOracle} from './defi-oracles.mjs';

export const POOL = '0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2';
export const ORACLE = '0x54586bE62E3c3580375aE3723C145253060Ca0C2';
// Resolved from PoolAddressesProvider at the same block; no stale hardcoded provider.
export const ADDRESSES_PROVIDER = '0x2f39d218133AFaB8F2B819B1066c7E434Ad94E9e';
// Runtime EIP-1967 identity verified on Ethereum on 2026-10-09. An upgrade
// requires revalidation, even if a published address-book implementation lags.
const VALIDATED_POOL_IMPLEMENTATION='0x728a138a4823392c2efa55e028d434f526fe03cf';
export const poolAbi = parseAbi([
  'function getReservesList() view returns (address[])',
  'function getUserEMode(address user) view returns (uint256)',
  'function getUserAccountData(address user) view returns (uint256 totalCollateralBase,uint256 totalDebtBase,uint256 availableBorrowsBase,uint256 currentLiquidationThreshold,uint256 ltv,uint256 healthFactor)',
  'function getConfiguration(address asset) view returns (uint256 data)',
  'function supply(address asset,uint256 amount,address onBehalfOf,uint16 referralCode)',
  'function repay(address asset,uint256 amount,uint256 interestRateMode,address onBehalfOf) returns (uint256)',
  'function withdraw(address asset,uint256 amount,address to) returns (uint256)',
  'function borrow(address asset,uint256 amount,uint256 interestRateMode,uint16 referralCode,address onBehalfOf)',
]);
const providerAbi = parseAbi(['function getPoolDataProvider() view returns (address)','function getPool() view returns (address)','function getPriceOracle() view returns (address)']);
const dataAbi = parseAbi(['function getUserReserveData(address asset,address user) view returns (uint256,uint256,uint256,uint256,uint256,uint256,uint256,uint40,bool)']);
const oracleAbi = parseAbi(['function getAssetPrice(address asset) view returns (uint256)','function getSourceOfAsset(address asset) view returns (address)','function BASE_CURRENCY_UNIT() view returns (uint256)']);
const tokenAbi = parseAbi(['function symbol() view returns (string)','function balanceOf(address user) view returns (uint256)','function allowance(address owner,address spender) view returns (uint256)']);
const sourceAbi = parseAbi(['function latestRoundData() view returns (uint80,int256,uint256,uint256,uint80)']);
const capAbi = parseAbi(['function ASSET_TO_USD_AGGREGATOR() view returns (address)','function getPriceCap() view returns (int256)','function decimals() view returns (uint8)']);
const compositeAbi=parseAbi(['function PEG_TO_BASE() view returns(address)','function ASSET_TO_PEG() view returns(address)','function DENOMINATOR() view returns(int256)','function decimals() view returns(uint8)']);
const STABLE_SOURCES={
  '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48':'0x3f73f03aa83b2a48ed27e964ed0fdb590332095b',
  '0xdac17f958d2ee523a2206206994597c13d831ec7':'0x260326c220e469358846b187ee53328303efe19c',
};
const FRESHNESS = {
  '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2': 4200,
  '0x2260fac5e5542a773aa44fbcfedf7c193bc2c599': 4200,
  '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48': 90000,
  '0xdac17f958d2ee523a2206206994597c13d831ec7': 90000,
};
export function client(url='https://ethereum.publicnode.com') {
  return createPublicClient({chain:mainnet,transport:http(url,{timeout:12000,retryCount:0}),batch:{multicall:{batchSize:24000}}});
}
function good(value) {if(value.status!=='success')throw new Error('Protocol evidence read failed'); return value.result;}
export async function snapshot(wallet, rpc=client(), pinnedBlock=null) {
  if (!isAddress(wallet, {strict:true}) || /^0x0{40}$/i.test(wallet)) throw new Error('Enter a valid Ethereum address; mixed-case addresses must have a valid checksum');
  wallet=getAddress(wallet);
  if (await rpc.getChainId() !== 1) throw new Error('RPC is not Ethereum mainnet');
  const block = pinnedBlock??await rpc.getBlock({blockTag:'latest'});
  if (!block.number || !block.hash || Date.now()/1000-Number(block.timestamp)>180 || Number(block.timestamp)>Date.now()/1000+30) throw new Error('Latest Ethereum block is stale or has an invalid timestamp');
  const blockNumber=block.number, read=(address,abi,functionName,args=[])=>({address,abi,functionName,args});
  const implementationSlot=await rpc.getStorageAt({address:POOL,slot:'0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc',blockNumber});
  const poolImplementation=implementationSlot?`0x${implementationSlot.slice(-40)}`:null;
  const identity=await rpc.multicall({blockNumber,contracts:[read(ADDRESSES_PROVIDER,providerAbi,'getPoolDataProvider'),read(ADDRESSES_PROVIDER,providerAbi,'getPool'),read(ADDRESSES_PROVIDER,providerAbi,'getPriceOracle'),read(ORACLE,oracleAbi,'BASE_CURRENCY_UNIT')]});
  const dataProvider=good(identity[0]);
  if(good(identity[1]).toLowerCase()!==POOL.toLowerCase()||good(identity[2]).toLowerCase()!==ORACLE.toLowerCase()||good(identity[3])!==100000000n)throw new Error('Protocol deployment identity or price unit changed');
  const initial=await rpc.multicall({blockNumber,contracts:[read(POOL,poolAbi,'getReservesList'),read(POOL,poolAbi,'getUserEMode',[wallet]),read(POOL,poolAbi,'getUserAccountData',[wallet])]});
  const assets=good(initial[0]), eMode=Number(good(initial[1])), account=good(initial[2]);
  if (assets.length>80) throw new Error('Reserve count exceeds bounded beta capacity');
  const balances=await rpc.multicall({blockNumber,contracts:assets.map(asset=>read(dataProvider,dataAbi,'getUserReserveData',[asset,wallet]))});
  const active=assets.map((asset,i)=>({asset,user:good(balances[i])})).filter(({user})=>user[0]>0n||user[1]>0n||user[2]>0n);
  const details=await rpc.multicall({blockNumber,contracts:active.flatMap(({asset})=>[read(POOL,poolAbi,'getConfiguration',[asset]),read(ORACLE,oracleAbi,'getAssetPrice',[asset]),read(ORACLE,oracleAbi,'getSourceOfAsset',[asset]),read(asset,tokenAbi,'symbol'),read(asset,tokenAbi,'balanceOf',[wallet]),read(asset,tokenAbi,'allowance',[wallet,POOL])])});
  const sources=active.map((_,i)=>good(details[i*6+2]));
  const rounds=active.length?await rpc.multicall({blockNumber,contracts:sources.map(source=>read(source,sourceAbi,'latestRoundData'))}):[];
  const oracleEvidence=sources.map((source,i)=>({source,feed:source,round:rounds[i].status==='success'?rounds[i].result:null,cap:null,valid:true}));
  const stableIndices=active.map((a,i)=>STABLE_SOURCES[a.asset.toLowerCase()]===sources[i].toLowerCase()?i:-1).filter(i=>i>=0);
  if(stableIndices.length){
    const adapters=await rpc.multicall({blockNumber,contracts:stableIndices.flatMap(i=>[read(sources[i],capAbi,'ASSET_TO_USD_AGGREGATOR'),read(sources[i],capAbi,'getPriceCap'),read(sources[i],capAbi,'decimals')])});
    const feeds=stableIndices.map((i,j)=>good(adapters[j*3]));
    const feedRounds=await rpc.multicall({blockNumber,contracts:feeds.map(feed=>read(feed,sourceAbi,'latestRoundData'))});
    stableIndices.forEach((i,j)=>{
      const round=feedRounds[j].status==='success'?feedRounds[j].result:null,cap=good(adapters[j*3+1]);
      oracleEvidence[i]={source:sources[i],feed:feeds[j],round,cap,valid:good(adapters[j*3+2])===8&&round&&cap>0n&&(round[1]>cap?cap:round[1])===good(details[i*6+1])};
    });
  }
  const wbtcIndex=active.findIndex((a,i)=>a.asset.toLowerCase()===WBTC_ORACLE.asset&&sources[i].toLowerCase()===WBTC_ORACLE.source);
  if(wbtcIndex>=0){
    const source=sources[wbtcIndex];
    const adapter=await rpc.multicall({blockNumber,contracts:['PEG_TO_BASE','ASSET_TO_PEG','DENOMINATOR','decimals'].map(name=>read(source,compositeAbi,name))});
    const feedResults=await rpc.multicall({blockNumber,contracts:[WBTC_ORACLE.baseFeed,WBTC_ORACLE.ratioFeed].flatMap(feed=>[read(feed,sourceAbi,'latestRoundData'),read(feed,compositeAbi,'decimals')])});
    const code=await rpc.getCode({address:source,blockNumber}),codeHash=code?keccak256(code):null;
    const value=r=>r.status==='success'?r.result:null;
    const baseRound=value(feedResults[0]),ratioRound=value(feedResults[2]);
    const valid=validateWbtcOracle({source,codeHash,baseFeed:value(adapter[0]),ratioFeed:value(adapter[1]),denominator:value(adapter[2]),decimals:value(adapter[3]),baseRound,ratioRound,baseDecimals:value(feedResults[1]),ratioDecimals:value(feedResults[3]),price:good(details[wbtcIndex*6+1]),blockTimestamp:block.timestamp});
    const components=[{kind:'BTC_USD',feed:WBTC_ORACLE.baseFeed,round:baseRound,maxAge:WBTC_ORACLE.baseMaxAge},{kind:'WBTC_BTC',feed:WBTC_ORACLE.ratioFeed,round:ratioRound,maxAge:WBTC_ORACLE.ratioMaxAge}];
    oracleEvidence[wbtcIndex]={source,feed:null,round:null,cap:null,valid,composite:true,codeHash,components};
  }
  const warnings = [], reserves=active.map(({asset,user},i)=>{
    const cfg=good(details[i*6]), price=good(details[i*6+1]), decimals=Number((cfg>>48n)&255n), debtCeiling=cfg>>212n&((1n<<40n)-1n), paused=(cfg>>60n&1n)===1n;
    const {round,feed,cap,valid,composite,codeHash,components}=oracleEvidence[i],age=FRESHNESS[asset.toLowerCase()];
    const directSource=asset.toLowerCase()==='0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2'&&sources[i].toLowerCase()==='0x5424384b256154046e9667ddfaaa5e550145215e'&&round&&round[1]===price;
    const stableSource=STABLE_SOURCES[asset.toLowerCase()]===sources[i].toLowerCase();
    const fresh=Boolean(composite?valid:(directSource||stableSource)&&valid&&age&&round&&round[0]>0n&&round[4]>=round[0]&&round[1]>0n&&round[3]>0n&&round[3]<=block.timestamp&&block.timestamp-round[3]<=BigInt(age));
    if(!fresh)warnings.push(`${good(details[i*6+3])}: oracle timestamp/heartbeat adapter is unvalidated or stale`);
    if(debtCeiling>0n)warnings.push('Isolation collateral requires a separately validated adapter');
    if(user[1]>0n)warnings.push('Stable debt is unsupported in this model');
    const componentEvidence=components?.map(c=>({kind:c.kind,feed:c.feed,maxAgeSeconds:c.maxAge,roundId:c.round?.[0].toString()??null,answerRaw:c.round?.[1].toString()??null,startedAt:c.round?.[2].toString()??null,updatedAt:c.round?.[3].toString()??null,answeredInRound:c.round?.[4].toString()??null}));
    const updatedAt=composite&&components.every(c=>c.round)?components.reduce((old,c)=>c.round[3]<old?c.round[3]:old,block.timestamp):round?.[3];
    return {asset,symbol:good(details[i*6+3]),decimals,collateralRaw:user[0].toString(),debtRaw:(user[1]+user[2]).toString(),walletRaw:good(details[i*6+4]).toString(),allowanceRaw:good(details[i*6+5]).toString(),priceRaw:price.toString(),ltBps:((cfg>>16n)&65535n).toString(),ltvBps:(cfg&65535n).toString(),collateralEnabled:user[8],supplyAllowed:(cfg>>56n&1n)===1n&&(cfg>>57n&1n)===0n&&!paused,borrowAllowed:(cfg>>58n&1n)===1n&&!paused,oracleState:fresh?'FRESH':'UNVALIDATED',oracleSource:sources[i],underlyingFeed:feed,oracleAdapter:composite?'WBTC_BTC_USD':'DIRECT_OR_STABLE_CAP',oracleCodeHash:codeHash??null,oracleComponents:componentEvidence??null,priceCapRaw:cap?.toString()??null,oracleUpdatedAt:updatedAt?.toString()??null,isolation:debtCeiling>0n,configurationRaw:cfg.toString(),stableDebtRaw:user[1].toString(),scaledVariableDebtRaw:user[4].toString(),liquidityRateRay:user[6].toString()};
  });
  if(eMode!==0)warnings.push('eMode is observable but unsupported for scenario and action modeling');
  if(poolImplementation!==VALIDATED_POOL_IMPLEMENTATION)warnings.push('Pool implementation changed; financial modeling requires revalidation');
  const position={id:`aave-v3:1:${wallet}`,chainId:1,protocol:'Aave V3',pool:POOL,eMode,reserves};
  const modeled=metrics(position), observed=account[1]===0n?null:account[5].toString();
  if(BigInt(modeled.collateralRaw)!==account[0]||BigInt(modeled.debtRaw)!==account[1]||(observed&&modeled.healthFactorRaw&&abs(BigInt(observed)-BigInt(modeled.healthFactorRaw))>1n))warnings.push('Reserve accounting does not reconcile with Pool.getUserAccountData; modeling disabled');
  if(reserves.some(r=>integer(r.priceRaw)===0n))warnings.push('Oracle returned a zero price');
  const native=await rpc.getBalance({address:wallet,blockNumber});
  const end=await rpc.getBlock({blockNumber});
  if(end.hash!==block.hash)throw new Error('Block changed during snapshot; refresh after chain reorganization');
  return {model:MODEL,oracleValidation:'ethereum-aave-oracles-2',status:warnings.length?'UNSUPPORTED':'READY',wallet,chainId:1,protocol:'Aave V3',pool:POOL,poolImplementation,oracle:ORACLE,dataProvider,blockNumber:blockNumber.toString(),blockHash:block.hash,blockTimestamp:Number(block.timestamp),fetchedAt:new Date().toISOString(),source:'Ethereum RPC / Aave V3 contracts',rpcHost:new URL(rpc.transport.url||'https://ethereum.publicnode.com').host,nativeBalanceRaw:native.toString(),observedCollateralRaw:account[0].toString(),observedDebtRaw:account[1].toString(),observedHealthFactorRaw:observed,positions:active.length?[position]:[],warnings,limitations:['Single Ethereum Aave V3 account; other protocols and chains are not discovered.','Balances include debt interest accrued by the protocol at the snapshot block. Future interest and governance changes are not forecast.','Oracle timestamp support is restricted to validated WETH, USDC, USDT and WBTC sources. WBTC requires pinned adapter bytecode and two timestamped component feeds; other sources require separate validation. An RPC response alone does not independently certify the provider.']};
}
function abs(n){return n<0n?-n:n;}
export async function gasguard(input,rpc=client()) {
  const s=await snapshot(input.wallet,rpc); validateSnapshot(s);
  const p=s.positions[0], r=p?.reserves.find(r=>r.asset.toLowerCase()===String(input.asset).toLowerCase());
  if(!r||!['repay','supply','withdraw','borrow'].includes(input.kind))throw new Error('Unsupported asset or transaction');
  const amount=decimal(input.amount,r.decimals); if(amount===0n)throw new Error('Amount must be greater than zero');
  if(input.kind==='supply'&&!r.supplyAllowed)throw new Error('Reserve cannot accept collateral supply');
  if(input.kind==='borrow'&&!r.borrowAllowed)throw new Error('Reserve borrowing is disabled');
  const blockers=[];
  if(['repay','supply'].includes(input.kind)){if(amount>integer(r.walletRaw))blockers.push('Insufficient wallet token balance');if(amount>integer(r.allowanceRaw))blockers.push('Pool allowance is insufficient; a separate approval is required');}
  const action={positionId:p.id,asset:r.asset,kind:input.kind,amountRaw:amount.toString()};
  const before=metrics(p),after=metrics(p,{},[action]);
  const args=input.kind==='repay'?[r.asset,amount,2n,s.wallet]:input.kind==='supply'?[r.asset,amount,s.wallet,0]:input.kind==='withdraw'?[r.asset,amount,s.wallet]:[r.asset,amount,2n,0,s.wallet];
  const data=encodeFunctionData({abi:poolAbi,functionName:input.kind,args});
  const blockNumber=BigInt(s.blockNumber),call={account:s.wallet,to:POOL,data,blockNumber};
  let simulation='NOT_RUN',gas=null,fees=null;
  try{await rpc.call(call);simulation='SUCCEEDED_AT_BLOCK';gas=await rpc.estimateGas(call);fees=await rpc.estimateFeesPerGas();}catch{simulation='REVERTED_OR_RPC_UNAVAILABLE';blockers.push('RPC call or gas estimate failed; execution remains unverified');}
  const maxFee=fees?.maxFeePerGas??fees?.gasPrice??null,cost=gas!==null&&maxFee!==null?gas*maxFee*120n/100n:null;
  if(cost!==null&&cost>BigInt(s.nativeBalanceRaw))blockers.push('Insufficient native ETH for gas reserve');
  if(after.liquidatable)blockers.push('Modeled health factor below liquidation threshold');
  const nonce=await rpc.getTransactionCount({address:s.wallet,blockNumber});
  const end=await rpc.getBlock({blockNumber});if(end.hash!==s.blockHash)throw new Error('Block changed during transaction preview');
  return {model:MODEL,blockNumber:s.blockNumber,blockHash:s.blockHash,wallet:s.wallet,to:POOL,data,nonceAtBlock:nonce,action,before,after,simulation,gasRaw:gas?.toString()??null,maxFeePerGasRaw:maxFee?.toString()??null,feeReserveWei:cost?.toString()??null,nativeBalanceRaw:s.nativeBalanceRaw,allowanceRaw:r.allowanceRaw,tokenBalanceRaw:r.walletRaw,blockers,status:blockers.length?'BLOCKED':'PREVIEW_ONLY',warnings:['eth_call and eth_estimateGas are independent read-only calls, not a state fork or signed transaction.','Fees are a current network estimate with a 20% gas reserve; inclusion costs and future execution may differ.','Nonce is observed at the snapshot block; pending transactions and replacement rules are not simulated.','No arbitrary contract traces, MEV guarantees, swaps, signing or automatic execution.']};
}
