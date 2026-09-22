from rivexis_api.models.decision import RivexisDecision

def grounded_explanation(d:RivexisDecision):
    return {"decision_id":d.decision_id,"grounded":True,"decision":d.decision.value,"summary":d.executive_summary,"why":d.why,"critical_findings":d.critical_findings,"recommended_action":d.recommended_action,"safer_option":d.safer_option,"disclaimer":"This explanation only restates structured Rivexis evidence; it does not generate a new risk score."}
