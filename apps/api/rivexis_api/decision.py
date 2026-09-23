from statistics import fmean

from rivexis_api.models.decision import DecisionRequest, RivexisDecision
from rivexis_api.models.engine import EngineResult
from rivexis_api.models.enums import AnalysisStatus, DecisionState

USABLE_STATUSES = {
    AnalysisStatus.COMPLETED,
    AnalysisStatus.PARTIAL,
    AnalysisStatus.CONFLICTING_DATA,
    AnalysisStatus.STALE_DATA,
}


def _canonicalize_persisted(results: list[EngineResult]) -> tuple[list[EngineResult], bool]:
    # API callers submit full EngineResult objects for backward compatibility, but
    # decisions must never trust client-supplied scores/confidence/blockers once an
    # analysis_id has been persisted. The API router already authorizes each ID;
    # this layer rehydrates the canonical stored payload before scoring it.
    from rivexis_api.services.store import analysis_record

    canonical: list[EngineResult] = []
    persisted = 0
    for submitted in results:
        record = analysis_record(submitted.analysis_id)
        if record:
            canonical.append(EngineResult.model_validate(record["payload"]))
            persisted += 1
        else:
            canonical.append(submitted)
    return canonical, bool(canonical) and persisted == len(canonical)


def _provenance(results: list[EngineResult], canonical_persistence_verified: bool):
    return {
        "analysis_ids": [r.analysis_id for r in results],
        "engine_versions": {r.engine_id.value: r.engine_version for r in results},
        "engine_statuses": {r.engine_id.value: r.status.value for r in results},
        "analysis_framework_versions": {r.engine_id.value: r.analysis_framework_version for r in results},
        "evidence_sources": sorted({e.provider for r in results for e in r.evidence}),
        "unresolved_conflict_count": sum(len(r.provider_conflicts) for r in results),
        "evidence_count": sum(len(r.evidence) for r in results),
        "canonical_persistence_verified": canonical_persistence_verified,
        "demo": any(r.demo for r in results),
    }


def _duplicate_reference_decision(results: list[EngineResult], reason: str, canonical: bool) -> RivexisDecision:
    provenance = _provenance(results, canonical)
    return RivexisDecision(
        decision=DecisionState.UNKNOWN,
        overall_risk_score=0,
        decision_confidence=0,
        data_confidence=round(fmean(r.data_confidence for r in results), 2) if results else 0,
        executive_summary="Decision inputs contain duplicate analytical references and cannot be weighted safely.",
        why=[reason],
        recommended_action="Use one unique persisted result per specialist engine before requesting a decision.",
        missing_data=["unique decision-grade specialist engine results"],
        **provenance,
    )


def analyze_decision(req: DecisionRequest) -> RivexisDecision:
    submitted = req.engine_results
    if not submitted:
        return RivexisDecision(
            decision=DecisionState.UNKNOWN,
            overall_risk_score=0,
            decision_confidence=0,
            data_confidence=0,
            executive_summary="No engine evidence was supplied.",
            recommended_action="Collect required evidence before acting.",
            missing_data=["engine results"],
        )

    results, canonical = _canonicalize_persisted(submitted)
    analysis_ids = [r.analysis_id for r in results]
    if len(set(analysis_ids)) != len(analysis_ids):
        return _duplicate_reference_decision(
            results,
            "The same persisted analysis_id was submitted more than once; repeated references are not additional evidence.",
            canonical,
        )
    engine_ids = [r.engine_id.value for r in results]
    if len(set(engine_ids)) != len(engine_ids):
        return _duplicate_reference_decision(
            results,
            "Multiple results from the same specialist engine were supplied; the shared decision model does not silently overweight one engine.",
            canonical,
        )

    provenance = _provenance(results, canonical)
    usable = [r for r in results if r.status in USABLE_STATUSES]
    if not usable:
        return RivexisDecision(
            decision=DecisionState.UNKNOWN,
            overall_risk_score=0,
            decision_confidence=0,
            data_confidence=round(fmean(r.data_confidence for r in results), 2),
            executive_summary="Required evidence is insufficient to support a Rivexis decision.",
            why=["No submitted specialist result is in a decision-usable evidence state."],
            recommended_action="Obtain fresh normalized provider evidence.",
            missing_data=sorted({x for r in results for x in r.missing_data}),
            **provenance,
        )

    hard = [b for r in usable for b in r.hard_blockers]
    risk = max(r.risk_score for r in usable) if hard else fmean(r.risk_score for r in usable)
    data_conf = fmean(r.data_confidence for r in usable)
    engine_conf = fmean(r.engine_confidence for r in usable)
    conflicts = sum(len(r.provider_conflicts) for r in usable)
    uncertain = [r for r in results if r.status != AnalysisStatus.COMPLETED]
    decision_conf = max(0, min(100, (data_conf + engine_conf) / 2 - conflicts * 12 - len(uncertain) * 10))

    # A material hard blocker is independently actionable. Otherwise Rivexis never
    # turns partial/stale/conflicting/unavailable evidence into PROCEED/MODIFY/AVOID;
    # uncertainty remains WAIT/UNKNOWN until the requested evidence is decision-grade.
    if hard:
        state = DecisionState.AVOID
    elif data_conf < 35:
        state = DecisionState.UNKNOWN
    elif uncertain:
        state = DecisionState.WAIT
    elif risk >= 80:
        state = DecisionState.AVOID
    elif risk >= 40:
        state = DecisionState.MODIFY
    else:
        state = DecisionState.PROCEED

    why = [f"Aggregate materialized risk assessment is {risk:.1f}/100 across {len(usable)} usable specialist result(s)."]
    if hard:
        why.append(f"{len(hard)} hard blocker(s) override aggregate scoring.")
    if uncertain:
        detail = ", ".join(f"{r.engine_id.value}={r.status.value}" for r in uncertain)
        why.append(f"Decision-grade evidence is incomplete or unresolved: {detail}.")
    if conflicts:
        why.append(f"{conflicts} unresolved source conflict(s) reduce decision confidence.")
    if data_conf < 60:
        why.append("Data confidence is below the preferred institutional threshold.")

    action = {
        DecisionState.PROCEED: "Proceed subject to the stated assumptions and current evidence.",
        DecisionState.MODIFY: "Modify the exposure or transaction to reduce identified material risks.",
        DecisionState.WAIT: "Wait until partial, stale, unavailable, or conflicting evidence is resolved.",
        DecisionState.AVOID: "Avoid the proposed action while material blockers remain.",
        DecisionState.UNKNOWN: "Do not act on this analysis; evidence is insufficient.",
    }[state]
    mitigations = [m for r in usable for m in r.mitigations]
    warnings = [w for r in usable for w in r.warnings]
    positives = [
        f"{r.engine_id.value} returned no hard blocker."
        for r in usable
        if r.status == AnalysisStatus.COMPLETED and not r.hard_blockers and r.risk_score < 40
    ]

    return RivexisDecision(
        decision=state,
        overall_risk_score=round(risk, 2),
        decision_confidence=round(decision_conf, 2),
        data_confidence=round(data_conf, 2),
        executive_summary=f"Rivexis evaluated {len(results)} specialist engine result(s) and returned {state.value}.",
        critical_findings=hard + warnings,
        positive_findings=positives,
        risk_breakdown={r.engine_id.value: r.risk_score for r in usable},
        why=why,
        what_could_go_wrong=warnings,
        recommended_action=action,
        safer_option=(mitigations[0] if mitigations else None),
        assumptions=sorted({a for r in results for a in r.assumptions}),
        missing_data=sorted({x for r in results for x in r.missing_data}),
        **provenance,
    )
