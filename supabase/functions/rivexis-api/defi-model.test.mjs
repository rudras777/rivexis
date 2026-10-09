import test from 'node:test';
import assert from 'node:assert/strict';
import {sampleSnapshot} from './defi-sample.mjs';
import {metrics,scenario,frontier,decimal,validateSnapshot,WAD} from './defi-model.mjs';
const now=1791550000000;
const state=()=>sampleSnapshot(now);
test('independent single-collateral reference: 10 ETH × $3000 × 80% / $18000',()=>{
  assert.equal(metrics(state().positions[0]).healthFactorRaw,'1333333333333333333');
});
test('ETH -20% reference: 24000 × 80% / 18000, debt stable',()=>{
  const s=state(),r=scenario(s,{[s.positions[0].reserves[0].asset.toLowerCase()]:-2000},[],now)[0];
  assert.equal(r.healthFactorRaw,'1066666666666666666');assert.equal(r.collateralRaw,'2400000000000');
});
test('simultaneous collateral -30% and debt +10% crosses liquidation threshold',()=>{
  const s=state(),[eth,usdc]=s.positions[0].reserves;
  const r=scenario(s,{[eth.asset.toLowerCase()]:-3000,[usdc.asset.toLowerCase()]:1000},[],now)[0];
  assert.equal(r.debtRaw,'1980000000000');assert.equal(r.healthFactorRaw,'848484848484848484');assert.equal(r.liquidatable,true);
});
test('mixed thresholds use weighted numerator without averaged threshold truncation',()=>{
  const p=state().positions[0];p.reserves[0].collateralRaw='1000000000000000001';
  p.reserves[1].collateralRaw='1000000001';p.reserves[1].collateralEnabled=true;p.reserves[1].ltBps='7800';
  // Independent rational reference: each collateral floors to USD base; debt ceils.
  const expected=((300000000000n*8000n+100000000100n*7800n)*WAD+900000000000n)/1800000000000n/10000n;
  assert.equal(metrics(p).healthFactorRaw,expected.toString());
});
test('debt valuation rounds up below one price unit',()=>{
  const p=state().positions[0];p.reserves[1].debtRaw='1';p.reserves[1].priceRaw='100000001';
  assert.equal(metrics(p).debtRaw,'101');
});
test('repayment and collateral additions have distinct independently checked effects',()=>{
  const p=state().positions[0], [eth,usdc]=p.reserves;
  assert.equal(metrics(p,{},[{positionId:p.id,asset:usdc.asset,kind:'repay',amountRaw:'2000000000'}]).healthFactorRaw,'1500000000000000000');
  assert.equal(metrics(p,{},[{positionId:p.id,asset:eth.asset,kind:'supply',amountRaw:'1000000000000000000'}]).healthFactorRaw,'1466666666666666666');
});
test('zero debt has no finite HF; over-repayment and over-withdrawal reject',()=>{
  const p=state().positions[0];assert.throws(()=>metrics(p,{},[{positionId:p.id,asset:p.reserves[1].asset,kind:'repay',amountRaw:'18000000001'}]));
  p.reserves[1].debtRaw='0';assert.equal(metrics(p).healthFactorRaw,null);
  assert.throws(()=>metrics(p,{},[{positionId:p.id,asset:p.reserves[0].asset,kind:'withdraw',amountRaw:'11000000000000000000'}]));
});
test('stale, malformed, unvalidated oracle, eMode and isolation snapshots fail closed',()=>{
  assert.throws(()=>validateSnapshot(state(),now+181000),/stale/);
  for(const mutate of [s=>s.positions[0].eMode=1,s=>s.positions[0].reserves[0].oracleState='UNVALIDATED',s=>s.positions[0].reserves[0].priceRaw='0',s=>s.positions[0].reserves[0].isolation=true,s=>s.positions[0].reserves[0].debtRaw='NaN']){
    const s=state();mutate(s);assert.throws(()=>scenario(s,{},[],now));
  }
});
test('precision exceeds JS safe integer range and decimal parsing rejects unsafe forms',()=>{
  assert.equal(decimal('123456789012345678.12345678'),12345678901234567812345678n);
  for(const v of ['1e9','NaN','Infinity','-1','0x10','1.123456789'])assert.throws(()=>decimal(v));
});
test('frontier enforces budget, fee reserve and actual shared token balances',()=>{
  const s=state();const r=frontier(s,{budget:'3000',gasReserve:'25',target:'1.5'},now);
  assert.equal(r.meetsTarget,true);assert.ok(r.alternatives.length>0);
  for(const a of r.alternatives){assert.ok(BigInt(a.totalBudgetRaw)<=3000n*100000000n);assert.equal(a.feasibility,'MODELED_ONLY');
    for(const action of a.actions){const reserve=s.positions[0].reserves.find(r=>r.asset===action.asset);assert.ok(BigInt(action.amountRaw)<=BigInt(reserve.walletRaw));}
  }
});
test('zero capital, empty wallets and insufficient budget report no target solution',()=>{
  assert.equal(frontier(state(),{budget:'0',gasReserve:'0',target:'2'},now).alternatives.length,0);
  assert.equal(frontier(state(),{budget:'10',gasReserve:'0',target:'2'},now).meetsTarget,false);
  const s=state();s.positions[0].reserves.forEach(r=>r.walletRaw='0');assert.equal(frontier(s,{budget:'100000',target:'2'},now).alternatives.length,0);
  assert.throws(()=>frontier(state(),{budget:'10',gasReserve:'11'},now));
});
test('two independent positions are not netted; allocation across both improves minimum HF',()=>{
  const s=state(),second=structuredClone(s.positions[0]);second.id='second-aave-fixture';second.reserves[0].collateralRaw='8000000000000000000';s.positions.push(second);
  const r=frontier(s,{budget:'5000',gasReserve:'0',target:'1.3',objective:'max-min'},now);
  assert.equal(r.baseline.length,2);assert.notEqual(r.baseline[0].healthFactorRaw,r.baseline[1].healthFactorRaw);
  assert.ok(r.alternatives.some(a=>new Set(a.actions.map(x=>x.positionId)).size===2));
  for(const a of r.alternatives){for(const token of s.positions[0].reserves){const spent=a.actions.filter(x=>x.asset===token.asset).reduce((n,a)=>n+BigInt(a.amountRaw),0n);assert.ok(spent<=BigInt(token.walletRaw));}}
});
test('invalid shocks, unsupported assets and impossible targets cannot become results',()=>{
  const s=state();assert.throws(()=>scenario(s,{[s.positions[0].reserves[0].asset.toLowerCase()]:-10000},[],now));
  assert.throws(()=>frontier(s,{budget:'100',target:'0.9'},now));
  assert.throws(()=>scenario(s,{['0x'+'1'.repeat(40)]:100},[],now));
});
test('insufficient native ETH withholds fee-constrained candidates',()=>{
  const s=state();s.nativeBalanceRaw='0';const result=frontier(s,{budget:'3000',gasReserve:'25'},now);
  assert.equal(result.gasConstraint,'INSUFFICIENT_NATIVE_GAS_RESERVE');assert.equal(result.alternatives.length,0);
});
test('zero-cost no-action baseline wins when the scenario target is already met',()=>{
  const s=state();const result=frontier(s,{budget:'3000',gasReserve:'25',target:'1.2'},now);
  assert.equal(result.alternatives[0].totalBudgetRaw,'0');assert.deepEqual(result.alternatives[0].actions,[]);assert.equal(result.alternatives[0].execution,'NO_TRANSACTION');
  s.nativeBalanceRaw='0';const noGas=frontier(s,{budget:'3000',gasReserve:'25',target:'1.2'},now);
  assert.equal(noGas.alternatives.length,1);assert.equal(noGas.alternatives[0].totalBudgetRaw,'0');
});
