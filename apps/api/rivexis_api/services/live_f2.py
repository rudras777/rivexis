from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from rivexis_api.models.engine import EngineResult
from rivexis_api.models.enums import AnalysisStatus, EngineId, FreshnessStatus, Severity
from rivexis_api.models.evidence import EvidenceRecord
from rivexis_api.provider_clients import DefiLlamaClient, ProviderCall, ProviderError
from rivexis_api.services.protocol_native import collect_protocol_native, has_protocol_native_input


def _ev(call:ProviderCall,normalized:Any)->EvidenceRecord:
    return EvidenceRecord(evidence_id=str(uuid4()),provider="defillama",source_type="analytical_enriched_data",provider_endpoint="GET /protocol/{slug}",provider_request_id=call.request_id,retrieved_at=datetime.now(timezone.utc),observed_at=datetime.now(timezone.utc),raw_reference=f"provider:defillama;request:{call.request_id}",normalized_value=normalized,calculation_version="f2-live-1.1.0",engine_version="1.1.0",confidence=86,freshness=FreshnessStatus.CURRENT,license_classification="external-provider-evidence")

def _sev(score:float)->Severity:
    if score>=80:return Severity.CRITICAL
    if score>=60:return Severity.HIGH
    if score>=35:return Severity.MODERATE
    return Severity.LOW

def _latest_tvl(body:dict[str,Any])->float|None:
    series=body.get("tvl")
    if isinstance(series,list):
        for row in reversed(series):
            if isinstance(row,dict) and row.get("totalLiquidityUSD") is not None:
                try:return float(row["totalLiquidityUSD"])
                except (TypeError,ValueError):pass
    value=body.get("tvl")
    if isinstance(value,(int,float)):return float(value)
    chain_tvls=body.get("currentChainTvls")
    if isinstance(chain_tvls,dict):
        vals=[]
        for k,v in chain_tvls.items():
            if "-borrowed" in k.lower() or "-staking" in k.lower() or "-pool2" in k.lower():continue
            if isinstance(v,(int,float)):vals.append(float(v))
        if vals:return sum(vals)
    return None

