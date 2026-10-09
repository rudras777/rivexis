import test from 'node:test';import assert from 'node:assert/strict';import {readFileSync} from 'node:fs';
import {validateSnapshot,metrics,scenario,frontier} from './defi-unified-model.mjs';
import {morphoRepayShares} from './defi-morpho-model.mjs';
const real=JSON.parse(readFileSync(new URL('../../../certification-reports/morpho-portfolio-reference.json',import.meta.url)));
const now=real.snapshot.blockTimestamp*1000;
test('same-block real Aave/Morpho reference retains independent protocol health and transaction effects',()=>{
  const s=structuredClone(real.snapshot);validateSnapshot(s,now);assert.equal(s.positions.length,2);
  const base=scenario(s,{},[],now),shock=scenario(s,real.constraints.shocks,[],now);
  assert.equal(base[0].healthFactorRaw,shock[0].healthFactorRaw);assert.ok(BigInt(shock[1].healthFactorRaw)<BigInt(base[1].healthFactorRaw));
  assert.equal(real.transaction.simulation,'SUCCEEDED_AT_BLOCK');assert.equal(real.transaction.positionEffects.length,2);
});
function hypothetical(){
  const s=structuredClone(real.snapshot);s.sample=true;s.nativeBalanceRaw='100000000000000000000';
  const a=s.positions.find(p=>p.protocol==='Aave V3'),m=s.positions.find(p=>p.protocol==='Morpho Blue'),loan=structuredClone(m.reserves.find(r=>r.symbol==='USDC'));
  loan.debtRaw='25000000000';a.reserves.push(loan);a.reserves[0].collateralRaw='10000000000000000000';
  for(const p of s.positions)for(const r of p.reserves)r.walletRaw=r.symbol==='USDC'?'1000000000000':r.symbol==='WBTC'?'1000000000':'10000000000000000000';
  return s;
}
test('hypothetical multi-protocol frontier shares wallet capital and uses exact Morpho repayment shares',()=>{
  const s=hypothetical();validateSnapshot(s,now);
  const f=frontier(s,{budget:'1000000',gasReserve:'10',target:'1.50',objective:'max-min'},now);assert.ok(f.alternatives.length>0);
  let morphoRepays=0;
  for(const a of f.alternatives){
    assert.ok(BigInt(a.totalBudgetRaw)<=1000000n*10n**8n);const balances=new Map();
    for(const action of a.actions){const p=s.positions.find(p=>p.id===action.positionId),r=p.reserves.find(r=>r.asset===action.asset);balances.set(r.asset,(balances.get(r.asset)??0n)+BigInt(action.amountRaw));assert.ok(balances.get(r.asset)<=BigInt(r.walletRaw));
      if(p.protocol==='Morpho Blue'&&action.kind==='repay'){morphoRepays++;assert.ok(action.sharesRaw);const exact=morphoRepayShares(p.market,p.morphoPosition,action.sharesRaw);assert.equal(exact.assetsRaw,action.amountRaw);assert.ok(BigInt(exact.borrowAssetsAfterRaw)<BigInt(r.debtRaw));}
    }
    assert.deepEqual(a.outcomes,scenario(s,{},a.actions,now));
  }
  assert.ok(morphoRepays>0);
});
test('cross-protocol mismatched wallet balance or budget price is rejected rather than double counted',()=>{
  for(const key of ['walletRaw','priceRaw']){const s=hypothetical();s.positions[0].reserves.find(r=>r.symbol==='USDC')[key]='1';assert.throws(()=>validateSnapshot(s,now),/mismatch/);}
});
test('Morpho scenario rejects asset/share mismatch and changed market evidence',()=>{
  const s=hypothetical(),p=s.positions[1],loan=p.reserves.find(r=>r.symbol==='USDC');
  assert.throws(()=>scenario(s,{},[{positionId:p.id,asset:loan.asset,kind:'repay',amountRaw:'2',sharesRaw:'1'}],now),/mismatch/);
  p.oracleEvidence.codeHash='0x00';assert.throws(()=>validateSnapshot(s,now),/Unvalidated/);
});
