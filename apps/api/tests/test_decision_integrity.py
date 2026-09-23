from rivexis_api.decision import analyze_decision
from rivexis_api.models.decision import DecisionRequest
from rivexis_api.models.engine import EngineResult
from rivexis_api.models.enums import AnalysisStatus, DecisionState, EngineId, Severity
from rivexis_api.models.evidence import SourceConflict


def decide(*results):
    return analyze_decision(DecisionRequest(engine_results=list(results)))


def result(engine_id=EngineId.B1, *, status=AnalysisStatus.COMPLETED, risk=10, data_conf=90, engine_conf=90, blockers=None, conflicts=None):
    return EngineResult(
        engine_id=engine_id,
        status=status,
        risk_score=risk,
        data_confidence=data_conf,
        engine_confidence=engine_conf,
        severity=Severity.LOW,
        summary="fixture",
        hard_blockers=blockers or [],
        provider_conflicts=conflicts or [],
    )


def provision(client, email):
    signup = client.post('/api/v1/auth/signup', json={"email": email, "password": "correct-horse-battery", "role": "Analyst"})
    assert signup.status_code == 200
    headers = {"Authorization": "Bearer " + signup.json()["access_token"]}
    workspace = client.post('/api/v1/workspaces', headers=headers, json={"name": "Decision Integrity", "role": "Analyst"})
    assert workspace.status_code == 200
    return headers, workspace.json()


def test_partial_evidence_cannot_become_proceed():
    decision = decide(result(status=AnalysisStatus.PARTIAL, risk=5, data_conf=95, engine_conf=95))
    assert decision.decision == DecisionState.WAIT
    assert "B1=PARTIAL" in " ".join(decision.why)


def test_single_conflicting_result_cannot_become_proceed():
    conflict = SourceConflict(metric="price", source_a="a", value_a=100, source_b="b", value_b=105)
    decision = decide(result(status=AnalysisStatus.CONFLICTING_DATA, risk=5, data_conf=95, engine_conf=95, conflicts=[conflict]))
    assert decision.decision == DecisionState.WAIT
    assert decision.unresolved_conflict_count == 1


def test_unavailable_requested_engine_prevents_positive_decision():
    completed = result(EngineId.B1, risk=5)
    unavailable = result(EngineId.F2, status=AnalysisStatus.PROVIDER_UNAVAILABLE, risk=0, data_conf=0, engine_conf=0)
    decision = decide(completed, unavailable)
    assert decision.decision == DecisionState.WAIT
    assert decision.engine_statuses == {"B1": "COMPLETED", "F2": "PROVIDER_UNAVAILABLE"}


def test_hard_blocker_remains_actionable_even_with_partial_evidence():
    decision = decide(result(status=AnalysisStatus.PARTIAL, risk=20, blockers=["Known malicious destination"]))
    assert decision.decision == DecisionState.AVOID


def test_duplicate_analysis_reference_is_not_reweighted():
    analysis = result(risk=5)
    decision = decide(analysis, analysis.model_copy(deep=True))
    assert decision.decision == DecisionState.UNKNOWN
    assert decision.decision_confidence == 0
    assert "same persisted analysis_id" in " ".join(decision.why)


def test_duplicate_specialist_engine_is_not_silently_overweighted():
    first = result(EngineId.B1, risk=5)
    second = result(EngineId.B1, risk=90)
    decision = decide(first, second)
    assert decision.decision == DecisionState.UNKNOWN
    assert "same specialist engine" in " ".join(decision.why)


def test_api_decision_uses_persisted_engine_result_not_tampered_client_copy(client):
    headers, workspace = provision(client, "decision-tamper@example.com")
    analysis = client.post(
        '/api/v1/analysis/security',
        headers=headers,
        json={"demo": True, "workspace_id": workspace["id"], "input": {"known_malicious": True}},
    )
    assert analysis.status_code == 200
    canonical = analysis.json()
    assert canonical["hard_blockers"]
    assert canonical["risk_score"] >= 80
    assert canonical["analysis_framework_version"]

    tampered = dict(canonical)
    tampered.update({
        "risk_score": 0,
        "data_confidence": 100,
        "engine_confidence": 100,
        "severity": "low",
        "hard_blockers": [],
        "warnings": [],
        "provider_conflicts": [],
        "summary": "client says safe",
    })
    response = client.post('/api/v1/decisions/analyze', headers=headers, json={"engine_results": [tampered]})
    assert response.status_code == 200
    body = response.json()
    assert body["decision"] == "AVOID"
    assert body["risk_breakdown"]["B2"] == canonical["risk_score"]
    assert body["canonical_persistence_verified"] is True
    assert body["analysis_ids"] == [canonical["analysis_id"]]
    assert body["engine_versions"]["B2"] == canonical["engine_version"]
    assert body["analysis_framework_versions"]["B2"] == canonical["analysis_framework_version"]


def test_api_duplicate_persisted_analysis_cannot_skew_decision(client):
    headers, workspace = provision(client, "decision-duplicate@example.com")
    analysis = client.post(
        '/api/v1/analysis/simulations',
        headers=headers,
        json={"demo": True, "workspace_id": workspace["id"], "input": {}},
    ).json()
    response = client.post('/api/v1/decisions/analyze', headers=headers, json={"engine_results": [analysis, analysis]})
    assert response.status_code == 200
    body = response.json()
    assert body["decision"] == "UNKNOWN"
    assert body["decision_confidence"] == 0
    assert body["canonical_persistence_verified"] is True
