from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from rivexis_api.models.engine import EngineResult
from rivexis_api.models.enums import AnalysisStatus, EngineId, FreshnessStatus, Severity
from rivexis_api.models.evidence import EvidenceRecord
from rivexis_api.provider_clients import CoinGeckoClient, ProviderError
from rivexis_api.services.protocol_native import collect_protocol_native, has_protocol_native_input


def _num(v, default=None):
    try:
        if v in (None, ""):
            return default
        return float(v)
    except (TypeError, ValueError):
        return default


def _severity(score: float) -> Severity:
    return Severity.CRITICAL if score >= 80 else Severity.HIGH if score >= 60 else Severity.MODERATE if score >= 35 else Severity.LOW


def _price_freshness(prices: dict, ids: list[str]):
    now = datetime.now(timezone.utc)
    stamps = []
    for cid in ids:
        raw = (prices.get(cid) or {}).get("last_updated_at") if isinstance(prices.get(cid), dict) else None
        try:
            if raw not in (None, ""):
                stamps.append(float(raw))
        except (TypeError, ValueError):
            pass
    if not stamps:
        return FreshnessStatus.UNKNOWN, None, now
    observed = datetime.fromtimestamp(min(stamps), tz=timezone.utc)
    age = max(0.0, (now - observed).total_seconds())
    status = FreshnessStatus.LIVE if age <= 120 else FreshnessStatus.CURRENT if age <= 900 else FreshnessStatus.RECENT if age <= 3600 else FreshnessStatus.STALE if age <= 21600 else FreshnessStatus.EXPIRED
    return status, age, observed


