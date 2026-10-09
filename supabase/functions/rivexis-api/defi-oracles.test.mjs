import test from 'node:test';import assert from 'node:assert/strict';
import {WBTC_ORACLE as o,validateWbtcOracle} from './defi-oracles.mjs';
import {readFileSync} from 'node:fs';import {metrics} from './defi-model.mjs';
// Independently captured same-block production evidence, block 26155556.
const fixture=()=>({source:o.source,codeHash:o.codeHash,baseFeed:o.baseFeed,ratioFeed:o.ratioFeed,baseDecimals:8,ratioDecimals:8,decimals:8,denominator:10000000000000000n,blockTimestamp:1791557363n,price:8286613348460n,baseRound:[36893488147419121564n,8298322530501n,1791555441n,1791555455n,36893488147419121564n],ratioRound:[36893488147419104056n,99858897n,1791494505n,1791494519n,36893488147419104056n]});
test('WBTC composite reconciles integer price and both component timestamps',()=>{
  assert.equal(validateWbtcOracle(fixture()),true);
  const e=fixture();e.price++;assert.equal(validateWbtcOracle(e),false);
  e.price=8298322530501n;assert.equal(validateWbtcOracle(e),false); // Never treat WBTC as BTC at 1:1.
});
test('WBTC adapter, bytecode, feed identity and units must be pinned',()=>{
  for(const [key,value] of Object.entries({source:'0x'+'0'.repeat(40),codeHash:'0x'+'0'.repeat(64),baseFeed:o.ratioFeed,ratioFeed:o.baseFeed,baseDecimals:18,ratioDecimals:18,decimals:18,denominator:10n**18n}))assert.equal(validateWbtcOracle({...fixture(),[key]:value}),false,key);
});
test('each WBTC component fails closed for stale, future or invalid rounds',()=>{
  for(const kind of ['baseRound','ratioRound'])for(const issue of ['missing','negative','zeroRound','incomplete','stale','future','startAfterUpdate']){
    const e=fixture();if(issue==='missing')e[kind]=null;else{
      const r=e[kind];if(issue==='negative')r[1]=-1n;
      if(issue==='zeroRound')r[0]=0n;if(issue==='incomplete')r[4]=r[0]-1n;
      if(issue==='stale'){r[3]=e.blockTimestamp-BigInt(kind==='baseRound'?o.baseMaxAge:o.ratioMaxAge)-1n;r[2]=r[3]-1n;}
      if(issue==='future')r[3]=e.blockTimestamp+1n;if(issue==='startAfterUpdate')r[2]=r[3]+1n;
    }assert.equal(validateWbtcOracle(e),false,kind+':'+issue);
  }
});
test('WBTC freshness boundaries are inclusive without extending either feed allowance',()=>{
  const e=fixture();e.baseRound[3]=e.blockTimestamp-BigInt(o.baseMaxAge);e.baseRound[2]=e.baseRound[3];e.ratioRound[3]=e.blockTimestamp-BigInt(o.ratioMaxAge);e.ratioRound[2]=e.ratioRound[3];assert.equal(validateWbtcOracle(e),true);
});
test('mixed WETH/WBTC/USDC/USDT live accounting agrees with independent Pool totals',()=>{
  const s=JSON.parse(readFileSync(new URL('../../../certification-reports/wbtc-reference-snapshot.json',import.meta.url),'utf8'));
  const m=metrics(s.positions[0]);assert.equal(m.collateralRaw,s.observedCollateralRaw);assert.equal(m.debtRaw,s.observedDebtRaw);assert.equal(m.healthFactorRaw,s.observedHealthFactorRaw);
  const r=s.positions[0].reserves.find(r=>r.symbol==='WBTC'),[base,ratio]=r.oracleComponents;
  assert.equal(BigInt(base.answerRaw)*BigInt(ratio.answerRaw)/100000000n,BigInt(r.priceRaw));
  assert.equal(metrics(s.positions[0],{[r.asset.toLowerCase()]:-2000}).liquidatable,true);
});
