from rivexis_api.decision import analyze_decision
from rivexis_api.engines import ENGINES
from rivexis_api.models.decision import DecisionRequest
from rivexis_api.models.enums import DecisionState, EngineId

def decide(*results): return analyze_decision(DecisionRequest(engine_results=list(results)))
def test_unknown_without_evidence(): assert decide().decision==DecisionState.UNKNOWN
def test_avoid_hard_blocker(): assert decide(ENGINES[EngineId.B2]({"known_malicious":True},True)).decision==DecisionState.AVOID
def test_modify_moderate_risk(): assert decide(ENGINES[EngineId.F3]({"health_factor":1.4},True)).decision==DecisionState.MODIFY
def test_proceed_low_risk(): assert decide(ENGINES[EngineId.B1]({},True)).decision==DecisionState.PROCEED
def test_conflict_reduces_confidence():
    a=decide(ENGINES[EngineId.B4]({},True));b=decide(ENGINES[EngineId.B4]({"label_conflict":True},True));assert b.decision_confidence<a.decision_confidence
