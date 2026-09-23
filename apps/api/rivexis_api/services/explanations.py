from rivexis_api.models.decision import RivexisDecision


def grounded_explanation(d: RivexisDecision):
    return {
        "decision_id": d.decision_id,
        "grounded": True,
        "decision": d.decision.value,
        "decision_methodology_version": d.decision_methodology_version,
        "summary": d.executive_summary,
        "why": d.why,
        "critical_findings": d.critical_findings,
        "recommended_action": d.recommended_action,
        "safer_option": d.safer_option,
        "missing_data": d.missing_data,
        "assumptions": d.assumptions,
        "analysis_ids": d.analysis_ids,
        "engine_versions": d.engine_versions,
        "engine_statuses": d.engine_statuses,
        "analysis_framework_versions": d.analysis_framework_versions,
        "evidence_sources": d.evidence_sources,
        "evidence_count": d.evidence_count,
        "unresolved_conflict_count": d.unresolved_conflict_count,
        "canonical_persistence_verified": d.canonical_persistence_verified,
        "disclaimer": "This explanation only restates structured Rivexis evidence; it does not generate a new risk score.",
    }
