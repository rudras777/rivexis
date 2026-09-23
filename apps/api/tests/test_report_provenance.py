from rivexis_api.models.decision import RivexisDecision
from rivexis_api.models.enums import DecisionState
from rivexis_api.services.reports import decision_html, decision_pdf


def provenance_decision():
    return RivexisDecision(
        decision=DecisionState.WAIT,
        overall_risk_score=28,
        decision_confidence=54,
        data_confidence=62,
        executive_summary="Evidence is incomplete.",
        why=["B5=PARTIAL."],
        recommended_action="Wait until partial evidence is resolved.",
        analysis_ids=["analysis-b5"],
        engine_versions={"B5": "2.4.0"},
        engine_statuses={"B5": "PARTIAL"},
        analysis_framework_versions={"B5": "1.0.0"},
        evidence_sources=["lifi"],
        evidence_count=1,
        unresolved_conflict_count=0,
        canonical_persistence_verified=True,
        missing_data=["independent bridge security assessment"],
    )


def test_decision_html_discloses_exact_persisted_provenance():
    html = decision_html(provenance_decision())
    assert "Evidence provenance" in html
    assert "Decision methodology" in html
    assert "VERIFIED FROM PERSISTED ANALYSES" in html
    assert "analysis-b5" in html
    assert "B5" in html and "PARTIAL" in html
    assert "2.4.0" in html and "1.0.0" in html
    assert "lifi" in html
    assert "Unresolved source conflicts:</b> 0" in html
    assert "Generated only from the structured decision payload above" in html


def test_decision_html_does_not_claim_canonical_verification_when_absent():
    decision = provenance_decision().model_copy(update={"canonical_persistence_verified": False})
    html = decision_html(decision)
    assert "NOT VERIFIED FROM PERSISTED ANALYSES" in html
    assert "VERIFIED FROM PERSISTED ANALYSES" not in html.replace("NOT VERIFIED FROM PERSISTED ANALYSES", "")


def test_decision_pdf_renders_provenance_without_external_fetches():
    payload = decision_pdf(provenance_decision())
    assert payload.startswith(b"%PDF-")
    assert len(payload) > 1800
