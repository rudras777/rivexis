from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from rivexis_api.models.engine import EngineResult
from rivexis_api.models.enums import AnalysisStatus, EngineId, FreshnessStatus, Severity
from rivexis_api.models.evidence import EvidenceRecord
from rivexis_api.provider_clients import DefiLlamaYieldClient, ProviderError
from rivexis_api.services.protocol_native import collect_protocol_native, has_protocol_native_input


def _num(value, default=None):
    try:
        if value in (None, ""):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _observed_freshness(value):
    if value in (None, ""):
        return datetime.now(timezone.utc), FreshnessStatus.UNKNOWN, None
    dt = None
    try:
        if isinstance(value, (int, float)) or (isinstance(value, str) and value.isdigit()):
            dt = datetime.fromtimestamp(float(value), tz=timezone.utc)
        else:
            dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError, OSError):
        return datetime.now(timezone.utc), FreshnessStatus.UNKNOWN, None
    age = max(0.0, (datetime.now(timezone.utc) - dt).total_seconds())
    status = FreshnessStatus.CURRENT if age <= 900 else FreshnessStatus.RECENT if age <= 7200 else FreshnessStatus.STALE if age <= 86400 else FreshnessStatus.EXPIRED
    return dt, status, age


def _severity(score: float) -> Severity:
    if score >= 80:
        return Severity.CRITICAL
    if score >= 60:
        return Severity.HIGH
    if score >= 35:
        return Severity.MODERATE
    return Severity.LOW


def _match_pool(rows: list[dict], data: dict) -> dict | None:
    pool_id = str(data.get("pool_id") or "").strip().lower()
    project = str(data.get("protocol") or data.get("project") or "").strip().lower()
    symbol = str(data.get("asset") or data.get("symbol") or "").strip().lower()
    chain = str(data.get("chain") or "").strip().lower()

    if pool_id:
        for row in rows:
            if str(row.get("pool") or "").lower() == pool_id:
                return row
        return None

    candidates = rows
    if project:
        candidates = [r for r in candidates if project in str(r.get("project") or "").lower()]
    if symbol:
        candidates = [r for r in candidates if symbol in str(r.get("symbol") or "").lower()]
    if chain:
        candidates = [r for r in candidates if chain == str(r.get("chain") or "").lower()]
    if not candidates:
        return None

    # Deterministic selection: prefer the largest TVL among matching rows.
    return max(candidates, key=lambda r: _num(r.get("tvlUsd"), 0.0) or 0.0)


