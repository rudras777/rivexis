import {parseAbi,keccak256,encodeAbiParameters} from 'viem';
import {MORPHO_WBTC as config,validateMorphoWbtcOracle} from './defi-morpho-oracle.mjs';
import {accrueMorphoMarket,morphoBorrowAssets,morphoPositionMetrics} from './defi-morpho-model.mjs';
export const MORPHO='0xbbbbbbbbbb9cc5e90e3b3af64bdaf62c37eeffcb';
export const morphoParamsType='(address loanToken,address collateralToken,address oracle,address irm,uint256 lltv)';
const marketType='(uint128 totalSupplyAssets,uint128 totalSupplyShares,uint128 totalBorrowAssets,uint128 totalBorrowShares,uint128 lastUpdate,uint128 fee)';
export const morphoAbi=parseAbi([
  'function idToMarketParams(bytes32) view returns(address,address,address,address,uint256)',
  'function market(bytes32) view returns(uint128,uint128,uint128,uint128,uint128,uint128)',
  'function position(bytes32,address) view returns(uint256,uint128,uint128)',
  'function isIrmEnabled(address) view returns(bool)','function isLltvEnabled(uint256) view returns(bool)','function MORPHO() view returns(address)',
  `function borrowRateView(${morphoParamsType},${marketType}) view returns(uint256)`,
  `function accrueInterest(${morphoParamsType})`,
  `function repay(${morphoParamsType},uint256 assets,uint256 shares,address onBehalf,bytes data) returns(uint256,uint256)`,
  `function supplyCollateral(${morphoParamsType},uint256 assets,address onBehalf,bytes data)`,
  `function withdrawCollateral(${morphoParamsType},uint256 assets,address onBehalf,address receiver)`,
  `function borrow(${morphoParamsType},uint256 assets,uint256 shares,address onBehalf,address receiver) returns(uint256,uint256)`,
  'function VAULT() view returns(address)','function VAULT_CONVERSION_SAMPLE() view returns(uint256)',
  'function BASE_FEED_1() view returns(address)','function BASE_FEED_2() view returns(address)',
  'function QUOTE_FEED_1() view returns(address)','function QUOTE_FEED_2() view returns(address)',
  'function SCALE_FACTOR() view returns(uint256)','function price() view returns(uint256)',
  'function decimals() view returns(uint8)','function latestRoundData() view returns(uint80,int256,uint256,uint256,uint80)',
  'function balanceOf(address) view returns(uint256)','function allowance(address,address) view returns(uint256)',
]);
const fields=['totalSupplyAssetsRaw','totalSupplySharesRaw','totalBorrowAssetsRaw','totalBorrowSharesRaw','lastUpdateRaw','feeRaw'];
const stringify=value=>JSON.parse(JSON.stringify(value,(_,v)=>typeof v==='bigint'?v.toString():v));
export async function readMorphoPosition(rpc,block,wallet,capitalReserves=[]){
  const blockNumber=block.number,read=(address,functionName,args=[])=>({address,abi:morphoAbi,functionName,args});
  const [coreCode,irmCode,oracleCode]=await Promise.all([MORPHO,config.irm,config.oracle].map(address=>rpc.getCode({address,blockNumber})));
  if(!coreCode||keccak256(coreCode)!=='0xfa259fa317198f88f5fa3c119f06c066295dbcd47d715e0a30e1bcf94c02ef8c'||!irmCode||keccak256(irmCode)!=='0x73b578a0cd95d0d6e77f85a3945a670a9b8679670f8fc190ca97e89a1f07f6cd')throw new Error('Unvalidated Morpho deployment identity');
  const [params,stored,pos,enabled,lltvEnabled,binding]=await rpc.multicall({allowFailure:false,blockNumber,contracts:[read(MORPHO,'idToMarketParams',[config.marketId]),read(MORPHO,'market',[config.marketId]),read(MORPHO,'position',[config.marketId,wallet]),read(MORPHO,'isIrmEnabled',[config.irm]),read(MORPHO,'isLltvEnabled',[BigInt(config.lltvRaw)]),read(config.irm,'MORPHO')]});
  const id=keccak256(encodeAbiParameters([{type:'address'},{type:'address'},{type:'address'},{type:'address'},{type:'uint256'}],params));
  if(id!==config.marketId||!enabled||!lltvEnabled||binding.toLowerCase()!==MORPHO)throw new Error('Unvalidated Morpho market identity');
  // Discovery is deliberately bounded to this validated market, never all Morpho.
  if(pos[1]===0n&&pos[2]===0n)return null;
  const names=['VAULT','VAULT_CONVERSION_SAMPLE','BASE_FEED_1','BASE_FEED_2','QUOTE_FEED_1','QUOTE_FEED_2','SCALE_FACTOR','price'];
  const [rate,...values]=await rpc.multicall({allowFailure:false,blockNumber,contracts:[read(config.irm,'borrowRateView',[params,stored]),...names.map(n=>read(config.oracle,n))]});
  const readings=await rpc.multicall({allowFailure:false,blockNumber,contracts:[...config.feeds.flatMap(f=>[read(f.address,'decimals'),read(f.address,'latestRoundData')]),... [config.loanToken,config.collateralToken].flatMap(a=>[read(a,'decimals'),read(a,'balanceOf',[wallet]),read(a,'allowance',[wallet,MORPHO])])]});
  const evidence={marketId:id,loanToken:params[0],collateralToken:params[1],oracle:params[2],irm:params[3],lltvRaw:params[4].toString(),codeHash:oracleCode?keccak256(oracleCode):null,vault:values[0],vaultConversionSample:values[1],quoteFeed2:values[5],scaleFactor:values[6],price:values[7],loanDecimals:readings[6],collateralDecimals:readings[9],blockTimestamp:block.timestamp,
    feeds:config.feeds.map((f,i)=>({kind:f.kind,address:values[i+2],decimals:readings[i*2],round:readings[i*2+1],maxAgeSeconds:f.maxAge}))};
  if(!validateMorphoWbtcOracle(evidence))throw new Error('Unvalidated or stale Morpho oracle');
  const rawStored=Object.fromEntries(fields.map((f,i)=>[f,stored[i].toString()])),market=accrueMorphoMarket(rawStored,rate.toString(),block.timestamp.toString());
  const [,actual]=await rpc.multicall({allowFailure:false,blockNumber,contracts:[read(MORPHO,'accrueInterest',[params]),read(MORPHO,'market',[id])]});
  if(!fields.every((f,i)=>market[f]===actual[i].toString()))throw new Error('Morpho accrual fails actual contract reconciliation');
  const morphoPosition={borrowSharesRaw:pos[1].toString(),collateralRaw:pos[2].toString(),supplySharesRaw:pos[0].toString()};
  const token=(asset,symbol,decimals,collateralRaw,debtRaw,walletRaw,allowanceRaw,price,enabled)=>{
    const shared=capitalReserves.find(r=>r.asset.toLowerCase()===asset);if(shared&&shared.walletRaw!==walletRaw.toString())throw new Error('Cross-protocol wallet balance mismatch');
    return {asset,symbol,decimals,collateralRaw,debtRaw,walletRaw:walletRaw.toString(),allowanceRaw:allowanceRaw.toString(),priceRaw:shared?.priceRaw??price.toString(),ltBps:enabled?'8600':'0',collateralEnabled:enabled,supplyAllowed:enabled,borrowAllowed:!enabled,oracleState:'FRESH',isolation:false,oracleAdapter:'MORPHO_WBTC_USDC_V1',oracleSource:config.oracle};
  };
  const p={id:`morpho-blue:1:${id}:${wallet}`,protocol:'Morpho Blue',chainId:1,eMode:0,pool:MORPHO,marketId:id,loanToken:config.loanToken,collateralToken:config.collateralToken,lltvRaw:config.lltvRaw,marketParams:stringify(params),storedMarket:rawStored,market,morphoPosition,rateRaw:rate.toString(),oraclePriceRaw:values[7].toString(),oracleEvidence:stringify(evidence),reserves:[
    token(config.collateralToken,'WBTC',8,pos[2].toString(),'0',readings[10],readings[11],readings[1][1]*readings[3][1]/10n**8n,true),
    token(config.loanToken,'USDC',6,'0',morphoBorrowAssets(market,pos[1].toString()).toString(),readings[7],readings[8],readings[5][1],false),
  ]};
  p.observed=morphoPositionMetrics(p);return p;
}
