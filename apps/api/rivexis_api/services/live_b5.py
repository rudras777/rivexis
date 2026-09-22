from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from rivexis_api.chains import normalize_chain
from rivexis_api.models.engine import EngineResult
from rivexis_api.models.enums import AnalysisStatus, EngineId, FreshnessStatus, Severity
from rivexis_api.models.evidence import EvidenceRecord
from rivexis_api.provider_clients import LifiClient, ProviderCall, ProviderError


def _evidence(call: ProviderCall, normalized: Any) -> EvidenceRecord:
    return EvidenceRecord(
        evidence_id=str(uuid4()),
        provider="lifi",
        source_type="route_aggregator",
        provider_endpoint="GET /v1/quote",
        provider_request_id=call.request_id,
        retrieved_at=datetime.now(timezone.utc),
        observed_at=datetime.now(timezone.utc),
        raw_reference=f"provider:lifi;request:{call.request_id}",
        normalized_value=normalized,
        calculation_version="b5-live-1.1.0",
        engine_version="1.1.0",
        confidence=90,
        freshness=FreshnessStatus.LIVE,
        license_classification="external-provider-evidence",
    )


def _sev(score: float) -> Severity:
    if score >= 80:return Severity.CRITICAL
    if score >= 60:return Severity.HIGH
    if score >= 35:return Severity.MODERATE
    return Severity.LOW


def _usd_total(items: Any) -> float | None:
    if not isinstance(items, list):return None
    total=0.0; seen=False
    for item in items:
        if not isinstance(item, dict):continue
        value=item.get("amountUSD")
        if value not in (None, ""):
            try:total+=float(value);seen=True
            except (TypeError,ValueError):pass
    return round(total,6) if seen else None


def run_live_b5(input_data: dict[str, Any]) -> EngineResult:
    try:
        source = normalize_chain(input_data.get("source_chain") or input_data.get("fromChain"))
        destination = normalize_chain(input_data.get("destination_chain") or input_data.get("toChain"))
    except ValueError as exc:
        return _fail(str(exc), AnalysisStatus.UNSUPPORTED)

    from_token=input_data.get("source_token") or input_data.get("fromToken")
    to_token=input_data.get("destination_token") or input_data.get("toToken")
    amount=input_data.get("amount") or input_data.get("fromAmount")
    wallet=input_data.get("wallet") or input_data.get("fromAddress")
    to_address=input_data.get("toAddress")
    slippage=input_data.get("slippage",0.005)
    try:slippage=float(slippage)
    except (TypeError,ValueError):return _fail("slippage must be numeric")
    if slippage < 0 or slippage > 0.5:return _fail("slippage must be between 0 and 0.5")
    if not all([from_token,to_token,amount,wallet]):
        return _fail("B5 live analysis requires source/destination chain, token, amount in smallest units, and wallet")

    params={
        "fromChain":source.chain_id,"toChain":destination.chain_id,"fromToken":str(from_token),"toToken":str(to_token),
        "fromAmount":str(amount),"fromAddress":str(wallet),"toAddress":str(to_address) if to_address else None,"slippage":slippage,
        "order":input_data.get("order"),"allowBridges":input_data.get("allow_bridges"),"preferBridges":input_data.get("prefer_bridges"),
    }
    try:
        call=LifiClient().quote(params)
    except ProviderError as exc:
        return EngineResult(engine_id=EngineId.B5,engine_version="1.1.0",status=AnalysisStatus.PROVIDER_UNAVAILABLE,risk_score=0,data_confidence=0,engine_confidence=0,severity=Severity.UNKNOWN,summary="LI.FI route data is unavailable; no route was fabricated.",warnings=[f"{exc.code}: {exc}"],missing_data=["live cross-chain route quote"],provider_consensus="UNAVAILABLE",provider_status=[{"provider_id":"lifi","status":"UNAVAILABLE","detail":f"{exc.code}: {exc}"}])

    body=call.result if isinstance(call.result,dict) else {}
    estimate=body.get("estimate") if isinstance(body.get("estimate"),dict) else {}
    action=body.get("action") if isinstance(body.get("action"),dict) else {}
    tool_details=body.get("toolDetails") if isinstance(body.get("toolDetails"),dict) else {}
    included=body.get("includedSteps") if isinstance(body.get("includedSteps"),list) else []
    normalized={
        "route_id":body.get("id"),"tool":body.get("tool"),"tool_name":tool_details.get("name"),
        "from_chain":source.chain_id,"to_chain":destination.chain_id,
        "from_token":(action.get("fromToken") or {}).get("symbol") if isinstance(action.get("fromToken"),dict) else from_token,
        "to_token":(action.get("toToken") or {}).get("symbol") if isinstance(action.get("toToken"),dict) else to_token,
        "from_amount":action.get("fromAmount") or str(amount),"expected_to_amount":estimate.get("toAmount"),"minimum_to_amount":estimate.get("toAmountMin"),
        "execution_duration_seconds":estimate.get("executionDuration"),"gas_cost_usd":_usd_total(estimate.get("gasCosts")),"fee_cost_usd":_usd_total(estimate.get("feeCosts")),
        "included_steps":len(included),"approval_address":estimate.get("approvalAddress"),
    }
    score=22.0
    if len(included)>=4:score+=10
    if slippage>0.03:score+=12
    if source.chain_id!=destination.chain_id:score+=8
    warnings=["Route quote is aggregator evidence, not an independent bridge-security assessment."]
    missing=["independent bridge security intelligence","independent liquidity/dependency risk validation","historical bridge incident assessment"]
    if estimate.get("toAmountMin") in (None,""):
        missing.append("minimum received amount")
        warnings.append("LI.FI response did not provide a normalized minimum received amount.")
    return EngineResult(
        engine_id=EngineId.B5,engine_version="1.1.0",status=AnalysisStatus.PARTIAL,risk_score=min(100,score),data_confidence=82,engine_confidence=72,severity=_sev(score),
        summary="A live LI.FI route quote was normalized. Rivexis has not yet completed independent bridge-security/liquidity validation, so the route remains a partial analysis.",
        metrics=normalized,warnings=warnings,mitigations=["Cross-check bridge security and liquidity before signing a high-value cross-chain transaction."],
        safer_alternatives=["Request and compare additional routes after independent security providers are connected."],evidence=[_evidence(call,normalized)],provider_consensus="SINGLE SOURCE",
        data_freshness={"status":"LIVE","source":"LI.FI"},missing_data=missing,provider_status=[{"provider_id":"lifi","status":"HEALTHY","latency_ms":round(call.latency_ms,2)}],
        assumptions=["Rivexis does not execute or sign the returned route; the wallet remains under explicit user control."],
    )


def _fail(message: str,status:AnalysisStatus=AnalysisStatus.INSUFFICIENT_DATA)->EngineResult:
    return EngineResult(engine_id=EngineId.B5,engine_version="1.1.0",status=status,risk_score=0,data_confidence=0,engine_confidence=0,severity=Severity.UNKNOWN,summary=message,warnings=["No route was fabricated."],missing_data=["valid B5 route input"],provider_consensus="UNAVAILABLE")
