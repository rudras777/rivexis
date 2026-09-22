from __future__ import annotations
from uuid import uuid4
from rivexis_api.models.engine import EngineResult
from rivexis_api.models.enums import AnalysisStatus, EngineId, FreshnessStatus, Severity
from rivexis_api.models.evidence import EvidenceRecord, SourceConflict

ENGINE_NAMES={
EngineId.B1:"Transaction Simulation Engine",EngineId.B2:"Transaction & Contract Security Engine",EngineId.B3:"Real-Time Threat & Monitoring Engine",EngineId.B4:"On-Chain Entity & Fund-Flow Intelligence Engine",EngineId.B5:"Cross-Chain Route & Bridge Intelligence Engine",
EngineId.F1:"Portfolio & Exposure Engine",EngineId.F2:"Protocol Risk Engine",EngineId.F3:"Position & Liquidation Risk Engine",EngineId.F4:"Yield & Strategy Risk Engine",EngineId.F5:"Treasury Allocation & Scenario Engine"}

def _sev(score):
    return Severity.CRITICAL if score>=80 else Severity.HIGH if score>=60 else Severity.MODERATE if score>=35 else Severity.LOW

def _demo_evidence(engine_id,input_data):
    return EvidenceRecord(evidence_id=str(uuid4()),provider="Rivexis Demo Adapter",source_type="demo",normalized_value=input_data,confidence=75,freshness=FreshnessStatus.CURRENT)

def _score(engine_id,d):
    # Deterministic, transparent demo heuristics only. Live engines must use normalized provider evidence.
    if engine_id==EngineId.B1:
        return min(100, (45 if d.get("will_revert") else 10)+(35 if d.get("unlimited_approval") else 0)+(20 if d.get("suspicious_value_flow") else 0))
    if engine_id==EngineId.B2:
        return min(100,(85 if d.get("known_malicious") else 0)+(35 if d.get("unlimited_approval") else 0)+(20 if d.get("unverified_contract") else 0))
    if engine_id==EngineId.B3:
        return min(100,(80 if d.get("active_exploit") else 0)+(40 if d.get("oracle_anomaly") else 0)+(30 if d.get("liquidity_deterioration") else 0))
    if engine_id==EngineId.B4:
        return min(100,(35 if d.get("label_conflict") else 0)+(30 if d.get("suspicious_flow") else 0)+(20 if d.get("holder_concentration",0)>0.7 else 0))
    if engine_id==EngineId.B5:
        return min(100,float(d.get("route_risk",25))+(20 if d.get("bridge_incident") else 0)+(15 if d.get("low_liquidity") else 0))
    if engine_id==EngineId.F1:
        concentration=float(d.get("largest_exposure_pct",25)); return min(100,max(10,concentration)+(25 if d.get("stablecoin_concentration",0)>0.7 else 0))
    if engine_id==EngineId.F2:
        return min(100,(60 if d.get("exploit_history") else 0)+(25 if d.get("admin_privilege") else 0)+(25 if d.get("oracle_risk") else 0)+(20 if d.get("low_liquidity") else 0))
    if engine_id==EngineId.F3:
        hf=float(d.get("health_factor",2.0)); return 90 if hf<1.05 else 75 if hf<1.2 else 45 if hf<1.5 else 20
    if engine_id==EngineId.F4:
        apy=float(d.get("apy",0)); return min(100,20+(25 if apy>30 else 0)+(30 if d.get("incentive_dependent") else 0)+(25 if d.get("lockup") else 0))
    if engine_id==EngineId.F5:
        concentration=float(d.get("largest_allocation_pct",25)); return min(100,max(15,concentration)+(30 if d.get("stablecoin_depeg_scenario_loss_pct",0)>20 else 0))
    return 0

