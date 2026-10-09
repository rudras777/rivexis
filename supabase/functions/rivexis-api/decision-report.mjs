import {BRAND_REPORT_SVG} from "./brand.mjs";
const USABLE_STATUSES=new Set(["COMPLETED","PARTIAL","CONFLICTING_DATA","STALE_DATA"]);
const DECISION_METHODOLOGY_VERSION="1.1.0";

function finite(value,fallback=0){return typeof value==="number"&&Number.isFinite(value)?value:fallback}
function mean(values){return values.length?values.reduce((sum,value)=>sum+finite(value),0)/values.length:0}
function stringArray(value){return Array.isArray(value)?value.filter(item=>typeof item==="string"):[]}
function records(value){return Array.isArray(value)?value.filter(item=>item&&typeof item==="object"&&!Array.isArray(item)):[]}
function escapeHtml(value){return String(value??"").replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;").replaceAll("'","&#39;")}
function unique(values){return [...new Set(values)]}

function provenance(results){
  const engineVersions={};
  const engineStatuses={};
  const frameworks={};
  const evidenceSources=[];
  let unresolvedConflictCount=0;
  let evidenceCount=0;
  for(const result of results){
    const engineId=String(result.engine_id??"UNKNOWN");
    engineVersions[engineId]=String(result.engine_version??"UNKNOWN");
    engineStatuses[engineId]=String(result.status??"UNKNOWN");
    frameworks[engineId]=String(result.analysis_framework_version??"UNKNOWN");
    const evidence=records(result.evidence);
    evidenceCount+=evidence.length;
    for(const item of evidence){if(typeof item.provider==="string"&&item.provider.trim())evidenceSources.push(item.provider)}
    unresolvedConflictCount+=records(result.provider_conflicts).length;
  }
  return {
    analysis_ids:results.map(result=>String(result.analysis_id??"")),
    engine_versions:engineVersions,
    engine_statuses:engineStatuses,
    analysis_framework_versions:frameworks,
    evidence_sources:unique(evidenceSources).sort(),
    unresolved_conflict_count:unresolvedConflictCount,
    evidence_count:evidenceCount,
    canonical_persistence_verified:results.length>0,
    demo:results.some(result=>result.demo===true),
  };
}

function decisionBase(){
  return {decision_id:crypto.randomUUID(),timestamp:new Date().toISOString(),decision_methodology_version:DECISION_METHODOLOGY_VERSION};
}

function duplicateDecision(results,reason){
  return {
    ...decisionBase(),decision:"UNKNOWN",overall_risk_score:0,decision_confidence:0,data_confidence:Number(mean(results.map(result=>finite(result.data_confidence))).toFixed(2)),
    executive_summary:"Decision inputs contain duplicate analytical references and cannot be weighted safely.",critical_findings:[],positive_findings:[],risk_breakdown:{},
    why:[reason],what_could_go_wrong:[],recommended_action:"Use one unique persisted result per specialist engine before requesting a decision.",safer_option:null,
    assumptions:[],missing_data:["unique decision-grade specialist engine results"],...provenance(results),
  };
}

export function analyzeCanonicalDecision(resultsValue){
  const results=records(resultsValue);
  if(!results.length){
    return {...decisionBase(),decision:"UNKNOWN",overall_risk_score:0,decision_confidence:0,data_confidence:0,executive_summary:"No engine evidence was supplied.",critical_findings:[],positive_findings:[],risk_breakdown:{},why:[],what_could_go_wrong:[],recommended_action:"Collect required evidence before acting.",safer_option:null,assumptions:[],missing_data:["engine results"],analysis_ids:[],engine_versions:{},engine_statuses:{},analysis_framework_versions:{},evidence_sources:[],unresolved_conflict_count:0,evidence_count:0,canonical_persistence_verified:false,demo:false};
  }
  const analysisIds=results.map(result=>String(result.analysis_id??""));
  if(new Set(analysisIds).size!==analysisIds.length)return duplicateDecision(results,"The same persisted analysis_id was submitted more than once; repeated references are not additional evidence.");
  const engineIds=results.map(result=>String(result.engine_id??""));
  if(new Set(engineIds).size!==engineIds.length)return duplicateDecision(results,"Multiple results from the same specialist engine were supplied; the shared decision model does not silently overweight one engine.");

  const prov=provenance(results);
  const usable=results.filter(result=>USABLE_STATUSES.has(String(result.status??"UNKNOWN")));
  if(!usable.length){
    return {...decisionBase(),decision:"UNKNOWN",overall_risk_score:0,decision_confidence:0,data_confidence:Number(mean(results.map(result=>finite(result.data_confidence))).toFixed(2)),executive_summary:"Required evidence is insufficient to support a Rivexis decision.",critical_findings:[],positive_findings:[],risk_breakdown:{},why:["No submitted specialist result is in a decision-usable evidence state."],what_could_go_wrong:[],recommended_action:"Obtain fresh normalized provider evidence.",safer_option:null,assumptions:unique(results.flatMap(result=>stringArray(result.assumptions))).sort(),missing_data:unique(results.flatMap(result=>stringArray(result.missing_data))).sort(),...prov};
  }

  const hard=usable.flatMap(result=>stringArray(result.hard_blockers));
  const riskScores=usable.map(result=>finite(result.risk_score));
  const risk=hard.length?Math.max(...riskScores):mean(riskScores);
  const dataConf=mean(usable.map(result=>finite(result.data_confidence)));
  const engineConf=mean(usable.map(result=>finite(result.engine_confidence)));
  const conflicts=usable.reduce((sum,result)=>sum+records(result.provider_conflicts).length,0);
  const uncertain=results.filter(result=>String(result.status??"UNKNOWN")!=="COMPLETED");
  const decisionConf=Math.max(0,Math.min(100,(dataConf+engineConf)/2-conflicts*12-uncertain.length*10));
  let state;
  if(hard.length)state="AVOID";
  else if(dataConf<35)state="UNKNOWN";
  else if(uncertain.length)state="WAIT";
  else if(risk>=80)state="AVOID";
  else if(risk>=40)state="MODIFY";
  else state="PROCEED";

  const why=[`Aggregate materialized risk assessment is ${risk.toFixed(1)}/100 across ${usable.length} usable specialist result(s).`];
  if(hard.length)why.push(`${hard.length} hard blocker(s) override aggregate scoring.`);
  if(uncertain.length)why.push(`Decision-grade evidence is incomplete or unresolved: ${uncertain.map(result=>`${String(result.engine_id??"UNKNOWN")}=${String(result.status??"UNKNOWN")}`).join(", ")}.`);
  if(conflicts)why.push(`${conflicts} unresolved source conflict(s) reduce decision confidence.`);
  if(dataConf<60)why.push("Data confidence is below the preferred institutional threshold.");
  const actions={PROCEED:"Proceed subject to the stated assumptions and current evidence.",MODIFY:"Modify the exposure or transaction to reduce identified material risks.",WAIT:"Wait until partial, stale, unavailable, or conflicting evidence is resolved.",AVOID:"Avoid the proposed action while material blockers remain.",UNKNOWN:"Do not act on this analysis; evidence is insufficient."};
  const mitigations=usable.flatMap(result=>stringArray(result.mitigations));
  const warnings=usable.flatMap(result=>stringArray(result.warnings));
  const positives=usable.filter(result=>String(result.status)==="COMPLETED"&&!stringArray(result.hard_blockers).length&&finite(result.risk_score)<40).map(result=>`${String(result.engine_id??"UNKNOWN")} returned no hard blocker.`);
  const riskBreakdown={};for(const result of usable)riskBreakdown[String(result.engine_id??"UNKNOWN")]=finite(result.risk_score);

  return {
    ...decisionBase(),decision:state,overall_risk_score:Number(risk.toFixed(2)),decision_confidence:Number(decisionConf.toFixed(2)),data_confidence:Number(dataConf.toFixed(2)),
    executive_summary:`Rivexis evaluated ${results.length} specialist engine result(s) and returned ${state}.`,critical_findings:[...hard,...warnings],positive_findings:positives,risk_breakdown:riskBreakdown,
    why,what_could_go_wrong:warnings,recommended_action:actions[state],safer_option:mitigations[0]??null,assumptions:unique(results.flatMap(result=>stringArray(result.assumptions))).sort(),missing_data:unique(results.flatMap(result=>stringArray(result.missing_data))).sort(),...prov,
  };
}

export function decisionReportHtml(decision){
  const engines=unique([...Object.keys(decision.engine_statuses??{}),...Object.keys(decision.engine_versions??{}),...Object.keys(decision.analysis_framework_versions??{})]).sort();
  const engineRows=engines.length?engines.map(engine=>`<tr><td>${escapeHtml(engine)}</td><td>${escapeHtml(decision.engine_statuses?.[engine]??"UNKNOWN")}</td><td>${escapeHtml(decision.engine_versions?.[engine]??"UNKNOWN")}</td><td>${escapeHtml(decision.analysis_framework_versions?.[engine]??"UNKNOWN")}</td></tr>`).join(""):'<tr><td colspan="4">No specialist engine provenance recorded.</td></tr>';
  const list=value=>stringArray(value).length?stringArray(value).map(item=>`<li>${escapeHtml(item)}</li>`).join(""):"<li>None recorded.</li>";
  const demo=decision.demo===true?'<div class="demo">DEMONSTRATION RESULT - NOT LIVE DATA</div>':"";
  return `<!doctype html><html><head><meta charset="utf-8"><title>Rivexis ${escapeHtml(decision.decision)} Report</title><style>body{font:15px system-ui;max-width:900px;margin:40px auto;color:#202B2D;background:#F3F2EC;padding:24px}.reportBrand{width:220px;max-width:100%;margin-bottom:30px}h1{color:#326C6A}.demo{padding:12px;background:#E2E7DD;border:1px solid #80AAA1}.metric{display:inline-block;margin:8px 24px 8px 0}table{border-collapse:collapse;width:100%;margin:8px 0 18px}th,td{border:1px solid #D9DFD7;padding:8px;text-align:left;vertical-align:top}th{background:#202B2D;color:#E9EBE7}code{word-break:break-all}</style></head><body><div class="reportBrand">${BRAND_REPORT_SVG}</div>${demo}<h1>RIVEXIS Decision Report</h1><p><b>Decision:</b> ${escapeHtml(decision.decision)}</p><div class="metric"><b>Risk:</b> ${finite(decision.overall_risk_score).toFixed(1)}/100</div><div class="metric"><b>Decision confidence:</b> ${finite(decision.decision_confidence).toFixed(1)}%</div><div class="metric"><b>Data confidence:</b> ${finite(decision.data_confidence).toFixed(1)}%</div><h2>Executive summary</h2><p>${escapeHtml(decision.executive_summary)}</p><h2>Why</h2><ul>${list(decision.why)}</ul><h2>Critical findings</h2><ul>${list(decision.critical_findings)}</ul><h2>Recommended action</h2><p>${escapeHtml(decision.recommended_action)}</p><h2>Evidence provenance</h2><p><b>Decision methodology:</b> ${escapeHtml(decision.decision_methodology_version)}<br><b>Canonical persistence:</b> ${decision.canonical_persistence_verified?"VERIFIED FROM PERSISTED ANALYSES":"NOT VERIFIED FROM PERSISTED ANALYSES"}<br><b>Evidence records:</b> ${finite(decision.evidence_count)}<br><b>Evidence sources:</b> ${stringArray(decision.evidence_sources).map(escapeHtml).join(", ")||"None recorded"}<br><b>Unresolved source conflicts:</b> ${finite(decision.unresolved_conflict_count)}</p><table><thead><tr><th>Engine</th><th>Status</th><th>Engine version</th><th>Analysis framework</th></tr></thead><tbody>${engineRows}</tbody></table><h3>Persisted analysis references</h3><ul>${list(decision.analysis_ids)}</ul><p><small>Generated only from the structured persisted decision payload above. Decision ID: ${escapeHtml(decision.decision_id)}</small></p></body></html>`;
}

export function decisionReportLines(decision){
  return [
    `Decision: ${String(decision.decision??"UNKNOWN")}`,
    `Risk: ${finite(decision.overall_risk_score).toFixed(1)}/100`,
    `Decision confidence: ${finite(decision.decision_confidence).toFixed(1)}%`,
    `Data confidence: ${finite(decision.data_confidence).toFixed(1)}%`,
    `Methodology: ${String(decision.decision_methodology_version??"UNKNOWN")}`,
    `Canonical persistence: ${decision.canonical_persistence_verified?"VERIFIED":"NOT VERIFIED"}`,
    `Demo: ${decision.demo===true?"YES - SYNTHETIC":"NO"}`,
    `Summary: ${String(decision.executive_summary??"")}`,
    `Recommended action: ${String(decision.recommended_action??"")}`,
    ...stringArray(decision.why).map(item=>`Why: ${item}`),
    ...stringArray(decision.analysis_ids).map(item=>`Analysis: ${item}`),
  ];
}
