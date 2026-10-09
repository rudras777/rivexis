import test from 'node:test';import assert from 'node:assert/strict';
import {compoundedRate,accrueMorphoMarket,morphoBorrowAssets,morphoRisk,morphoRepayShares,morphoRepaymentForBudget,shockMorphoOracle,morphoWithdrawalLimit} from './defi-morpho-model.mjs';
const market=()=>({totalSupplyAssetsRaw:'1000',totalSupplySharesRaw:'1000000000',totalBorrowAssetsRaw:'500',totalBorrowSharesRaw:'500000000',lastUpdateRaw:'100',feeRaw:'100000000000000000'});
test('Morpho uses three integer Taylor terms and rounds accrued interest and fees down',()=>{
  assert.equal(compoundedRate('10000000000000000','2'),20201333333333333n);
  const m=accrueMorphoMarket(market(),'10000000000000000','102');
  assert.equal(m.interestRaw,'10');assert.equal(m.totalBorrowAssetsRaw,'510');assert.equal(m.totalSupplyAssetsRaw,'1010');assert.equal(m.feeSharesRaw,'991089');assert.equal(m.totalSupplySharesRaw,'1000991089');assert.equal(m.totalBorrowSharesRaw,'500000000');
  assert.equal(morphoBorrowAssets(m,'100000000'),102n);
});
test('zero elapsed, zero rate, zero borrow and zero IRM accrue no interest',()=>{
  assert.equal(accrueMorphoMarket(market(),'10000000000000000','100').interestRaw,'0');
  assert.equal(accrueMorphoMarket(market(),'0','102').interestRaw,'0');
  assert.equal(accrueMorphoMarket({...market(),totalBorrowAssetsRaw:'0'},'10000000000000000','102').interestRaw,'0');
  assert.equal(accrueMorphoMarket(market(),'10000000000000000','102',true).interestRaw,'0');
});
test('virtual assets/shares and ceiling debt avoid the legacy fractional-debt error',()=>{
  const m={...market(),totalBorrowAssetsRaw:'1',totalBorrowSharesRaw:'3'},p={borrowSharesRaw:'1',collateralRaw:'100'};
  assert.equal(morphoBorrowAssets(m,'1'),1n);
  const a=morphoRepaymentForBudget(m,p,'1');assert.equal(a.assetsRaw,'1');assert.equal(a.sharesRaw,'1');assert.equal(a.borrowAssetsAfterRaw,'0');assert.equal(a.market.totalBorrowAssetsRaw,'0');
  assert.throws(()=>morphoRepayShares(m,p,'2'));
});
test('Morpho liquidation boundary uses native loan units and two separate floors',()=>{
  const m={...market(),totalBorrowAssetsRaw:'1000000000',totalBorrowSharesRaw:'1000000000000000'},p={borrowSharesRaw:m.totalBorrowSharesRaw,collateralRaw:'1000000000000000000'};
  const r=morphoRisk(m,p,'2000000000000000000000000000','860000000000000000');
  assert.equal(r.collateralInLoanRaw,'2000000000');assert.equal(r.maxBorrowAssetsRaw,'1720000000');assert.equal(r.healthFactorRaw,'1720000000000000000');assert.equal(r.healthy,true);
  const b={...m,totalBorrowAssetsRaw:'1720000000',totalBorrowSharesRaw:'1720000000000000'};p.borrowSharesRaw=b.totalBorrowSharesRaw;
  assert.equal(morphoRisk(b,p,'2000000000000000000000000000','860000000000000000').healthy,true);
  b.totalBorrowAssetsRaw='1720000001';assert.equal(morphoRisk(b,p,'2000000000000000000000000000','860000000000000000').liquidatable,true);
});
test('repayment recomputes remaining debt from updated market and position shares',()=>{
  const m=market(),p={borrowSharesRaw:'100000000',collateralRaw:'999'};
  const a=morphoRepaymentForBudget(m,p,'20');assert.ok(BigInt(a.assetsRaw)<=20n);assert.ok(BigInt(a.borrowAssetsAfterRaw)<morphoBorrowAssets(m,p.borrowSharesRaw));assert.equal(a.position.collateralRaw,'999');
  assert.equal(morphoRepaymentForBudget(m,p,'0'),null);assert.equal(morphoRepaymentForBudget(m,p,'10000').borrowAssetsAfterRaw,'0');
});
test('inverse liquidation math distinguishes adjacent collateral base units',()=>{
  const m=market(),p={borrowSharesRaw:'100000000',collateralRaw:'1000'},price=(10n**36n).toString(),lltv='860000000000000000';
  const limit=BigInt(morphoWithdrawalLimit(m,p,price,lltv));assert.equal(limit,883n);
  assert.equal(morphoRisk(m,{...p,collateralRaw:(1000n-limit).toString()},price,lltv).healthy,true);
  assert.equal(morphoRisk(m,{...p,collateralRaw:(999n-limit).toString()},price,lltv).healthy,false);
});
test('collateral and debt-token shocks affect the relative oracle rather than nominal debt',()=>{
  assert.equal(shockMorphoOracle('3000',-2000,1000),'2181');assert.equal(shockMorphoOracle('3000',0,-500),'3157');assert.throws(()=>shockMorphoOracle('3000',-10000));
});
test('malformed time, fee, share conservation and Solidity arithmetic overflow reject',()=>{
  assert.throws(()=>accrueMorphoMarket(market(),'1','99'));assert.throws(()=>accrueMorphoMarket({...market(),feeRaw:'250000000000000001'},'1','101'));
  assert.throws(()=>morphoBorrowAssets(market(),'500000001'));assert.throws(()=>compoundedRate((2n**255n).toString(),'2'));
  assert.throws(()=>morphoRisk(market(),{borrowSharesRaw:'1',collateralRaw:(2n**128n).toString()},'1','1'));
});
