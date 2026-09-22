from rivexis_api.engines import ENGINES
from rivexis_api.models.enums import AnalysisStatus, EngineId

def test_exactly_ten_engines(): assert set(ENGINES)==set(EngineId) and len(ENGINES)==10
def test_live_without_provider_evidence_fails_safe():
    r=ENGINES[EngineId.B2]({},False);assert r.status in {AnalysisStatus.INSUFFICIENT_DATA,AnalysisStatus.PROVIDER_UNAVAILABLE} and r.demo is False and r.risk_score==0
def test_demo_malicious_is_high_risk():
    r=ENGINES[EngineId.B2]({"known_malicious":True},True);assert r.risk_score>=80 and r.hard_blockers and r.demo
def test_label_conflict_is_not_silently_resolved():
    r=ENGINES[EngineId.B4]({"label_conflict":True},True);assert r.provider_conflicts and r.provider_conflicts[0].resolution_method=="unresolved"
def test_liquidation_engine_near_threshold(): assert ENGINES[EngineId.F3]({"health_factor":1.03},True).risk_score>=80
def test_treasury_concentration_detected(): assert ENGINES[EngineId.F5]({"largest_allocation_pct":82},True).risk_score>=80
