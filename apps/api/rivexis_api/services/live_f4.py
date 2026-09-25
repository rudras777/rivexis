from __future__ import annotations

from datetime import datetime, timezone
from math import isfinite
from uuid import uuid4

from rivexis_api.models.engine import EngineResult
from rivexis_api.models.enums import AnalysisStatus, EngineId, FreshnessStatus, Severity
from rivexis_api.models.evidence import EvidenceRecord
from rivexis_api.provider_clients import DefiLlamaYieldClient, ProviderError
from rivexis_api.services.protocol_native import collect_protocol_native, has_protocol_native_input

MAX_POOL_ROWS = 50_000
MAX_SELECTOR_LENGTH = 256
MIN_PROVIDER_TIMESTAMP = 946684800  # 2000-01-01 UTC


def _bounded_text(value, *, maximum=MAX_SELECTOR_LENGTH):
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized if normalized and len(normalized) <= maximum else None


def _num(value, default=None):
    try:
        if value in (None, "") or isinstance(value, bool):
            return default
        parsed = float(value)
        return parsed if isfinite(parsed) else default
    except (TypeError, ValueError, OverflowError):
        return default


def _observed_freshness(value):
    now = datetime.now(timezone.utc)
    if value in (None, "") or isinstance(value, bool):
        return now, FreshnessStatus.UNKNOWN, None
    dt = None
    try:
        if isinstance(value, (int, float)) or (
            isinstance(value, str) and value.isdigit()
        ):
            parsed = float(value)
            if not isfinite(parsed) or parsed < MIN_PROVIDER_TIMESTAMP:
                return now, FreshnessStatus.UNKNOWN, None
            dt = datetime.fromtimestamp(parsed, tz=timezone.utc)
        else:
            dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError, OSError, OverflowError):
        return now, FreshnessStatus.UNKNOWN, None

    if dt.timestamp() < MIN_PROVIDER_TIMESTAMP:
        return now, FreshnessStatus.UNKNOWN, None
    if (dt - now).total_seconds() > 300:
        return now, FreshnessStatus.UNKNOWN, None

    age = max(0.0, (now - dt).total_seconds())
    status = (
        FreshnessStatus.CURRENT
        if age <= 900
        else FreshnessStatus.RECENT
        if age <= 7200
        else FreshnessStatus.STALE
        if age <= 86400
        else FreshnessStatus.EXPIRED
    )
    return dt, status, age


def _severity(score: float) -> Severity:
    if score >= 80:
        return Severity.CRITICAL
    if score >= 60:
        return Severity.HIGH
    if score >= 35:
        return Severity.MODERATE
    return Severity.LOW


def _matching_pools(rows: list[dict], data: dict) -> list[dict]:
    pool_id = (_bounded_text(data.get("pool_id")) or "").lower()
    project = (_bounded_text(data.get("protocol") or data.get("project")) or "").lower()
    symbol = (_bounded_text(data.get("asset") or data.get("symbol")) or "").lower()
    chain = (_bounded_text(data.get("chain")) or "").lower()

    if pool_id:
        return [row for row in rows if (_bounded_text(row.get("pool")) or "").lower() == pool_id]

    candidates = rows
    if project:
        candidates = [row for row in candidates if _selector_matches(row.get("project"), project)]
    if symbol:
        candidates = [row for row in candidates if _selector_matches(row.get("symbol"), symbol)]
    if chain:
        candidates = [row for row in candidates if chain == (_bounded_text(row.get("chain")) or "").lower()]
    return candidates


def _selector_matches(observed, requested: str) -> bool:
    value = (_bounded_text(observed) or "").lower()
    return value == requested or any(
        value.startswith(requested + separator) for separator in ("-", "_", " ")
    )


