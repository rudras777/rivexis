import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {MORPHO_WBTC,validateMorphoWbtcOracle} from './defi-morpho-oracle.mjs';
import {accrueMorphoMarket,morphoRisk,morphoWithdrawalLimit} from './defi-morpho-model.mjs';
const oracle=JSON.parse(readFileSync(new URL('../../../certification-reports/morpho-oracle-reference.json',import.meta.url)));
const accrual=JSON.parse(readFileSync(new URL('../../../certification-reports/morpho-accrual-reference.json',import.meta.url)));
function evidence(){const e=structuredClone(oracle.evidence);for(const k of ['vaultConversionSample','scaleFactor','price','blockTimestamp'])e[k]=BigInt(e[k]);for(const f of e.feeds)f.round=f.round.map(BigInt);return e;}
test('real pinned Morpho V1 oracle agrees exactly with independent same-block components',()=>{
  const e=evidence();assert.equal(validateMorphoWbtcOracle(e),true);
  assert.equal(e.price,e.scaleFactor*e.feeds[0].round[1]*e.feeds[1].round[1]/e.feeds[2].round[1]);
});
test('all Morpho component feeds reject stale, future, negative, incomplete and bad rounds',()=>{
  for(let i=0;i<3;i++)for(const mutate of [
    (f,e)=>{f.round[3]=e.blockTimestamp-BigInt(MORPHO_WBTC.feeds[i].maxAge)-1n;f.round[2]=f.round[3];},
    (f,e)=>{f.round[3]=e.blockTimestamp+1n;},f=>{f.round[1]=-1n;},f=>{f.round[1]=0n;},
    f=>{f.round[4]=f.round[0]-1n;},f=>{f.round.pop();},f=>{f.round[2]=f.round[3]+1n;},
  ]){const e=evidence();mutate(e.feeds[i],e);assert.equal(validateMorphoWbtcOracle(e),false);}
});
test('Morpho market, units, vault and feed identities cannot be silently substituted',()=>{
  for(const k of ['marketId','loanToken','collateralToken','oracle','irm','vault','quoteFeed2']){const e=evidence();e[k]='0x1111111111111111111111111111111111111111';assert.equal(validateMorphoWbtcOracle(e),false);}
  for(const [k,v] of [['codeHash','0x00'],['lltvRaw','850000000000000000'],['scaleFactor',10n**27n],['vaultConversionSample',2n],['loanDecimals',18],['collateralDecimals',18],['price',evidence().price+1n]]){const e=evidence();e[k]=v;assert.equal(validateMorphoWbtcOracle(e),false);}
  for(let i=0;i<3;i++){const e=evidence();e.feeds[i].decimals=18;assert.equal(validateMorphoWbtcOracle(e),false);e.feeds[i].decimals=8;e.feeds[i].address=e.feeds[(i+1)%3].address;assert.equal(validateMorphoWbtcOracle(e),false);}
  assert.equal(validateMorphoWbtcOracle(null),false);
});
test('Morpho integer accrual matches all captured actual EVM market states',()=>{
  const cases=accrual.results.filter(r=>r.status==='ACCRUAL_REFERENCE_PASS');assert.ok(cases.length>=6);
  const fields=['totalSupplyAssetsRaw','totalSupplySharesRaw','totalBorrowAssetsRaw','totalBorrowSharesRaw','lastUpdateRaw','feeRaw'];
  for(const r of cases){const model=accrueMorphoMarket(r.stored,r.rateRaw,accrual.blockTimestamp);for(const key of fields)assert.equal(model[key],r.reference[key]);}
});
test('actual EVM WBTC withdrawal boundary matches adjacent-unit model health',()=>{
  const r=accrual.results.find(r=>r.id===MORPHO_WBTC.marketId);assert.ok(r?.boundary);
  assert.equal(r.boundary.healthyCall,'SUCCEEDED');assert.equal(r.boundary.nextUnitCall,'REVERTED_INSUFFICIENT_COLLATERAL');
  const maximum=morphoWithdrawalLimit(r.modeled,r.position,r.oraclePriceRaw,r.params[4]);assert.equal(maximum,r.boundary.maximumWithdrawRaw);
  const left=BigInt(r.position.collateralRaw)-BigInt(maximum);
  assert.equal(morphoRisk(r.modeled,{...r.position,collateralRaw:left.toString()},r.oraclePriceRaw,r.params[4]).healthy,true);
  assert.equal(morphoRisk(r.modeled,{...r.position,collateralRaw:(left-1n).toString()},r.oraclePriceRaw,r.params[4]).healthy,false);
});