def run_live_f5(data: dict) -> EngineResult:
    raw = data.get("allocations")
    if not isinstance(raw, list) or not raw:
        return EngineResult(
            engine_id=EngineId.F5,
            status=AnalysisStatus.INSUFFICIENT_DATA,
            risk_score=0,
            data_confidence=0,
            engine_confidence=0,
            severity=Severity.UNKNOWN,
            summary="F5 requires an allocations array with current or proposed treasury positions.",
            warnings=["No fabricated treasury allocation was produced."],
            missing_data=["allocations"],
            provider_consensus="UNAVAILABLE",
            demo=False,
        )

    allocations = [a for a in raw if isinstance(a, dict)]
    ids = sorted({str(a.get("coingecko_id") or "").strip() for a in allocations if a.get("coingecko_id")})
    prices: dict = {}
    call = None
    if ids:
        try:
            call = CoinGeckoClient().simple_price(ids)
            prices = call.result if isinstance(call.result, dict) else {}
        except ProviderError as exc:
            return EngineResult(
                engine_id=EngineId.F5,
                status=AnalysisStatus.PROVIDER_UNAVAILABLE,
                risk_score=0,
                data_confidence=0,
                engine_confidence=0,
                severity=Severity.UNKNOWN,
                summary="Current market-reference data is unavailable; Rivexis did not fabricate treasury valuations.",
                warnings=[str(exc)],
                missing_data=["current market reference prices"],
                provider_consensus="UNAVAILABLE",
                provider_status=[{"provider_id": exc.provider_id, "status": exc.code}],
                demo=False,
            )

    capital = _num(data.get("capital_usd"))
    normalized: list[dict] = []
    value_total = 0.0
    explicit_weights = True
    for a in allocations:
        cid = str(a.get("coingecko_id") or "").strip()
        price = _num((prices.get(cid) or {}).get("usd")) if cid else None
        quantity = _num(a.get("quantity"))
        weight = _num(a.get("weight_pct"))
        value = None
        if quantity is not None and price is not None:
            value = quantity * price
            value_total += value
        if weight is None:
            explicit_weights = False
        normalized.append({
            "coingecko_id": cid or None,
            "symbol": a.get("symbol") or cid or "UNKNOWN",
            "quantity": quantity,
            "price_usd": price,
            "value_usd": value,
            "weight_pct": weight,
            "stablecoin": bool(a.get("stablecoin", False)),
            "protocol": a.get("protocol"),
            "chain": a.get("chain"),
        })

    if not explicit_weights:
        if value_total <= 0:
            return EngineResult(
                engine_id=EngineId.F5,
                status=AnalysisStatus.INSUFFICIENT_DATA,
                risk_score=0,
                data_confidence=25,
                engine_confidence=30,
                severity=Severity.UNKNOWN,
                summary="Treasury weights could not be derived from the supplied allocations.",
                warnings=["Provide weight_pct for every allocation or quantity plus a CoinGecko id."],
                missing_data=["allocation weights"],
                provider_consensus="SINGLE SOURCE" if call else "UNAVAILABLE",
                demo=False,
            )
        for row in normalized:
            row["weight_pct"] = ((row["value_usd"] or 0.0) / value_total) * 100
        capital = capital or value_total
    else:
        weight_sum = sum(float(r["weight_pct"] or 0) for r in normalized)
        if weight_sum <= 0:
            return EngineResult(
                engine_id=EngineId.F5,
                status=AnalysisStatus.INSUFFICIENT_DATA,
                risk_score=0,
                data_confidence=0,
                engine_confidence=0,
                severity=Severity.UNKNOWN,
                summary="Treasury allocation weights must sum to a positive value.",
                missing_data=["valid allocation weights"],
                demo=False,
            )
        # Normalize deliberately instead of silently assuming the user summed to 100.
        for row in normalized:
            row["weight_pct"] = (float(row["weight_pct"] or 0) / weight_sum) * 100
            if capital is not None:
                row["value_usd"] = capital * row["weight_pct"] / 100

    largest = max((float(r["weight_pct"] or 0) for r in normalized), default=0.0)
    hhi = sum((float(r["weight_pct"] or 0) / 100) ** 2 for r in normalized)
    stable_weight = sum(float(r["weight_pct"] or 0) for r in normalized if r["stablecoin"])
    protocol_weights: dict[str, float] = {}
    chain_weights: dict[str, float] = {}
    for r in normalized:
        if r.get("protocol"):
            protocol_weights[str(r["protocol"])] = protocol_weights.get(str(r["protocol"]), 0.0) + float(r["weight_pct"] or 0)
        if r.get("chain"):
            chain_weights[str(r["chain"])] = chain_weights.get(str(r["chain"]), 0.0) + float(r["weight_pct"] or 0)

    max_concentration = _num(data.get("max_concentration_pct"), 35.0) or 35.0
    market_shock = abs(_num(data.get("market_shock_pct"), 30.0) or 30.0)
    depeg_shock = abs(_num(data.get("stablecoin_depeg_pct"), 10.0) or 10.0)
    nonstable_weight = 100.0 - stable_weight
    market_scenario_loss_pct = nonstable_weight / 100 * market_shock
    depeg_scenario_loss_pct = stable_weight / 100 * depeg_shock

    violations: list[str] = []
    warnings: list[str] = []
    mitigations: list[str] = []
    if largest > max_concentration:
        violations.append(f"Largest allocation {largest:.1f}% exceeds configured maximum {max_concentration:.1f}%.")
        warnings.append("Treasury concentration exceeds the configured policy limit.")
        mitigations.append("Reduce the largest allocation or diversify across independently validated exposures.")
    if stable_weight >= 70:
        warnings.append("Stablecoin exposure is highly concentrated as a treasury category; issuer and depeg dependencies require decomposition by asset.")
    if protocol_weights and max(protocol_weights.values()) > max_concentration:
        warnings.append("Protocol concentration exceeds the configured allocation threshold.")
    if chain_weights and max(chain_weights.values()) > 60:
        warnings.append("A majority of treasury exposure is concentrated on one chain.")

    risk = 15.0 + min(45.0, largest * 0.55) + min(20.0, hhi * 35)
    if violations:
        risk += 12
    if stable_weight >= 70:
        risk += 8
    risk = min(100.0, risk)

    evidence: list[EvidenceRecord] = []
    market_freshness, market_age, market_observed = _price_freshness(prices, ids) if call else (FreshnessStatus.UNKNOWN, None, datetime.now(timezone.utc))
    if call:
        now = datetime.now(timezone.utc)
        evidence.append(EvidenceRecord(
            evidence_id=str(uuid4()),
            provider="coingecko",
            source_type="market_reference",
            provider_endpoint=call.endpoint,
            provider_request_id=call.request_id,
            retrieved_at=now,
            observed_at=market_observed,
            normalized_value={cid: {"usd": (prices.get(cid) or {}).get("usd"), "last_updated_at": (prices.get(cid) or {}).get("last_updated_at")} for cid in ids},
            confidence=72,
            freshness=market_freshness,
            license_classification="external-provider-attributed",
        ))

    provider_status=[{"provider_id": call.provider_id, "status": "HEALTHY", "latency_ms": call.latency_ms}] if call else []
    assumptions=[f"Broad market shock is modeled as -{market_shock:.1f}% on non-stablecoin allocation weights.", f"Stablecoin depeg scenario is modeled as -{depeg_shock:.1f}% on allocations explicitly marked stablecoin=true."]
    native_metrics=[]
    native_inputs=[]
    if has_protocol_native_input(data):
        native_inputs.append(data)
    checks=data.get("protocol_native_checks")
    if isinstance(checks,list):
        native_inputs.extend(x for x in checks[:10] if isinstance(x,dict) and has_protocol_native_input(x))
    native_risk_delta=0.0
    native_confidence=0.0
    for native_input in native_inputs:
        try:
            native=collect_protocol_native(native_input)
            native_metrics.append(native.metrics)
            evidence.extend(native.evidence)
            provider_status.extend(native.provider_status)
            warnings.extend(native.warnings)
            assumptions.extend(native.assumptions)
            native_risk_delta+=native.risk_delta
            native_confidence=max(native_confidence,native.confidence)
        except (ValueError,ProviderError) as exc:
            warnings.append(f"Treasury protocol-native evidence could not be collected for one declared exposure: {exc}")
    if native_metrics:
        risk=min(100.0,risk+min(25.0,native_risk_delta))

    data_conf = (72 if market_freshness in {FreshnessStatus.LIVE, FreshnessStatus.CURRENT} else 64 if call and ids else 48)
    if native_metrics:
        data_conf=min(92,max(data_conf+8,native_confidence))
    return EngineResult(
        engine_id=EngineId.F5,
        engine_version="1.2.0",
        status=AnalysisStatus.PARTIAL,
        risk_score=risk,
        data_confidence=data_conf,
        engine_confidence=68,
        severity=_severity(risk),
        summary=f"Treasury allocation screening identifies a {largest:.1f}% largest exposure and {market_scenario_loss_pct:.1f}% modeled loss under the configured broad market shock. Dependency-level evidence remains incomplete.",
        metrics={
            "capital_usd": capital,
            "allocations": normalized,
            "largest_allocation_pct": largest,
            "concentration_hhi": hhi,
            "stablecoin_weight_pct": stable_weight,
            "protocol_weights_pct": protocol_weights,
            "chain_weights_pct": chain_weights,
            "scenario_losses_pct": {
                "broad_market_shock": market_scenario_loss_pct,
                "stablecoin_depeg": depeg_scenario_loss_pct,
            },
            "policy_violations": violations,
            "protocol_native_checks": native_metrics,
        },
        signals=[{"type": "policy_violation", "detail": v} for v in violations],
        warnings=warnings,
        mitigations=mitigations,
        safer_alternatives=mitigations[:],
        evidence=evidence,
        provider_consensus="SINGLE SOURCE" if evidence else "USER_INPUT_ONLY",
        data_freshness={"status": market_freshness.value if evidence else "UNKNOWN", "provider": "coingecko" if evidence else None, "age_seconds": market_age},
        missing_data=[
            "independent protocol and smart-contract risk for each deployment",
            "bridge and cross-chain dependency risk where applicable",
            "asset-specific liquidity/depth and liquidation capacity",
            "issuer/counterparty decomposition for stablecoin exposures",
            "correlation and contagion calibration for institutional stress testing",
        ],
        provider_status=provider_status,
        assumptions=assumptions,
        demo=False,
    )