def _invalid_pool_identity(call, pool: dict) -> EngineResult:
    return EngineResult(
        engine_id=EngineId.F4,
        engine_version="1.2.0",
        status=AnalysisStatus.INSUFFICIENT_DATA,
        risk_score=0,
        data_confidence=20,
        engine_confidence=0,
        severity=Severity.UNKNOWN,
        summary="The selected yield pool lacks bounded canonical identity fields; Rivexis did not score it.",
        warnings=["Pool, project, chain and symbol must be non-empty bounded strings."],
        missing_data=["canonical yield-pool identity"],
        provider_consensus="UNAVAILABLE",
        provider_status=[{"provider_id": call.provider_id, "status": "MALFORMED_POOL_IDENTITY", "latency_ms": call.latency_ms}],
        demo=False,
    )


def _insufficient_selector(call, matches: list[dict]) -> EngineResult:
    candidate_ids = [pool_id for row in matches[:20] if (pool_id := _bounded_text(row.get("pool"))) is not None]
    return EngineResult(
        engine_id=EngineId.F4,
        engine_version="1.2.0",
        status=AnalysisStatus.INSUFFICIENT_DATA,
        risk_score=0,
        data_confidence=35,
        engine_confidence=0,
        severity=Severity.UNKNOWN,
        summary=f"The supplied F4 selector matched {len(matches)} current DefiLlama yield pools. Rivexis did not silently choose one strategy by TVL.",
        metrics={"matching_pool_count": len(matches), "candidate_pool_ids": candidate_ids},
        warnings=["Provide pool_id, or make protocol/project + asset/symbol + chain specific enough to identify exactly one pool."],
        missing_data=["unique yield-pool selector"],
        provider_consensus="UNAVAILABLE",
        provider_status=[{"provider_id": call.provider_id, "status": "HEALTHY", "latency_ms": call.latency_ms}],
        demo=False,
    )


def _invalid_pool_metric(call, pool: dict, field: str) -> EngineResult:
    return EngineResult(
        engine_id=EngineId.F4,
        engine_version="1.2.0",
        status=AnalysisStatus.INSUFFICIENT_DATA,
        risk_score=0,
        data_confidence=30,
        engine_confidence=0,
        severity=Severity.UNKNOWN,
        summary=f"The selected yield pool does not contain a usable finite {field} value; Rivexis did not substitute zero for missing or non-finite provider data.",
        metrics={"pool_id": pool.get("pool"), "project": pool.get("project"), "chain": pool.get("chain"), "symbol": pool.get("symbol")},
        warnings=["No yield-risk score was produced from malformed core pool metrics."],
        missing_data=[f"finite {field}"],
        provider_consensus="UNAVAILABLE",
        provider_status=[{"provider_id": call.provider_id, "status": "MALFORMED_POOL_METRICS", "latency_ms": call.latency_ms}],
        demo=False,
    )


def _conflicting_optional_metric(call, pool: dict, field: str, detail: str) -> EngineResult:
    return EngineResult(
        engine_id=EngineId.F4,
        engine_version="1.2.0",
        status=AnalysisStatus.CONFLICTING_DATA,
        risk_score=0,
        data_confidence=25,
        engine_confidence=0,
        severity=Severity.UNKNOWN,
        summary=f"The selected yield pool contains internally invalid {field} metadata. Rivexis discarded strategy scoring instead of normalizing the contradiction away.",
        metrics={"pool_id": pool.get("pool"), "project": pool.get("project"), "chain": pool.get("chain"), "symbol": pool.get("symbol"), "invalid_field": field, "invalid_value": pool.get(field)},
        warnings=[detail],
        missing_data=[f"internally consistent {field}"],
        provider_consensus="CONFLICTING",
        provider_status=[{"provider_id": call.provider_id, "status": "CONFLICTING_POOL_METRICS", "latency_ms": call.latency_ms}],
        demo=False,
    )


