// Conditional collateral-price boundaries, never a cross-protocol safety score.
import {integer,WAD} from './defi-model.mjs';
import {validateSnapshot,scenario,metrics} from './defi-unified-model.mjs';
import {morphoBorrowAssets} from './defi-morpho-model.mjs';
const SCALE=10n**36n,ceil=(n,d)=>(n+d-1n)/d;
function aaveBoundary(p,r,shocks){
  const reserves=p.reserves.map(x=>({...x,priceRaw:(integer(x.priceRaw)*BigInt(10000+(shocks[x.asset.toLowerCase()]??0))/10000n).toString()}));
  const current=BigInt(reserves.find(x=>x.asset===r.asset).priceRaw);
  if(!current)return {state:'ZERO_SCENARIO_PRICE'};
  if(BigInt(r.debtRaw)>0n)return {state:'SAME_ASSET_DEBT_UNVALIDATED',reason:'A simultaneous collateral/debt price path requires separate boundary validation.'};
  const healthy=price=>!metrics({...p,reserves:reserves.map(x=>x.asset===r.asset?{...x,priceRaw:price.toString()}:x)}).liquidatable;
  if(healthy(0n))return {state:'NO_DOWNWARD_TRIGGER',reason:'Other collateral covers this position even if this collateral reference falls to zero.'};
  let high=current;
  for(let i=0;i<8&&!healthy(high);i++)high*=2n;
  if(!healthy(high))return {state:'OUTSIDE_BOUNDED_SEARCH'};
  let low=0n;
  while(high-low>1n){const middle=(low+high)/2n;if(healthy(middle))high=middle;else low=middle;}
  return {state:'AVAILABLE',currentPriceRaw:current.toString(),minimumHealthyPriceRaw:high.toString(),firstLiquidatablePriceRaw:low.toString(),distanceBps:((current-high)*10000n/current).toString(),basis:'AAVE_ORACLE_USD_1E8',reason:'One collateral oracle price changes; all other prices, balances, thresholds and debt accrual stay fixed.'};
}
function morphoBoundary(p,r,shocks,outcome){
  const debt=morphoBorrowAssets(p.market,p.morphoPosition.borrowSharesRaw),collateral=integer(p.morphoPosition.collateralRaw),lltv=integer(p.lltvRaw);
  if(!collateral)return {state:'NO_COLLATERAL'};
  const currentOracle=integer(outcome.oraclePriceRaw),currentPrice=integer(r.priceRaw)*BigInt(10000+(shocks[r.asset.toLowerCase()]??0))/10000n;
  if(!currentPrice||!currentOracle)return {state:'ZERO_SCENARIO_PRICE'};
  // Invert both floors in Morpho maxBorrow; native loan shares are rounded up.
  const boundary=ceil(ceil(debt*WAD,lltv)*SCALE,collateral);
  return {state:'AVAILABLE',currentPriceRaw:currentPrice.toString(),minimumHealthyPriceRaw:ceil(currentPrice*boundary,currentOracle).toString(),firstLiquidatablePriceRaw:null,oracleBoundaryRaw:boundary.toString(),firstLiquidatableOracleRaw:(boundary-1n).toString(),distanceBps:((currentOracle-boundary)*10000n/currentOracle).toString(),basis:'MORPHO_RELATIVE_ORACLE_1E36',reason:'Exact native-loan oracle boundary; USD price is a proportional reference estimate. Loan oracle components, balances, LLTV and accrued debt stay fixed.'};
}
export function liquidationAnalysis(snapshot,shocks={},now=Date.now()){
  validateSnapshot(snapshot,now);const outcomes=scenario(snapshot,shocks,[],now),rows=[],exposure=new Map();
  let totalCollateral=0n,totalDebt=0n;
  snapshot.positions.forEach((p,i)=>{
    const o=outcomes[i];totalCollateral+=BigInt(o.collateralRaw);totalDebt+=BigInt(o.debtRaw);
    for(const r of p.reserves){
      const price=integer(r.priceRaw)*BigInt(10000+(shocks[r.asset.toLowerCase()]??0))/10000n,unit=10n**BigInt(r.decimals);
      const key=r.asset.toLowerCase(),e=exposure.get(key)??{asset:r.asset,symbol:r.symbol,collateral:0n,debt:0n};
      if(r.collateralEnabled)e.collateral+=integer(r.collateralRaw)*price/unit;
      e.debt+=ceil(integer(r.debtRaw)*price,unit);exposure.set(key,e);
      if(!r.collateralEnabled||integer(r.collateralRaw)===0n)continue;
      const base={positionId:p.id,protocol:p.protocol,asset:r.asset,symbol:r.symbol,currentPriceRaw:price.toString(),healthFactorRaw:o.healthFactorRaw,liquidatable:o.liquidatable};
      rows.push({...base,...(o.healthFactorRaw===null?{state:'NO_DEBT'}:p.protocol==='Aave V3'?aaveBoundary(p,r,shocks):morphoBoundary(p,r,shocks,o))});
    }
  });
  const ranked=rows.filter(r=>r.state==='AVAILABLE').sort((a,b)=>{const x=BigInt(a.distanceBps),y=BigInt(b.distanceBps);return x<y?-1:x>y?1:0;});
  return {model:'conditional-collateral-boundaries-1',blockNumber:snapshot.blockNumber,blockHash:snapshot.blockHash,shocks,rows,closest:ranked[0]??null,exposures:[...exposure.values()].map(e=>({asset:e.asset,symbol:e.symbol,collateralRaw:e.collateral.toString(),debtRaw:e.debt.toString(),collateralBps:totalCollateral?(e.collateral*10000n/totalCollateral).toString():null,debtBps:totalDebt?(e.debt*10000n/totalDebt).toString():null})),limitations:['Conditional single-collateral price paths, not a prediction of which asset moves first.','Separate liquidation domains never offset one another. Minimum health and each position eligibility remain primary.','Oracle-reference prices differ from executable market prices. Interest, governance changes and joint future moves are held fixed.','Same-token collateral and debt price boundaries remain explicitly unvalidated. Percent distances truncate to one basis point; adjacent-unit boundary evidence is retained.']};
}
