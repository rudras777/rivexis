import assert from "node:assert/strict";
import test from "node:test";
import {analysisResult} from "./analysis.mjs";

const scenarios={
  B1:{input:{will_revert:false,unlimited_approval:true},score:45},
  B2:{input:{unlimited_approval:true},score:35},
  B3:{input:{active_exploit:true},score:80},
  B4:{input:{label_conflict:true},score:35,status:"CONFLICTING_DATA"},
  B5:{input:{route_risk:48,low_liquidity:true},score:63},
  F1:{input:{largest_exposure_pct:62},score:62},
  F2:{input:{admin_privilege:true,oracle_risk:true},score:50},
  F3:{input:{health_factor:1.12},score:75},
  F4:{input:{apy:42,incentive_dependent:true},score:75},
  F5:{input:{largest_allocation_pct:72,stablecoin_depeg_scenario_loss_pct:25},score:100},
};

for(const [engineId,scenario] of Object.entries(scenarios)){
  test(`${engineId} produces attributed deterministic demonstration output`,()=>{
    const result=analysisResult(engineId,true,scenario.input);
    assert.equal(result.demo,true);
    assert.equal(result.risk_score,scenario.score);
    assert.equal(result.status,scenario.status??"COMPLETED");
    assert.equal(result.evidence.length,1);
    assert.equal(result.evidence[0].provider,"Rivexis Demo Adapter");
    assert.equal(result.evidence[0].freshness,"CURRENT");
    assert.equal(result.evidence[0].engine_version,result.engine_version);
    assert.match(result.summary,/Demonstration result for .+ Engine: detected synthetic risk score/);
  });
}

test("live execution remains UNKNOWN without verified provider evidence",()=>{
  const result=analysisResult("B2",false,{known_malicious:true});
  assert.equal(result.demo,false);
  assert.equal(result.status,"UNKNOWN");
  assert.equal(result.risk_score,null);
  assert.equal(result.evidence.length,0);
  assert.deepEqual(result.hard_blockers,["NO_VERIFIED_PROVIDER_EVIDENCE"]);
});

test("malformed demonstration numerics cannot create NaN or infinite scores",()=>{
  for(const input of [{route_risk:"100"},{route_risk:null},{route_risk:Infinity},{route_risk:NaN}]){
    const result=analysisResult("B5",true,input);
    assert.equal(Number.isFinite(result.risk_score),true);
    assert.equal(result.risk_score,25);
  }
});

test("explicit demo security and price conflicts remain first-class",()=>{
  const blocked=analysisResult("B2",true,{known_malicious:true,price_conflict_pct:8});
  assert.equal(blocked.risk_score,85);
  assert.equal(blocked.severity,"critical");
  assert.equal(blocked.status,"CONFLICTING_DATA");
  assert.equal(blocked.hard_blockers.length,1);
  assert.equal(blocked.provider_conflicts[0].metric,"reference_price");
});
