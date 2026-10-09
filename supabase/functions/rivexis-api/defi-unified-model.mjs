// Protocol routing preserves Aave integer semantics and Morpho native loan units.
import {MODEL as AAVE_MODEL,validateSnapshot as validateAave,metrics as aaveMetrics,frontier as enumerate,integer} from './defi-model.mjs';
import {morphoPositionMetrics,morphoBorrowAssets,morphoRepaymentForBudget} from './defi-morpho-model.mjs';
import {MORPHO_WBTC,validateMorphoWbtcOracle} from './defi-morpho-oracle.mjs';
export const MODEL='ethereum-lending-1';
export {format} from './defi-model.mjs';
export function metrics(p,shocks={},actions=[]){return p.protocol==='Morpho Blue'?morphoPositionMetrics(p,shocks,actions):aaveMetrics(p,shocks,actions);}
export function validateSnapshot(s,now=Date.now()){
  if(s?.model===AAVE_MODEL)return validateAave(s,now);
  if(!s||s.model!==MODEL||s.status!=='READY'||!Array.isArray(s.positions)||s.positions.length>4)throw new Error('Validated supported portfolio required');
  if(!Number.isSafeInteger(s.blockTimestamp)||now/1000-s.blockTimestamp>180||s.blockTimestamp>now/1000+30)throw new Error('Snapshot is stale; refresh evidence');
  const ids=new Set(),wallet=new Map();
  for(const p of s.positions){
    if(ids.has(p.id)||p.chainId!==1)throw new Error('Duplicate or unsupported position');ids.add(p.id);
    if(p.protocol==='Aave V3')validateAave({...s,model:AAVE_MODEL,positions:[p]},now);
    else if(p.protocol==='Morpho Blue'){
      if(p.marketId!==MORPHO_WBTC.marketId||p.loanToken!==MORPHO_WBTC.loanToken||p.collateralToken!==MORPHO_WBTC.collateralToken||p.lltvRaw!==MORPHO_WBTC.lltvRaw||p.reserves?.length!==2)throw new Error('Unsupported Morpho market');
      const e=structuredClone(p.oracleEvidence);try{for(const k of ['vaultConversionSample','scaleFactor','price','blockTimestamp'])e[k]=integer(e[k]);for(const f of e.feeds)f.round=f.round.map(integer);}catch{throw new Error('Invalid Morpho oracle evidence');}
      if(!validateMorphoWbtcOracle(e)||e.blockTimestamp!==BigInt(s.blockTimestamp)||e.price.toString()!==p.oraclePriceRaw)throw new Error('Unvalidated Morpho oracle');
      const c=p.reserves.find(r=>r.asset===p.collateralToken),loan=p.reserves.find(r=>r.asset===p.loanToken);
      if(!c||!loan||c.decimals!==8||loan.decimals!==6||c.collateralRaw!==p.morphoPosition.collateralRaw||loan.debtRaw!==morphoBorrowAssets(p.market,p.morphoPosition.borrowSharesRaw).toString()||c.debtRaw!=='0'||loan.collateralRaw!=='0')throw new Error('Morpho reserve accounting mismatch');
      metrics(p);
    }else throw new Error('Unsupported protocol');
    for(const r of p.reserves){
      if(!/^0x[\da-fA-F]{40}$/.test(r.asset)||!Number.isInteger(r.decimals)||r.decimals<0||r.decimals>36||r.oracleState!=='FRESH'||integer(r.priceRaw)===0n)throw new Error('Invalid reserve evidence');
      for(const key of ['walletRaw','allowanceRaw','collateralRaw','debtRaw'])integer(r[key]);
      const key=r.asset.toLowerCase(),previous=wallet.get(key);
      if(previous&&(previous.walletRaw!==r.walletRaw||previous.priceRaw!==r.priceRaw||previous.decimals!==r.decimals))throw new Error('Shared wallet balance or capital price mismatch');
      wallet.set(key,r);
    }
  }
  return s;
}
export function scenario(s,shocks={},actions=[],now=Date.now()){
  validateSnapshot(s,now);const assets=new Set(s.positions.flatMap(p=>p.reserves.map(r=>r.asset.toLowerCase())));
  if(!shocks||typeof shocks!=='object'||Array.isArray(shocks)||Object.keys(shocks).some(k=>!assets.has(k)))throw new Error('Unknown scenario asset');
  for(const v of Object.values(shocks))if(!Number.isInteger(v)||v< -9500||v>10000)throw new Error('Invalid price shock');
  for(const a of actions){const p=s.positions.find(p=>p.id===a.positionId);if(!p?.reserves.some(r=>r.asset.toLowerCase()===a.asset.toLowerCase()))throw new Error('Unsupported action position or asset');}
  return s.positions.map(p=>({positionId:p.id,...metrics(p,shocks,actions)}));
}
export function frontier(s,input,now=Date.now()){
  if(s?.model===AAVE_MODEL)return enumerate(s,input,now);
  return enumerate(s,input,now,{validate:validateSnapshot,scenario,prepareRepayment:(p,amount)=>{
    if(p.protocol!=='Morpho Blue')return {amountRaw:amount.toString()};
    const a=morphoRepaymentForBudget(p.market,p.morphoPosition,amount.toString());return a?{amountRaw:a.assetsRaw,sharesRaw:a.sharesRaw}:null;
  }});
}
