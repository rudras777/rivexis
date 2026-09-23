from __future__ import annotations

from datetime import datetime, timezone
from math import isfinite
from typing import Any
from uuid import uuid4

from rivexis_api.models.engine import EngineResult
from rivexis_api.models.enums import AnalysisStatus, EngineId, FreshnessStatus, Severity
from rivexis_api.models.evidence import EvidenceRecord
from rivexis_api.provider_clients import DefiLlamaClient, ProviderCall, ProviderError
from rivexis_api.services.protocol_native import collect_protocol_native, has_protocol_native_input


def _finite_float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        parsed = float(value)
        return parsed if isfinite(parsed) else None
    except (TypeError, ValueError):
        return None


def _parse_observed_at(value: Any) -> datetime | None:
    parsed = _finite_float(value)
    if parsed is None:
        return None
    # DefiLlama TVL history uses unix seconds. Reject obviously non-production fixture/
    # corrupt epochs rather than presenting them as centuries-old live evidence.
    if parsed < 946684800:  # 2000-01-01 UTC
        return None
    try:
        observed = datetime.fromtimestamp(parsed, tz=timezone.utc)
    except (ValueError, OSError, OverflowError):
        return None
    now = datetime.now(timezone.utc)
    if (observed - now).total_seconds() > 300:
        return None
    return observed


def _freshness(observed: datetime | None) -> tuple[FreshnessStatus, float | None]:
    if observed is None:
        return FreshnessStatus.UNKNOWN, None
    age = max(0.0, (datetime.now(timezone.utc) - observed).total_seconds())
    # Protocol TVL history is not a block-by-block feed; use day-scale thresholds.
    if age <= 36 * 3600:
        return FreshnessStatus.CURRENT, age
    if age <= 72 * 3600:
        return FreshnessStatus.RECENT, age
    if age <= 7 * 86400:
        return FreshnessStatus.STALE, age
    return FreshnessStatus.EXPIRED, age


def _latest_tvl_point(body: dict[str, Any]) -> tuple[float | None, datetime | None, bool]:
    """Return (tvl, observed_at, malformed_core_value)."""
    series = body.get("tvl")
    if isinstance(series, list):
        for row in reversed(series):
            if not isinstance(row, dict) or row.get("totalLiquidityUSD") is None:
                continue
            value = _finite_float(row.get("totalLiquidityUSD"))
            if value is None or value < 0:
                return None, None, True
            return value, _parse_observed_at(row.get("date")), False

    value = body.get("tvl")
    if value is not None and not isinstance(value, list):
        parsed = _finite_float(value)
        if parsed is None or parsed < 0:
            return None, None, True
        return parsed, None, False

    chain_tvls = body.get("currentChainTvls")
    if isinstance(chain_tvls, dict):
        values: list[float] = []
        for key, raw in chain_tvls.items():
            lowered = str(key).lower()
            if "-borrowed" in lowered or "-staking" in lowered or "-pool2" in lowered:
                continue
            if raw is None:
                continue
            parsed = _finite_float(raw)
            if parsed is None or parsed < 0:
                return None, None, True
            values.append(parsed)
        if values:
            return sum(values), None, False
    return None, None, False


def _evidence(
    call: ProviderCall,
    normalized: Any,
    *,
    observed_at: datetime | None,
    freshness: FreshnessStatus,
) -> EvidenceRecord:
    retrieved = datetime.now(timezone.utc)
    return EvidenceRecord(
        evidence_id=str(uuid4()),
        provider="defillama",
        source_type="analytical_enriched_data",
        provider_endpoint="GET /protocol/{slug}",
        provider_request_id=call.request_id,
        retrieved_at=retrieved,
        # EvidenceRecord currently requires a datetime. When provider observation time is
        # absent, retain retrieval time only as a schema fallback while freshness stays UNKNOWN.
        observed_at=observed_at or retrieved,
        raw_reference=f"provider:defillama;request:{call.request_id}",
        normalized_value=normalized,
        calculation_version="f2-live-1.2.0",
        engine_version="1.2.0",
        confidence=86 if freshness in {FreshnessStatus.CURRENT, FreshnessStatus.RECENT} else 70,
        freshness=freshness,
        license_classification="external-provider-evidence",
    )


def _severity(score: float) -> Severity:
    if score >= 80:
        return Severity.CRITICAL
    if score >= 60:
        return Severity.HIGH
    if score >= 35:
        return Severity.MODERATE
    return Severity.LOW