def run_live_f2(input_data:dict[str,Any])->EngineResult:
    slug=str(input_data.get("protocol") or input_data.get("slug") or "").strip().lower()
    if not slug:return _fail("F2 live analysis requires a DefiLlama protocol slug")
    try:call=DefiLlamaClient().protocol(slug)
    except ProviderError as exc:
        return EngineResult(engine_id=EngineId.F2,engine_version="1.1.0",status=AnalysisStatus.PROVIDER_UNAVAILABLE,risk_score=0,data_confidence=0,engine_confidence=0,severity=Severity.UNKNOWN,summary="Protocol metrics provider is unavailable; no protocol risk score was fabricated.",warnings=[f"{exc.code}: {exc}"],missing_data=["protocol metrics"],provider_consensus="UNAVAILABLE",provider_status=[{"provider_id":"defillama","status":"UNAVAILABLE","detail":f"{exc.code}: {exc}"}])
    body=call.result if isinstance(call.result,dict) else {}
    tvl=_latest_tvl(body);chains=body.get("chains") if isinstance(body.get("chains"),list) else []
    audits=body.get("audits");audit_links=body.get("audit_links") if isinstance(body.get("audit_links"),list) else []
    try:audit_count=int(audits) if audits not in (None,"") else len(audit_links)
    except (TypeError,ValueError):audit_count=len(audit_links)
    normalized={"slug":slug,"name":body.get("name"),"category":body.get("category"),"tvl_usd":tvl,"chains":chains,"audit_count":audit_count,"audit_links_count":len(audit_links),"oracles":body.get("oracles"),"latest_fetch_ok":body.get("latestFetchIsOk")}
    score=20.0;warnings=[]
    if tvl is None:warnings.append("Current TVL could not be normalized from the provider response.")
    elif tvl<1_000_000:score+=25;warnings.append("Observed TVL is below $1M; economic/liquidity resilience requires deeper review.")
    elif tvl<10_000_000:score+=15
    if audit_count==0:score+=15;warnings.append("No audit evidence was present in the normalized DefiLlama record.")
    if len(chains)==1:score+=5
    if body.get("latestFetchIsOk") is False:score+=20;warnings.append("Provider indicates the latest protocol fetch is not healthy.")
    missing=["direct smart-contract state and upgrade/admin privilege analysis","independent exploit/security intelligence","protocol-native oracle configuration and freshness","governance concentration/timelock analysis","liquidity depth and liquidation mechanics","independent external risk evidence"]
    evidence=[_ev(call,normalized)]
    provider_status=[{"provider_id":"defillama","status":"HEALTHY","latency_ms":round(call.latency_ms,2)}]
    assumptions=["DefiLlama metrics are external analytical evidence and are not treated as Rivexis-owned direct chain state."]
    data_conf=74.0
    engine_conf=65.0
    if has_protocol_native_input(input_data):
        try:
            native=collect_protocol_native(input_data)
            normalized["protocol_native"]=native.metrics
            evidence.extend(native.evidence)
            provider_status.extend(native.provider_status)
            warnings.extend(native.warnings)
            assumptions.extend(native.assumptions)
            missing.extend(native.missing_data)
            score=min(100.0,score+native.risk_delta)
            data_conf=min(94.0,max(data_conf,native.confidence))
            engine_conf=min(88.0,engine_conf+10)
            contracts=native.metrics.get("declared_contracts") if isinstance(native.metrics,dict) else []
            if contracts:
                missing=[x for x in missing if x!="direct smart-contract state and upgrade/admin privilege analysis"]
            roles={str(x.get("role")) for x in contracts if isinstance(x,dict)}
            if "governance" in roles:
                missing=[x for x in missing if x!="governance concentration/timelock analysis"]
                missing.append("governance concentration/timelock semantics beyond declared governance contract state")
            if native.metrics.get("declared_oracle"):
                missing=[x for x in missing if x!="protocol-native oracle configuration and freshness"]
                missing.append("independent verification that the declared oracle is authoritative for the selected protocol/market")
        except (ValueError, ProviderError) as exc:
            warnings.append(f"Protocol-native evidence could not be collected: {exc}")
            missing.append("protocol-native evidence collection")
    consensus="MULTI_SOURCE" if len({e.provider for e in evidence})>1 else "SINGLE_SOURCE"
    summary=("F2 combined attributed protocol fundamentals with caller-declared direct contract/oracle evidence. Remaining gaps are preserved explicitly." if len(evidence)>1 else "F2 normalized live protocol fundamentals from DefiLlama. Direct security, oracle, governance and liquidity evidence remains incomplete.")
    return EngineResult(engine_id=EngineId.F2,engine_version="1.2.0",status=AnalysisStatus.PARTIAL,risk_score=min(100,score),data_confidence=data_conf,engine_confidence=engine_conf,severity=_sev(score),summary=summary,metrics=normalized,warnings=warnings,mitigations=["Do not deploy material capital until unresolved contract, oracle, governance and security evidence is independently validated."],safer_alternatives=["Use this result as a screening layer, then run the remaining protocol-native and security checks before allocation."],evidence=evidence,provider_consensus=consensus,data_freshness={"status":"CURRENT","provider":"multi-source" if consensus=="MULTI_SOURCE" else "defillama"},missing_data=sorted(set(missing)),provider_status=provider_status,assumptions=assumptions)

def _fail(message:str)->EngineResult:
    return EngineResult(engine_id=EngineId.F2,engine_version="1.1.0",status=AnalysisStatus.INSUFFICIENT_DATA,risk_score=0,data_confidence=0,engine_confidence=0,severity=Severity.UNKNOWN,summary=message,warnings=["No protocol metric or risk score was fabricated."],missing_data=["valid protocol slug"],provider_consensus="UNAVAILABLE")
