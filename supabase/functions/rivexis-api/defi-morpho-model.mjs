// Morpho-specific validation kernel. Not wired into production discovery yet.
// Mathematical semantics: Morpho core, SharesMathLib and MorphoBalancesLib.
// Loan quantities stay in native units; health uses the market's 1e36 oracle.
import {integer,WAD} from './defi-model.mjs';
export const MORPHO_MODEL='morpho-blue-1';
export const VIRTUAL_SHARES=1000000n,ORACLE_SCALE=10n**36n;
const limit128=2n**128n;
function uint(v){return integer(typeof v==='bigint'?v.toString():v)}
function u128(v){const n=uint(v);if(n>=limit128)throw new Error('Morpho uint128 overflow');return n}
function mulDiv(a,b,d,up=false){a=uint(a);b=uint(b);d=uint(d);if(!d)throw new Error('Zero denominator');const product=uint(a*b),adjusted=up?uint(product+d-1n):product;return adjusted/d}
export function compoundedRate(rateRaw,elapsedRaw){
  const first=uint(uint(rateRaw)*uint(elapsedRaw)),second=mulDiv(first,first,2n*WAD),third=mulDiv(second,first,3n*WAD);
  return uint(first+second+third);
}
export function accrueMorphoMarket(market,rateRaw,timestampRaw,zeroIrm=false){
  const supply=u128(market.totalSupplyAssetsRaw),supplyShares=u128(market.totalSupplySharesRaw),borrow=u128(market.totalBorrowAssetsRaw),borrowShares=u128(market.totalBorrowSharesRaw),last=u128(market.lastUpdateRaw),fee=u128(market.feeRaw),now=u128(timestampRaw);
  if(!last||last>now||fee>WAD/4n)throw new Error('Invalid Morpho market time or fee');
  const elapsed=now-last,interest=zeroIrm?0n:u128(mulDiv(borrow,compoundedRate(rateRaw,elapsed),WAD));
  const nextSupply=u128(supply+interest),nextBorrow=u128(borrow+interest),feeAssets=mulDiv(interest,fee,WAD),feeShares=u128(mulDiv(feeAssets,uint(supplyShares+VIRTUAL_SHARES),uint(nextSupply-feeAssets+1n)));
  return {...market,totalSupplyAssetsRaw:nextSupply.toString(),totalSupplySharesRaw:u128(supplyShares+feeShares).toString(),totalBorrowAssetsRaw:nextBorrow.toString(),totalBorrowSharesRaw:borrowShares.toString(),lastUpdateRaw:now.toString(),interestRaw:interest.toString(),feeSharesRaw:feeShares.toString(),elapsedRaw:elapsed.toString()};
}
export function morphoBorrowAssets(market,sharesRaw){
  const shares=u128(sharesRaw),totalShares=u128(market.totalBorrowSharesRaw),assets=u128(market.totalBorrowAssetsRaw);
  if(shares>totalShares)throw new Error('Position shares exceed market shares');
  return mulDiv(shares,assets+1n,totalShares+VIRTUAL_SHARES,true);
}
export function morphoRisk(market,position,oraclePriceRaw,lltvRaw){
  const lltv=uint(lltvRaw),price=uint(oraclePriceRaw),collateral=u128(position.collateralRaw),shares=u128(position.borrowSharesRaw);
  if(!price||lltv>=WAD)throw new Error('Invalid Morpho oracle price or LLTV');
  const debt=morphoBorrowAssets(market,shares),collateralInLoan=mulDiv(collateral,price,ORACLE_SCALE),maxBorrow=mulDiv(collateralInLoan,lltv,WAD);
  return {borrowAssetsRaw:debt.toString(),collateralInLoanRaw:collateralInLoan.toString(),maxBorrowAssetsRaw:maxBorrow.toString(),healthFactorRaw:debt?mulDiv(maxBorrow,WAD,debt).toString():null,healthy:debt===0n||maxBorrow>=debt,liquidatable:debt>0n&&maxBorrow<debt};
}
export function morphoWithdrawalLimit(market,position,oraclePriceRaw,lltvRaw){
  const debt=morphoBorrowAssets(market,position.borrowSharesRaw),collateral=u128(position.collateralRaw),price=uint(oraclePriceRaw),lltv=uint(lltvRaw);
  if(!price||!lltv||lltv>=WAD)throw new Error('Invalid Morpho liquidation inputs');
  if(!debt)return collateral.toString();
  const minLoanCollateral=mulDiv(debt,WAD,lltv,true),minimumCollateral=mulDiv(minLoanCollateral,ORACLE_SCALE,price,true);
  return (minimumCollateral>collateral?0n:collateral-minimumCollateral).toString();
}
export function morphoRepayShares(market,position,sharesRaw){
  const shares=u128(sharesRaw),owned=u128(position.borrowSharesRaw);if(!shares||shares>owned)throw new Error('Invalid Morpho repayment shares');
  const assets=morphoBorrowAssets(market,shares),totalAssets=u128(market.totalBorrowAssetsRaw),totalShares=u128(market.totalBorrowSharesRaw);
  const nextMarket={...market,totalBorrowAssetsRaw:(assets>totalAssets?0n:totalAssets-assets).toString(),totalBorrowSharesRaw:(totalShares-shares).toString()};
  const nextPosition={...position,borrowSharesRaw:(owned-shares).toString()};
  return {assetsRaw:assets.toString(),sharesRaw:shares.toString(),market:nextMarket,position:nextPosition,borrowAssetsAfterRaw:morphoBorrowAssets(nextMarket,nextPosition.borrowSharesRaw).toString()};
}
export function morphoRepaymentForBudget(market,position,budgetAssetsRaw){
  const assets=uint(budgetAssetsRaw),owned=u128(position.borrowSharesRaw),calculated=mulDiv(assets,uint(u128(market.totalBorrowSharesRaw)+VIRTUAL_SHARES),uint(u128(market.totalBorrowAssetsRaw)+1n));
  const shares=calculated>owned?owned:calculated;
  if(!shares)return null;
  const action=morphoRepayShares(market,position,shares);if(uint(action.assetsRaw)>assets)throw new Error('Repayment exceeds allocated assets');return action;
}
export function shockMorphoOracle(priceRaw,collateralShockBps=0,loanShockBps=0){
  for(const s of [collateralShockBps,loanShockBps])if(!Number.isInteger(s)||s< -9500||s>10000)throw new Error('Invalid Morpho price shock');
  return mulDiv(uint(priceRaw),BigInt(10000+collateralShockBps),BigInt(10000+loanShockBps)).toString();
}