def run_engine(engine_id:EngineId,input_data:dict,demo:bool=False):
    if not demo and engine_id == EngineId.B1:
        from rivexis_api.services.live_b1 import run_live_b1
        return run_live_b1(input_data)
    if not demo and engine_id == EngineId.B2:
        from rivexis_api.services.live_b2 import run_live_b2
        return run_live_b2(input_data)
    if not demo and engine_id == EngineId.B3:
        from rivexis_api.services.live_b3 import run_live_b3
        return run_live_b3(input_data)
    if not demo and engine_id == EngineId.B4:
        from rivexis_api.services.live_b4 import run_live_b4
        return run_live_b4(input_data)
    if not demo and engine_id == EngineId.B5:
        from rivexis_api.services.live_b5 import run_live_b5
        return run_live_b5(input_data)
    if not demo and engine_id == EngineId.F1:
        from rivexis_api.services.live_f1 import run_live_f1
        return run_live_f1(input_data)
    if not demo and engine_id == EngineId.F2:
        from rivexis_api.services.live_f2 import run_live_f2
        return run_live_f2(input_data)
    if not demo and engine_id == EngineId.F3:
        from rivexis_api.services.live_f3 import run_live_f3
        return run_live_f3(input_data)
    if not demo and engine_id == EngineId.F4:
        from rivexis_api.services.live_f4 import run_live_f4
        return run_live_f4(input_data)
    if not demo and engine_id == EngineId.F5:
        from rivexis_api.services.live_f5 import run_live_f5
        return run_live_f5(input_data)
    if not demo:
        return EngineResult(engine_id=engine_id,status=AnalysisStatus.INSUFFICIENT_DATA,risk_score=0,data_confidence=0,engine_confidence=0,severity=Severity.UNKNOWN,summary=f"{ENGINE_NAMES[engine_id]} requires normalized live provider evidence.",warnings=["No fabricated live analysis was produced."],missing_data=["normalized provider evidence"],provider_consensus="UNAVAILABLE",demo=False)
    score=_score(engine_id,input_data)
    blockers=[]; warnings=[]; mitigations=[]; conflicts=[]
    if input_data.get("known_malicious") or input_data.get("active_exploit"): blockers.append("Material security blocker detected in demonstration input")
    if input_data.get("unlimited_approval"): warnings.append("Unlimited approval increases token exposure"); mitigations.append("Reduce approval to the minimum required amount")
    if input_data.get("label_conflict"):
        conflicts.append(SourceConflict(metric="entity_label",source_a="Demo Source A",value_a="Entity A",source_b="Demo Source B",value_b="Entity B",severity="high",resolution_method="unresolved",resolution_confidence=0))
        warnings.append("Entity labels conflict; identity is not resolved")
    if input_data.get("price_conflict_pct",0)>3:
        conflicts.append(SourceConflict(metric="reference_price",source_a="Demo Price A",value_a=100,source_b="Demo Price B",value_b=100*(1+float(input_data['price_conflict_pct'])/100),difference_percentage=float(input_data['price_conflict_pct']),severity="high",resolution_method="unresolved",resolution_confidence=0))
    status=AnalysisStatus.CONFLICTING_DATA if conflicts else AnalysisStatus.COMPLETED
    conf=65 if conflicts else 82
    return EngineResult(engine_id=engine_id,status=status,risk_score=score,data_confidence=conf,engine_confidence=80,severity=_sev(score),summary=f"Demonstration result for {ENGINE_NAMES[engine_id]}: detected risk score {score:.0f}/100.",metrics={"input_echo":input_data},warnings=warnings,hard_blockers=blockers,mitigations=mitigations,safer_alternatives=mitigations[:],evidence=[_demo_evidence(engine_id,input_data)],provider_consensus="CONFLICTING" if conflicts else "SINGLE SOURCE",provider_conflicts=conflicts,data_freshness={"status":"CURRENT","source":"demo"},assumptions=["Synthetic demonstration inputs supplied by the user/interface."],demo=True)

ENGINES={eid:(lambda data,demo=False,eid=eid:run_engine(eid,data,demo)) for eid in EngineId}
