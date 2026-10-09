// Morpho-specific fixed-point kernel for the bounded validated market adapter.
// Mathematical semantics: Morpho core, SharesMathLib and MorphoBalancesLib.
// Loan quantities stay in native units; health uses the market's 1e36 oracle.
const WAD=10n**18n;
export const MORPHO_MODEL='morpho-blue-1';
export const VIRTUAL_SHARES=1000000n,ORACLE_SCALE=10n**36n;
const limit128=2n**128n;
function uint(v){if(typeof v==='bigint')v=v.toString();if(typeof v!=='string'||!/^\d{1,78}$/.test(v)||BigInt(v)>=2n**256n)throw new Error('Invalid Morpho uint256');return BigInt(v)}
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
// Adapter into the shared USD display/budget model. Health remains protocol-native.
export function morphoPositionMetrics(p,shocks={},actions=[]){
  const collateral=p.reserves.find(r=>r.asset.toLowerCase()===p.collateralToken.toLowerCase()),loan=p.reserves.find(r=>r.asset.toLowerCase()===p.loanToken.toLowerCase());
  if(!collateral||!loan)throw new Error('Missing Morpho reserve');
  let market={...p.market},position={...p.morphoPosition};
  for(const a of actions.filter(a=>a.positionId===p.id)){
    const amount=uint(a.amountRaw),isLoan=a.asset.toLowerCase()===p.loanToken.toLowerCase(),isCollateral=a.asset.toLowerCase()===p.collateralToken.toLowerCase();
    if(!amount)throw new Error('Zero Morpho action');
    if(a.kind==='repay'&&isLoan){
      const prepared=a.sharesRaw?morphoRepayShares(market,position,a.sharesRaw):morphoRepaymentForBudget(market,position,a.amountRaw);
      if(!prepared||uint(prepared.assetsRaw)!==amount)throw new Error('Morpho repayment amount/share mismatch');
      market=prepared.market;position=prepared.position;
    }else if(a.kind==='borrow'&&isLoan){
      const shares=mulDiv(amount,u128(market.totalBorrowSharesRaw)+VIRTUAL_SHARES,u128(market.totalBorrowAssetsRaw)+1n,true);
      market.totalBorrowSharesRaw=u128(u128(market.totalBorrowSharesRaw)+shares).toString();market.totalBorrowAssetsRaw=u128(u128(market.totalBorrowAssetsRaw)+amount).toString();
      position.borrowSharesRaw=u128(u128(position.borrowSharesRaw)+shares).toString();
    }else if(a.kind==='supply'&&isCollateral){position.collateralRaw=u128(u128(position.collateralRaw)+amount).toString();}
    else if(a.kind==='withdraw'&&isCollateral){const owned=u128(position.collateralRaw);if(amount>owned)throw new Error('Withdrawal exceeds Morpho collateral');position.collateralRaw=(owned-amount).toString();}
    else throw new Error('Unsupported Morpho action asset');
  }
  const cShock=shocks[collateral.asset.toLowerCase()]??0,lShock=shocks[loan.asset.toLowerCase()]??0;
  const price=shockMorphoOracle(p.oraclePriceRaw,cShock,lShock),risk=morphoRisk(market,position,price,p.lltvRaw);
  const cUnit=10n**BigInt(collateral.decimals),lUnit=10n**BigInt(loan.decimals),usd=10n**8n;
  const cPrice=uint(collateral.priceRaw)*BigInt(10000+cShock)/10000n,lPrice=uint(loan.priceRaw)*BigInt(10000+lShock)/10000n;
  const debt=uint(risk.borrowAssetsRaw)*lPrice;
  return {collateralRaw:(uint(position.collateralRaw)*cPrice/cUnit).toString(),debtRaw:((debt+lUnit-1n)/lUnit).toString(),adjustedRaw:(uint(risk.maxBorrowAssetsRaw)*lPrice/lUnit).toString(),healthFactorRaw:risk.healthFactorRaw,liquidatable:risk.liquidatable,borrowAssetsRaw:risk.borrowAssetsRaw,oraclePriceRaw:price,healthBasis:'MORPHO_NATIVE_LOAN_UNITS',valuationUnit:usd.toString()};
}