def run_live_f4(data: dict) -> EngineResult:
    if not any(data.get(k) for k in ("pool_id", "protocol", "project")):
        return EngineResult(engine_id=EngineId.F4, engine_version="1.2.0", status=AnalysisStatus.INSUFFICIENT_DATA, risk_score=0, data_confidence=0, engine_confidence=0, severity=Severity.UNKNOWN, summary="F4 requires a DefiLlama pool_id or protocol/project selector.", warnings=["No fabricated yield analysis was produced."], missing_data=["pool_id or protocol/project"], provider_consensus="UNAVAILABLE", demo=False)

    selector_fields = ("pool_id", "protocol", "project", "asset", "symbol", "chain")
    if any(data.get(key) not in (None, "") and _bounded_text(data.get(key)) is None for key in selector_fields):
        return EngineResult(engine_id=EngineId.F4, engine_version="1.2.0", status=AnalysisStatus.INSUFFICIENT_DATA, risk_score=0, data_confidence=0, engine_confidence=0, severity=Severity.UNKNOWN, summary="F4 selectors must be non-empty bounded strings.", warnings=["No provider request was made from malformed selector input."], missing_data=["valid bounded yield-pool selector"], provider_consensus="UNAVAILABLE", demo=False)

    try:
        call = DefiLlamaYieldClient().pools()
    except ProviderError as exc:
        return EngineResult(engine_id=EngineId.F4, engine_version="1.2.0", status=AnalysisStatus.PROVIDER_UNAVAILABLE, risk_score=0, data_confidence=0, engine_confidence=0, severity=Severity.UNKNOWN, summary="DefiLlama yield data is unavailable; Rivexis did not substitute synthetic APY data.", warnings=[str(exc)], missing_data=["current yield-pool evidence"], provider_consensus="UNAVAILABLE", provider_status=[{"provider_id": exc.provider_id, "status": exc.code}], demo=False)

    body = call.result if isinstance(call.result, dict) else {}
    rows = body.get("data") if isinstance(body, dict) else None
    if not isinstance(rows, list) or len(rows) > MAX_POOL_ROWS:
        return EngineResult(engine_id=EngineId.F4, engine_version="1.2.0", status=AnalysisStatus.PROVIDER_UNAVAILABLE, risk_score=0, data_confidence=0, engine_confidence=0, severity=Severity.UNKNOWN, summary="DefiLlama returned an unexpected yield payload.", warnings=["Provider response could not be normalized."], missing_data=["normalized yield-pool evidence"], provider_consensus="UNAVAILABLE", provider_status=[{"provider_id": call.provider_id, "status": "MALFORMED_RESPONSE"}], demo=False)

    matches = _matching_pools([row for row in rows if isinstance(row, dict)], data)
    if not matches:
        return EngineResult(engine_id=EngineId.F4, engine_version="1.2.0", status=AnalysisStatus.INSUFFICIENT_DATA, risk_score=0, data_confidence=30, engine_confidence=40, severity=Severity.UNKNOWN, summary="No current DefiLlama yield pool matched the supplied selector.", warnings=["Rivexis did not infer a pool from a missing match."], missing_data=["matching yield pool"], provider_consensus="UNAVAILABLE", provider_status=[{"provider_id": call.provider_id, "status": "HEALTHY", "latency_ms": call.latency_ms}], demo=False)
    if len(matches) != 1:
        return _insufficient_selector(call, matches)
    pool = matches[0]
    identity = {
        field: _bounded_text(pool.get(field))
        for field in ("pool", "project", "chain", "symbol")
    }
    if any(value is None for value in identity.values()):
        return _invalid_pool_identity(call, pool)

    apy = _num(pool.get("apy"))
    if apy is None:
        return _invalid_pool_metric(call, pool, "apy")
    tvl = _num(pool.get("tvlUsd"))
    if tvl is None or tvl < 0:
        return _invalid_pool_metric(call, pool, "tvlUsd")
    apy_base = _num(pool.get("apyBase"))
    apy_reward = _num(pool.get("apyReward"))
    sigma = _num(pool.get("sigma"))
    il_7d = _num(pool.get("il7d"))
    apy_mean_30d = _num(pool.get("apyMean30d"))

    if pool.get("apyReward") not in (None, "") and apy_reward is None:
        return _conflicting_optional_metric(call, pool, "apyReward", "Reward APY was present but was not a finite numeric value.")
    if apy_reward is not None and apy_reward < 0:
        return _conflicting_optional_metric(call, pool, "apyReward", "Reward APY cannot be negative when used as an incentive-dependency component.")
    if apy >= 0 and apy_reward is not None and apy_reward > apy:
        return _conflicting_optional_metric(call, pool, "apyReward", "Reward APY exceeded the reported headline APY; Rivexis will not clamp the ratio and continue scoring.")
    if pool.get("sigma") not in (None, "") and sigma is None:
        return _conflicting_optional_metric(call, pool, "sigma", "Yield sigma was present but was not a finite numeric value.")
    if sigma is not None and sigma < 0:
        return _conflicting_optional_metric(call, pool, "sigma", "Yield sigma is a dispersion magnitude and cannot be negative.")
    for field, value in (
        ("apyBase", apy_base),
        ("il7d", il_7d),
        ("apyMean30d", apy_mean_30d),
    ):
        if pool.get(field) not in (None, "") and value is None:
            return _conflicting_optional_metric(
                call,
                pool,
                field,
                f"{field} was present but was not a finite non-boolean numeric value.",
            )

    reward_share = None
    if apy > 0 and apy_reward is not None:
        reward_share = apy_reward / apy

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

    mitigations.extend(["Validate smart-contract, oracle, governance and dependency risk before capital deployment.", "Model principal drawdown and withdrawal liquidity separately from headline APY."])

    retrieved = datetime.now(timezone.utc)
    observed, freshness, age_seconds = _observed_freshness(pool.get("timestamp"))
    evidence = EvidenceRecord(evidence_id=str(uuid4()), provider="defillama_yields", source_type="external_yield_data", provider_endpoint=call.endpoint, provider_request_id=call.request_id, retrieved_at=retrieved, observed_at=observed, protocol_id=identity["project"], asset_id=identity["symbol"], raw_reference=identity["pool"], normalized_value={"pool_id": identity["pool"], "project": identity["project"], "chain": identity["chain"], "symbol": identity["symbol"], "tvl_usd": tvl, "apy": apy, "apy_base": apy_base, "apy_reward": apy_reward}, calculation_version="f4-live-1.3.0", engine_version="1.2.0", confidence=70, freshness=freshness, license_classification="external-provider-attributed")

    metrics = {"pool_id": identity["pool"], "project": identity["project"], "chain": identity["chain"], "symbol": identity["symbol"], "tvl_usd": tvl, "headline_apy_pct": apy, "base_apy_pct": apy_base, "reward_apy_pct": apy_reward, "reward_share": reward_share, "apy_mean_30d_pct": apy_mean_30d, "yield_sigma": sigma, "impermanent_loss_7d_pct": il_7d}
    all_evidence = [evidence]
    provider_status = [{"provider_id": call.provider_id, "status": "HEALTHY", "latency_ms": call.latency_ms}]
    assumptions = ["DefiLlama yield data is external evidence and is not a Rivexis endorsement or independently verified APY.", "If the provider payload omits an observation timestamp, Rivexis records freshness as UNKNOWN rather than equating retrieval time with observation time."]
    missing = ["protocol-native contract state and withdrawal constraints", "independent smart-contract/security evidence", "oracle and dependency validation", "historical yield stability beyond provider summary metrics where needed"]
    data_conf = {
        FreshnessStatus.CURRENT: 70,
        FreshnessStatus.RECENT: 70,
        FreshnessStatus.STALE: 55,
        FreshnessStatus.EXPIRED: 45,
        FreshnessStatus.UNKNOWN: 62,
    }.get(freshness, 62)
    engine_conf = 62.0
    if has_protocol_native_input(data):
        try:
            native = collect_protocol_native(data)
            metrics["protocol_native"] = native.metrics
            all_evidence.extend(native.evidence)
            provider_status.extend(native.provider_status)
            warnings.extend(native.warnings)
            assumptions.extend(native.assumptions)
            missing.extend(native.missing_data)
            risk = min(100.0, risk + native.risk_delta)
            if native.evidence:
                data_conf = min(92.0, max(float(data_conf), native.confidence))
                engine_conf = min(84.0, engine_conf + 10)
            contracts = native.metrics.get("declared_contracts") if isinstance(native.metrics, dict) else []
            if any(isinstance(item, dict) and "has_code" in item for item in (contracts or [])):
                missing = [item for item in missing if item != "protocol-native contract state and withdrawal constraints"]
                missing.append("withdrawal constraints and strategy semantics beyond declared contract state")
            declared_oracle = native.metrics.get("declared_oracle") if isinstance(native.metrics, dict) else None
            if isinstance(declared_oracle, dict):
                missing = [item for item in missing if item != "oracle and dependency validation"]
                missing.append("independent verification of declared oracle/dependency authority")
                if declared_oracle.get("freshness") == FreshnessStatus.UNKNOWN.value:
                    missing.append("credible declared-oracle observation timestamp")
        except (ValueError, ProviderError) as exc:
            warnings.append(f"Protocol-native yield dependency evidence could not be collected: {exc}")
            missing.append("protocol-native yield dependency evidence")

    evidence_freshness = {item.freshness for item in all_evidence}
    if FreshnessStatus.EXPIRED in evidence_freshness:
        overall_freshness = FreshnessStatus.EXPIRED
    elif FreshnessStatus.STALE in evidence_freshness:
        overall_freshness = FreshnessStatus.STALE
    elif FreshnessStatus.UNKNOWN in evidence_freshness:
        overall_freshness = FreshnessStatus.UNKNOWN
    elif FreshnessStatus.RECENT in evidence_freshness:
        overall_freshness = FreshnessStatus.RECENT
    elif FreshnessStatus.CURRENT in evidence_freshness:
        overall_freshness = FreshnessStatus.CURRENT
    else:
        overall_freshness = FreshnessStatus.LIVE
    if overall_freshness in {FreshnessStatus.STALE, FreshnessStatus.EXPIRED}:
        warnings.append("Retained yield or protocol-native evidence is stale; refresh the affected evidence before strategy decisioning.")
    consensus = "MULTI_SOURCE" if len({item.provider for item in all_evidence}) > 1 else "SINGLE_SOURCE"
    status = AnalysisStatus.STALE_DATA if overall_freshness in {FreshnessStatus.STALE, FreshnessStatus.EXPIRED} else AnalysisStatus.PARTIAL
    return EngineResult(engine_id=EngineId.F4, engine_version="1.2.0", status=status, risk_score=risk, data_confidence=data_conf, engine_confidence=engine_conf, severity=_severity(risk), summary=f"Current attributed yield evidence found for {identity['project']} / {identity['symbol']}: {apy:.2f}% headline APY. Protocol-native evidence was incorporated when declared; unresolved principal-risk gaps remain explicit.", metrics=metrics, signals=signals, warnings=warnings, mitigations=mitigations, safer_alternatives=mitigations[:1], evidence=all_evidence, provider_consensus=consensus, data_freshness={"status": overall_freshness.value, "provider": "multi-source" if consensus == "MULTI_SOURCE" else "defillama_yields", "age_seconds": age_seconds, "provider_timestamp_present": age_seconds is not None, "evidence_freshness": sorted(item.value for item in evidence_freshness)}, missing_data=sorted(set(missing)), provider_status=provider_status, assumptions=assumptions, demo=False)
