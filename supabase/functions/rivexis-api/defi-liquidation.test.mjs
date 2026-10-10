import test from 'node:test';import assert from 'node:assert/strict';import {readFileSync} from 'node:fs';
import {sampleSnapshot} from './defi-sample.mjs';import {liquidationAnalysis} from './defi-liquidation.mjs';import {metrics} from './defi-model.mjs';import {morphoRisk} from './defi-morpho-model.mjs';
test('independent single-collateral boundary is $2250 with 25% distance and adjacent oracle-unit eligibility',()=>{
 const s=sampleSnapshot(0),r=liquidationAnalysis(s,{},0).rows[0];assert.equal(r.minimumHealthyPriceRaw,'225000000000');assert.equal(r.distanceBps,'2500');
 const p=structuredClone(s.positions[0]);p.reserves[0].priceRaw=r.minimumHealthyPriceRaw;assert.equal(metrics(p).liquidatable,false);p.reserves[0].priceRaw=r.firstLiquidatablePriceRaw;assert.equal(metrics(p).liquidatable,true);
});
test('multi-collateral price trigger holds other collateral fixed instead of assigning all debt to every asset',()=>{
 const s=sampleSnapshot(0);s.positions[0].reserves.push({...s.positions[0].reserves[0],asset:'0x'+'2'.repeat(40),symbol:'OTHER',collateralRaw:'5000000000000000000'});
 const a=liquidationAnalysis(s,{},0);assert.equal(a.rows[0].minimumHealthyPriceRaw,'75000000000');assert.equal(a.rows[1].state,'NO_DOWNWARD_TRIGGER');assert.equal(a.exposures[0].collateralBps,'6666');assert.equal(a.exposures[1].debtBps,'10000');
});
test('collateral and debt shocks update trigger and negative distance for an already liquidatable position',()=>{
 const s=sampleSnapshot(0),[c,d]=s.positions[0].reserves;
 const r=liquidationAnalysis(s,{[c.asset.toLowerCase()]:-3000,[d.asset.toLowerCase()]:1000},0).rows[0];assert.equal(r.minimumHealthyPriceRaw,'247500000000');assert.equal(r.distanceBps,'-1785');assert.equal(r.liquidatable,true);
});
test('same-token debt, debt-free and empty positions have explicit non-fabricated states',()=>{
 const s=sampleSnapshot(0);s.positions[0].reserves[0].debtRaw='100000000000000000';assert.equal(liquidationAnalysis(s,{},0).rows[0].state,'SAME_ASSET_DEBT_UNVALIDATED');
 s.positions[0].reserves.forEach(r=>r.debtRaw='0');assert.equal(liquidationAnalysis(s,{},0).rows[0].state,'NO_DEBT');s.positions=[];assert.equal(liquidationAnalysis(s,{},0).closest,null);
});
test('stale, missing price, unsupported protocol and unknown shock reject before boundary output',()=>{
 const s=sampleSnapshot(0);assert.throws(()=>liquidationAnalysis(s,{},181000),/stale/);assert.throws(()=>liquidationAnalysis(s,{['0x'+'9'.repeat(40)]:1},0),/Unknown/);
 s.positions[0].reserves[0].priceRaw='0';assert.throws(()=>liquidationAnalysis(s,{},0));s.positions[0].protocol='Unknown';assert.throws(()=>liquidationAnalysis(s,{},0));
});
test('real pinned Morpho native-unit boundary survives both floor inversions and does not net unrelated collateral',()=>{
 const s=JSON.parse(readFileSync(new URL('../../../certification-reports/morpho-portfolio-reference.json',import.meta.url))).snapshot;
 const a=liquidationAnalysis(s,{},s.blockTimestamp*1000),p=s.positions.find(p=>p.protocol==='Morpho Blue'),r=a.rows.find(r=>r.protocol==='Morpho Blue');
 assert.equal(morphoRisk(p.market,p.morphoPosition,r.oracleBoundaryRaw,p.lltvRaw).liquidatable,false);assert.equal(morphoRisk(p.market,p.morphoPosition,r.firstLiquidatableOracleRaw,p.lltvRaw).liquidatable,true);
 const q=structuredClone(s);q.positions.find(p=>p.protocol==='Aave V3').reserves[0].collateralRaw='999999999999999999999999';assert.equal(liquidationAnalysis(q,{},q.blockTimestamp*1000).rows.find(r=>r.protocol==='Morpho Blue').oracleBoundaryRaw,r.oracleBoundaryRaw);
});
