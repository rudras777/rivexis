import {MODEL} from './defi-model.mjs';
// Explicit educational fixture; never returned by a live RPC endpoint.
export function sampleSnapshot(now=Date.now()) {
  const reserves=[
    {asset:'0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',symbol:'WETH',decimals:18,collateralRaw:'10000000000000000000',debtRaw:'0',walletRaw:'2000000000000000000',allowanceRaw:'0',priceRaw:'300000000000',ltBps:'8000',collateralEnabled:true,supplyAllowed:true,oracleState:'FRESH',isolation:false},
    {asset:'0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',symbol:'USDC',decimals:6,collateralRaw:'0',debtRaw:'18000000000',walletRaw:'5000000000',allowanceRaw:'0',priceRaw:'100000000',ltBps:'7800',collateralEnabled:false,supplyAllowed:true,oracleState:'FRESH',isolation:false},
  ];
  return {model:MODEL,status:'READY',sample:true,wallet:'HYPOTHETICAL — no wallet',blockNumber:'SAMPLE',blockHash:'SAMPLE',blockTimestamp:Math.floor(now/1000),nativeBalanceRaw:'50000000000000000',observedHealthFactorRaw:'1333333333333333333',observedCollateralRaw:'3000000000000',observedDebtRaw:'1800000000000',positions:[{id:'sample:aave',protocol:'Aave V3',chainId:1,eMode:0,reserves}],warnings:['HYPOTHETICAL EDUCATIONAL SAMPLE. These are invented inputs, not live on-chain evidence.']};
}
