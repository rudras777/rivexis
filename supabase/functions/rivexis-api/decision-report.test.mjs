import test from "node:test";
import assert from "node:assert/strict";
import {analyzeCanonicalDecision,decisionReportHtml,decisionReportLines} from "./decision-report.mjs";

function result(overrides={}){
  return {
    analysis_id:crypto.randomUUID(),engine_id:"B1",engine_version:"1.3.0",analysis_framework_version:"b1-live-1.8.0",
    status:"COMPLETED",risk_score:20,data_confidence:80,engine_confidence:80,demo:false,evidence:[],provider_conflicts:[],hard_blockers:[],warnings:[],mitigations:[],assumptions:[],missing_data:[],
    ...overrides,
  };
}

test("canonical unavailable analyses remain UNKNOWN and preserve provenance",()=>{
  const input=result({status:"UNKNOWN",risk_score:null,data_confidence:0,engine_confidence:0,missing_data:["verified live provider evidence"]});
  const decision=analyzeCanonicalDecision([input]);
  assert.equal(decision.decision,"UNKNOWN");
  assert.equal(decision.canonical_persistence_verified,true);
  assert.deepEqual(decision.analysis_ids,[input.analysis_id]);
  assert.deepEqual(decision.missing_data,["verified live provider evidence"]);
  assert.equal(decision.evidence_count,0);
});

test("shared deterministic thresholds match the FastAPI decision contract",()=>{
  const b1=result({engine_id:"B1",risk_score:30});
  const f2=result({engine_id:"F2",engine_version:"1.2.0",analysis_framework_version:"f2-live-1.4.0",risk_score:60});
  const decision=analyzeCanonicalDecision([b1,f2]);
  assert.equal(decision.decision,"MODIFY");
  assert.equal(decision.overall_risk_score,45);
  assert.equal(decision.decision_confidence,80);
  assert.equal(decision.data_confidence,80);
  assert.equal(decision.decision_methodology_version,"1.1.0");
  assert.equal(decision.canonical_persistence_verified,true);
});

test("duplicate engine references do not silently overweight a specialist engine",()=>{
  const first=result({engine_id:"B1"});
  const second=result({engine_id:"B1",analysis_id:crypto.randomUUID(),risk_score:90});
  const decision=analyzeCanonicalDecision([first,second]);
  assert.equal(decision.decision,"UNKNOWN");
  assert.match(decision.executive_summary,/duplicate analytical references/i);
});

test("decision reports preserve demo labeling, provenance and escape HTML",()=>{
  const analysis=result({demo:true,evidence:[{provider:"Rivexis Demo Adapter"}],warnings:["<script>alert(1)</script>"]});
  const decision=analyzeCanonicalDecision([analysis]);
  const html=decisionReportHtml(decision);
  assert.match(html,/DEMONSTRATION RESULT - NOT LIVE DATA/);
  assert.match(html,/VERIFIED FROM PERSISTED ANALYSES/);
  assert.match(html,/Rivexis Demo Adapter/);
  assert.doesNotMatch(html,/<script>alert/);
  assert.match(html,/&lt;script&gt;alert\(1\)&lt;\/script&gt;/);
  const lines=decisionReportLines(decision);
  assert.ok(lines.some(line=>line==="Demo: YES - SYNTHETIC"));
  assert.ok(lines.some(line=>line.includes(analysis.analysis_id)));
});