def _provider_payload_failure(call: ProviderCall, message: str, missing: str) -> EngineResult:
    return EngineResult(
        engine_id=EngineId.F2,
        engine_version="1.2.0",
        status=AnalysisStatus.INSUFFICIENT_DATA,
        risk_score=0,
        data_confidence=20,
        engine_confidence=0,
        severity=Severity.UNKNOWN,
        summary=message,
        warnings=["No protocol risk score was produced from an unusable provider record."],
        missing_data=[missing],
        provider_consensus="UNAVAILABLE",
        provider_status=[
            {
                "provider_id": call.provider_id,
                "status": "MALFORMED_PROTOCOL_RECORD",
                "latency_ms": round(call.latency_ms, 2),
            }
        ],
        demo=False,
    )


def run_live_f2(input_data: dict[str, Any]) -> EngineResult:
    slug = str(input_data.get("protocol") or input_data.get("slug") or "").strip().lower()
    if not slug:
        return _fail("F2 live analysis requires a DefiLlama protocol slug")

    try:
        call = DefiLlamaClient().protocol(slug)
    except ProviderError as exc:
        return EngineResult(
            engine_id=EngineId.F2,
            engine_version="1.2.0",
            status=AnalysisStatus.PROVIDER_UNAVAILABLE,
            risk_score=0,
            data_confidence=0,
            engine_confidence=0,
            severity=Severity.UNKNOWN,
            summary="Protocol metrics provider is unavailable; no protocol risk score was fabricated.",
            warnings=[f"{exc.code}: {exc}"],
            missing_data=["protocol metrics"],
            provider_consensus="UNAVAILABLE",
            provider_status=[
                {
                    "provider_id": "defillama",
                    "status": "UNAVAILABLE",
                    "detail": f"{exc.code}: {exc}",
                }
            ],
            demo=False,
        )

    if not isinstance(call.result, dict):
        return _provider_payload_failure(
            call,
            "DefiLlama returned a non-object protocol record; Rivexis did not score it.",
            "normalized protocol record",
        )
    body = call.result
    name_raw = body.get("name")
    if not isinstance(name_raw, str) or not name_raw.strip():
        return _provider_payload_failure(
            call,
            "DefiLlama returned a protocol record without a usable protocol identity; Rivexis did not score it.",
            "protocol identity",
        )
    name = name_raw.strip()

    latest_fetch_ok = body.get("latestFetchIsOk")
    if latest_fetch_ok is not None and not isinstance(latest_fetch_ok, bool):
        return _provider_payload_failure(
            call,
            "DefiLlama returned malformed latest-fetch health metadata; Rivexis did not infer provider health from string/number truthiness.",
            "boolean latestFetchIsOk metadata",
        )

    tvl, tvl_observed_at, malformed_tvl = _latest_tvl_point(body)
    if malformed_tvl:
        return _provider_payload_failure(
            call,
            "DefiLlama returned a missing, negative, or non-finite core TVL value; Rivexis did not substitute zero or score the record.",
            "finite non-negative protocol TVL",
        )

    freshness, freshness_age = _freshness(tvl_observed_at)
    chains = (
        [str(item).strip() for item in body.get("chains", []) if isinstance(item, str) and item.strip()]
        if isinstance(body.get("chains"), list)
        else []
    )
    audit_links = body.get("audit_links") if isinstance(body.get("audit_links"), list) else []
    audits = body.get("audits")
    try:
        audit_count = int(audits) if audits not in (None, "") else len(audit_links)
    except (TypeError, ValueError):
        audit_count = len(audit_links)
    if audit_count < 0:
        audit_count = 0

    normalized = {
        "slug": slug,
        "name": name,
        "category": body.get("category"),
        "tvl_usd": tvl,
        "tvl_observed_at": tvl_observed_at.isoformat() if tvl_observed_at else None,
        "chains": chains,
        "audit_count": audit_count,
        "audit_links_count": len(audit_links),
        "oracles": body.get("oracles"),
        "latest_fetch_ok": latest_fetch_ok,
    }

    score = 20.0
    warnings: list[str] = []
    if tvl is None:
        warnings.append("Current TVL could not be normalized from the provider response.")
    elif tvl < 1_000_000:
        score += 25
        warnings.append("Observed TVL is below $1M; economic/liquidity resilience requires deeper review.")
    elif tvl < 10_000_000:
        score += 15
    if audit_count == 0:
        score += 15
        warnings.append("No audit evidence was present in the normalized DefiLlama record.")
    if len(chains) == 1:
        score += 5
    if latest_fetch_ok is False:
        score += 20
        warnings.append("Provider indicates the latest protocol fetch is not healthy; refresh fundamentals before decisioning.")
    if freshness in {FreshnessStatus.STALE, FreshnessStatus.EXPIRED}:
        warnings.append("The latest timestamped TVL observation is stale; refresh protocol fundamentals before decisioning.")

    missing = [
        "direct smart-contract state and upgrade/admin privilege analysis",
        "independent exploit/security intelligence",
        "protocol-native oracle configuration and freshness",
        "governance concentration/timelock analysis",
        "liquidity depth and liquidation mechanics",
        "independent external risk evidence",
    ]
    evidence = [
        _evidence(
            call,
            normalized,
            observed_at=tvl_observed_at,
            freshness=freshness,
        )
    ]
    provider_status = [
        {
            "provider_id": "defillama",
            "status": "DEGRADED" if latest_fetch_ok is False else "HEALTHY",
            "latency_ms": round(call.latency_ms, 2),
        }
    ]
    assumptions = [
        "DefiLlama metrics are external analytical evidence and are not treated as Rivexis-owned direct chain state.",
        "When the provider record lacks a usable observation timestamp, evidence freshness is UNKNOWN; retrieval time is not treated as proof of observation time.",
    ]
    data_conf = 74.0 if freshness in {FreshnessStatus.CURRENT, FreshnessStatus.RECENT} else 62.0
    if latest_fetch_ok is False:
        data_conf = min(data_conf, 50.0)
    engine_conf = 65.0

    if has_protocol_native_input(input_data):
        try:
            native = collect_protocol_native(input_data)
            normalized["protocol_native"] = native.metrics
            evidence.extend(native.evidence)
            provider_status.extend(native.provider_status)
            warnings.extend(native.warnings)
            assumptions.extend(native.assumptions)
            missing.extend(native.missing_data)
            score = min(100.0, score + native.risk_delta)
            data_conf = min(94.0, max(data_conf, native.confidence))
            engine_conf = min(88.0, engine_conf + 10)
            contracts = native.metrics.get("declared_contracts") if isinstance(native.metrics, dict) else []
            if contracts:
                missing = [
                    item
                    for item in missing
                    if item != "direct smart-contract state and upgrade/admin privilege analysis"
                ]
            roles = {str(item.get("role")) for item in contracts if isinstance(item, dict)}
            if "governance" in roles:
                missing = [item for item in missing if item != "governance concentration/timelock analysis"]
                missing.append("governance concentration/timelock semantics beyond declared governance contract state")
            if native.metrics.get("declared_oracle"):
                missing = [
                    item
                    for item in missing
                    if item != "protocol-native oracle configuration and freshness"
                ]
                missing.append("independent verification that the declared oracle is authoritative for the selected protocol/market")
        except (ValueError, ProviderError) as exc:
            warnings.append(f"Protocol-native evidence could not be collected: {exc}")
            missing.append("protocol-native evidence collection")

    consensus = "MULTI_SOURCE" if len({item.provider for item in evidence}) > 1 else "SINGLE_SOURCE"
    stale_gate = latest_fetch_ok is False or freshness in {FreshnessStatus.STALE, FreshnessStatus.EXPIRED}
    status = AnalysisStatus.STALE_DATA if stale_gate else AnalysisStatus.PARTIAL
    overall_freshness = (
        FreshnessStatus.STALE
        if latest_fetch_ok is False and freshness not in {FreshnessStatus.STALE, FreshnessStatus.EXPIRED}
        else freshness
    )
    summary = (
        "F2 combined attributed protocol fundamentals with caller-declared direct contract/oracle evidence. Remaining gaps are preserved explicitly."
        if len(evidence) > 1
        else "F2 normalized live protocol fundamentals from DefiLlama. Direct security, oracle, governance and liquidity evidence remains incomplete."
    )
    return EngineResult(
        engine_id=EngineId.F2,
        engine_version="1.2.0",
        status=status,
        risk_score=min(100.0, score),
        data_confidence=data_conf,
        engine_confidence=engine_conf,
        severity=_severity(score),
        summary=summary,
        metrics=normalized,
        warnings=warnings,
        mitigations=[
            "Do not deploy material capital until unresolved contract, oracle, governance and security evidence is independently validated."
        ],
        safer_alternatives=[
            "Use this result as a screening layer, then run the remaining protocol-native and security checks before allocation."
        ],
        evidence=evidence,
        provider_consensus=consensus,
        data_freshness={
            "status": overall_freshness.value,
            "provider": "multi-source" if consensus == "MULTI_SOURCE" else "defillama",
            "age_seconds": freshness_age,
            "provider_observation_timestamp_present": tvl_observed_at is not None,
            "latest_fetch_ok": latest_fetch_ok,
        },
        missing_data=sorted(set(missing)),
        provider_status=provider_status,
        assumptions=assumptions,
        demo=False,
    )


def _fail(message: str) -> EngineResult:
    return EngineResult(
        engine_id=EngineId.F2,
        engine_version="1.2.0",
        status=AnalysisStatus.INSUFFICIENT_DATA,
        risk_score=0,
        data_confidence=0,
        engine_confidence=0,
        severity=Severity.UNKNOWN,
        summary=message,
        warnings=["No protocol metric or risk score was fabricated."],
        missing_data=["valid protocol slug"],
        provider_consensus="UNAVAILABLE",
        demo=False,
    )
