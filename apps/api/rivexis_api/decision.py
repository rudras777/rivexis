from statistics import fmean
from rivexis_api.models.decision import DecisionRequest, RivexisDecision
from rivexis_api.models.enums import AnalysisStatus, DecisionState

def analyze_decision(req:DecisionRequest)->RivexisDecision:
    results=req.engine_results
    if not results:
        return RivexisDecision(decision=DecisionState.UNKNOWN,overall_risk_score=0,decision_confidence=0,data_confidence=0,executive_summary="No engine evidence was supplied.",recommended_action="Collect required evidence before acting.",missing_data=["engine results"])
    live_usable=[r for r in results if r.status in {AnalysisStatus.COMPLETED,AnalysisStatus.PARTIAL,AnalysisStatus.CONFLICTING_DATA,AnalysisStatus.STALE_DATA}]
    if not live_usable:
        return RivexisDecision(decision=DecisionState.UNKNOWN,overall_risk_score=0,decision_confidence=0,data_confidence=fmean(r.data_confidence for r in results),executive_summary="Required evidence is insufficient to support a Rivexis decision.",recommended_action="Obtain fresh normalized provider evidence.",missing_data=sorted({x for r in results for x in r.missing_data}),demo=any(r.demo for r in results))
    hard=[b for r in live_usable for b in r.hard_blockers]
    risk=max(r.risk_score for r in live_usable) if hard else fmean(r.risk_score for r in live_usable)
    data_conf=fmean(r.data_confidence for r in live_usable)
    engine_conf=fmean(r.engine_confidence for r in live_usable)
    conflicts=sum(len(r.provider_conflicts) for r in live_usable)
    stale=any(r.status==AnalysisStatus.STALE_DATA for r in live_usable)
    decision_conf=max(0,min(100,(data_conf+engine_conf)/2 - conflicts*12 - (15 if stale else 0)))
    if data_conf<35: state=DecisionState.UNKNOWN
    elif hard or risk>=80: state=DecisionState.AVOID
    elif stale or conflicts>=2: state=DecisionState.WAIT
    elif risk>=40: state=DecisionState.MODIFY
    else: state=DecisionState.PROCEED
    why=[]
    why.append(f"Highest materialized risk assessment is {risk:.1f}/100.")
    if hard: why.append(f"{len(hard)} hard blocker(s) override weighted scoring.")
    if conflicts: why.append(f"{conflicts} unresolved source conflict(s) reduce decision confidence.")
    if data_conf<60: why.append("Data confidence is below the preferred institutional threshold.")
    action={DecisionState.PROCEED:"Proceed subject to the stated assumptions and current evidence.",DecisionState.MODIFY:"Modify the exposure or transaction to reduce identified material risks.",DecisionState.WAIT:"Wait until temporary, stale, or conflicting evidence is resolved.",DecisionState.AVOID:"Avoid the proposed action while material blockers remain.",DecisionState.UNKNOWN:"Do not act on this analysis; evidence is insufficient."}[state]
    mitigations=[m for r in live_usable for m in r.mitigations]
    warnings=[w for r in live_usable for w in r.warnings]
    positives=[f"{r.engine_id.value} returned no hard blocker." for r in live_usable if not r.hard_blockers and r.risk_score<40]
    return RivexisDecision(decision=state,overall_risk_score=round(risk,2),decision_confidence=round(decision_conf,2),data_confidence=round(data_conf,2),executive_summary=f"Rivexis evaluated {len(live_usable)} applicable specialist engine result(s) and returned {state.value}.",critical_findings=hard+warnings,positive_findings=positives,risk_breakdown={r.engine_id.value:r.risk_score for r in live_usable},why=why,what_could_go_wrong=warnings,recommended_action=action,safer_option=(mitigations[0] if mitigations else None),assumptions=sorted({a for r in results for a in r.assumptions}),missing_data=sorted({x for r in results for x in r.missing_data}),evidence_count=sum(len(r.evidence) for r in results),demo=any(r.demo for r in results))