def run_live_f4(data: dict) -> EngineResult:
    if not any(data.get(k) for k in ("pool_id", "protocol", "project")):
        return EngineResult(
            engine_id=EngineId.F4,
            status=AnalysisStatus.INSUFFICIENT_DATA,
            risk_score=0,
            data_confidence=0,
            engine_confidence=0,
            severity=Severity.UNKNOWN,
            summary="F4 requires a DefiLlama pool_id or protocol/project selector.",
            warnings=["No fabricated yield analysis was produced."],
            missing_data=["pool_id or protocol/project"],
            provider_consensus="UNAVAILABLE",
            demo=False,
        )

    try:
        call = DefiLlamaYieldClient().pools()
    except ProviderError as exc:
        return EngineResult(
            engine_id=EngineId.F4,
            status=AnalysisStatus.PROVIDER_UNAVAILABLE,
            risk_score=0,
            data_confidence=0,
            engine_confidence=0,
            severity=Severity.UNKNOWN,
            summary="DefiLlama yield data is unavailable; Rivexis did not substitute synthetic APY data.",
            warnings=[str(exc)],
            missing_data=["current yield-pool evidence"],
            provider_consensus="UNAVAILABLE",
            provider_status=[{"provider_id": exc.provider_id, "status": exc.code}],
            demo=False,
        )

    body = call.result if isinstance(call.result, dict) else {}
    rows = body.get("data") if isinstance(body, dict) else None
    if not isinstance(rows, list):
        return EngineResult(
            engine_id=EngineId.F4,
            status=AnalysisStatus.PROVIDER_UNAVAILABLE,
            risk_score=0,
            data_confidence=0,
            engine_confidence=0,
            severity=Severity.UNKNOWN,
            summary="DefiLlama returned an unexpected yield payload.",
            warnings=["Provider response could not be normalized."],
            missing_data=["normalized yield-pool evidence"],
            provider_consensus="UNAVAILABLE",
            provider_status=[{"provider_id": call.provider_id, "status": "MALFORMED_RESPONSE"}],
            demo=False,
        )

    pool = _match_pool([r for r in rows if isinstance(r, dict)], data)
    if not pool:
        return EngineResult(
            engine_id=EngineId.F4,
            status=AnalysisStatus.INSUFFICIENT_DATA,
            risk_score=0,
            data_confidence=30,
            engine_confidence=40,
            severity=Severity.UNKNOWN,
            summary="No current DefiLlama yield pool matched the supplied selector.",
            warnings=["Rivexis did not infer a pool from an ambiguous or missing match."],
            missing_data=["matching yield pool"],
            provider_consensus="SINGLE SOURCE",
            provider_status=[{"provider_id": call.provider_id, "status": "HEALTHY", "latency_ms": call.latency_ms}],
            demo=False,
        )

    apy = _num(pool.get("apy"), 0.0) or 0.0
    apy_base = _num(pool.get("apyBase"))
    apy_reward = _num(pool.get("apyReward"))
    tvl = _num(pool.get("tvlUsd"), 0.0) or 0.0
    sigma = _num(pool.get("sigma"))
    il_7d = _num(pool.get("il7d"))
    apy_mean_30d = _num(pool.get("apyMean30d"))

    reward_share = None
    if apy > 0 and apy_reward is not None:
        reward_share = max(0.0, min(1.0, apy_reward / apy))

    # Conservative, transparent screening only. This is not a protocol safety score.
    risk = 20.0
    signals: list[dict] = []
    warnings: list[str] = []
    mitigations: list[str] = []
    if apy >= 30:
        risk += 20
        signals.append({"type": "high_headline_apy", "apy": apy})
        warnings.append("Headline APY is high and requires independent sustainability validation.")
    if reward_share is not None and reward_share >= 0.5:
        risk += 20
        signals.append({"type": "reward_dependency", "reward_share": reward_share})
        warnings.append("A material share of headline APY is reward/incentive dependent.")
    if tvl < 1_000_000:
        risk += 20
        signals.append({"type": "low_tvl", "tvl_usd": tvl})
        warnings.append("Pool TVL is below $1m; exit liquidity and capacity require deeper validation.")
    elif tvl < 10_000_000:
        risk += 10
    if sigma is not None and sigma > 0.1:
        risk += 10
        signals.append({"type": "yield_variability", "sigma": sigma})
    if il_7d is not None and il_7d < -1:
        risk += 10
        warnings.append("Recent impermanent-loss metric is material relative to yield and should be modeled separately.")
    risk = min(100.0, risk)

    mitigations.extend([
        "Validate smart-contract, oracle, governance and dependency risk before capital deployment.",
        "Model principal drawdown and withdrawal liquidity separately from headline APY.",
    ])

    retrieved = datetime.now(timezone.utc)
    observed, freshness, age_seconds = _observed_freshness(pool.get("timestamp"))
    evidence = EvidenceRecord(
        evidence_id=str(uuid4()),
        provider="defillama_yields",
        source_type="external_yield_data",
        provider_endpoint=call.endpoint,
        provider_request_id=call.request_id,
        retrieved_at=retrieved,
        observed_at=observed,
        protocol_id=str(pool.get("project") or "") or None,
        asset_id=str(pool.get("symbol") or "") or None,
        raw_reference=str(pool.get("pool") or "") or None,
        normalized_value={
            "pool_id": pool.get("pool"),
            "project": pool.get("project"),
            "chain": pool.get("chain"),
            "symbol": pool.get("symbol"),
            "tvl_usd": tvl,
            "apy": apy,
            "apy_base": apy_base,
            "apy_reward": apy_reward,
        },
        confidence=70,
        freshness=freshness,
        license_classification="external-provider-attributed",
    )

    metrics={
        "pool_id": pool.get("pool"),
        "project": pool.get("project"),
        "chain": pool.get("chain"),
        "symbol": pool.get("symbol"),
        "tvl_usd": tvl,
        "headline_apy_pct": apy,
        "base_apy_pct": apy_base,
        "reward_apy_pct": apy_reward,
        "reward_share": reward_share,
        "apy_mean_30d_pct": apy_mean_30d,
        "yield_sigma": sigma,
        "impermanent_loss_7d_pct": il_7d,
    }
    all_evidence=[evidence]
    provider_status=[{"provider_id": call.provider_id, "status": "HEALTHY", "latency_ms": call.latency_ms}]
    assumptions=["DefiLlama yield data is external evidence and is not a Rivexis endorsement or independently verified APY.", "If the provider payload omits an observation timestamp, Rivexis records freshness as UNKNOWN rather than equating retrieval time with observation time."]
    missing=["protocol-native contract state and withdrawal constraints","independent smart-contract/security evidence","oracle and dependency validation","historical yield stability beyond provider summary metrics where needed"]
    data_conf=70 if freshness != FreshnessStatus.UNKNOWN else 62
    engine_conf=62.0
    if has_protocol_native_input(data):
        try:
            native=collect_protocol_native(data)
            metrics["protocol_native"]=native.metrics
            all_evidence.extend(native.evidence)
            provider_status.extend(native.provider_status)
            warnings.extend(native.warnings)
            assumptions.extend(native.assumptions)
            missing.extend(native.missing_data)
            risk=min(100.0,risk+native.risk_delta)
            data_conf=min(92.0,max(float(data_conf),native.confidence))
            engine_conf=min(84.0,engine_conf+10)
            if native.metrics.get("declared_contracts"):
                missing=[x for x in missing if x!="protocol-native contract state and withdrawal constraints"]
                missing.append("withdrawal constraints and strategy semantics beyond declared contract state")
            if native.metrics.get("declared_oracle"):
                missing=[x for x in missing if x!="oracle and dependency validation"]
                missing.append("independent verification of declared oracle/dependency authority")
        except (ValueError,ProviderError) as exc:
            warnings.append(f"Protocol-native yield dependency evidence could not be collected: {exc}")
            missing.append("protocol-native yield dependency evidence")
    consensus="MULTI_SOURCE" if len({e.provider for e in all_evidence})>1 else "SINGLE_SOURCE"
    return EngineResult(
        engine_id=EngineId.F4,engine_version="1.2.0",status=AnalysisStatus.PARTIAL,risk_score=risk,data_confidence=data_conf,engine_confidence=engine_conf,severity=_severity(risk),
        summary=f"Current attributed yield evidence found for {pool.get('project') or 'protocol'} / {pool.get('symbol') or 'pool'}: {apy:.2f}% headline APY. Protocol-native evidence was incorporated when declared; unresolved principal-risk gaps remain explicit.",
        metrics=metrics,signals=signals,warnings=warnings,mitigations=mitigations,safer_alternatives=mitigations[:1],evidence=all_evidence,provider_consensus=consensus,
        data_freshness={"status": freshness.value, "provider": "multi-source" if consensus=="MULTI_SOURCE" else "defillama_yields", "age_seconds": age_seconds, "provider_timestamp_present": pool.get("timestamp") not in (None, "")},
        missing_data=sorted(set(missing)),provider_status=provider_status,assumptions=assumptions,demo=False,
    )
