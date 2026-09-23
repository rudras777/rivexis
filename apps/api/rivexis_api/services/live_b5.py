from __future__ import annotations

from datetime import datetime, timezone
import math
from typing import Any
from uuid import uuid4

from rivexis_api.chains import normalize_chain
from rivexis_api.models.engine import EngineResult
from rivexis_api.models.enums import AnalysisStatus, EngineId, FreshnessStatus, Severity
from rivexis_api.models.evidence import EvidenceRecord, SourceConflict
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
        calculation_version="b5-live-1.3.0",
        engine_version="1.2.0",
        confidence=90,
        freshness=FreshnessStatus.LIVE,
        license_classification="external-provider-evidence",
    )


def _sev(score: float) -> Severity:
    if score >= 80:
        return Severity.CRITICAL
    if score >= 60:
        return Severity.HIGH
    if score >= 35:
        return Severity.MODERATE
    return Severity.LOW


def _cost_total(items: object) -> tuple[float | None, bool]:
    """Normalize provider cost rows without treating malformed economics as zero/absent.

    An empty list is a valid observed zero-cost collection. Any malformed row, missing
    amountUSD, non-finite value or negative value makes the collection unusable so the
    caller can fail closed instead of presenting incomplete route economics.
    """
    if not isinstance(items, list):
        return None, False
    total = 0.0
    for item in items:
        if not isinstance(item, dict):
            return None, False
        value = item.get("amountUSD")
        if value in (None, "") or isinstance(value, bool):
            return None, False
        try:
            parsed = float(value)
        except (TypeError, ValueError, OverflowError):
            return None, False
        if not math.isfinite(parsed) or parsed < 0:
            return None, False
        total += parsed
        if not math.isfinite(total):
            return None, False
    return round(total, 6), True


def _duration_seconds(value: object) -> float | None:
    if isinstance(value, bool) or value in (None, ""):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    if not math.isfinite(parsed) or parsed < 0:
        return None
    return parsed


def _included_steps(value: object) -> tuple[list[dict[str, Any]], bool]:
    if not isinstance(value, list):
        return [], False
    rows: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict) or not item:
            return [], False
        rows.append(item)
    return rows, True


def _evm_address(value: object) -> str | None:
    raw = str(value or "").strip().lower()
    if len(raw) != 42 or not raw.startswith("0x"):
        return None
    try:
        int(raw[2:], 16)
    except ValueError:
        return None
    return raw


def _positive_integer(value: object) -> int | None:
    try:
        raw = str(value).strip()
        if not raw or raw.startswith(("+", "-")):
            return None
        parsed = int(raw, 10)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _token_matches(requested: object, observed: object) -> bool:
    if not isinstance(observed, dict):
        return False
    expected = str(requested or "").strip()
    expected_address = _evm_address(expected)
    if expected_address:
        observed_address = _evm_address(observed.get("address"))
        return observed_address == expected_address
    symbol = str(observed.get("symbol") or "").strip()
    coin_key = str(observed.get("coinKey") or "").strip()
    return bool(expected) and expected.casefold() in {symbol.casefold(), coin_key.casefold()}


def _conflict(metric: str, expected: object, observed: object) -> SourceConflict:
    return SourceConflict(
        metric=metric,
        source_a="requested_input",
        value_a=expected,
        source_b="lifi_quote",
        value_b=observed,
        severity="high",
        resolution_method="unresolved_quote_request_mismatch",
        resolution_confidence=0,
    )


def _quote_integrity_conflicts(
    *,
    action: dict[str, Any],
    estimate: dict[str, Any],
    raw_included_steps: object,
    source_chain_id: int,
    destination_chain_id: int,
    from_token: object,
    to_token: object,
    amount: int,
    from_address: str,
    to_address: str,
    slippage: float,
) -> list[SourceConflict]:
    conflicts: list[SourceConflict] = []

    if action.get("fromChainId") != source_chain_id:
        conflicts.append(_conflict("route.from_chain_id", source_chain_id, action.get("fromChainId")))
    if action.get("toChainId") != destination_chain_id:
        conflicts.append(_conflict("route.to_chain_id", destination_chain_id, action.get("toChainId")))

    quoted_from_amount = _positive_integer(action.get("fromAmount"))
    if quoted_from_amount != amount:
        conflicts.append(_conflict("route.from_amount", str(amount), action.get("fromAmount")))

    estimate_from_amount = estimate.get("fromAmount")
    if estimate_from_amount not in (None, ""):
        parsed_estimate_from = _positive_integer(estimate_from_amount)
        if parsed_estimate_from != amount:
            conflicts.append(_conflict("route.estimate_from_amount", str(amount), estimate_from_amount))

    quoted_from_address = _evm_address(action.get("fromAddress"))
    if quoted_from_address != from_address:
        conflicts.append(_conflict("route.from_address", from_address, action.get("fromAddress")))
    quoted_to_address = _evm_address(action.get("toAddress"))
    if quoted_to_address != to_address:
        conflicts.append(_conflict("route.to_address", to_address, action.get("toAddress")))

    if not _token_matches(from_token, action.get("fromToken")):
        conflicts.append(_conflict("route.from_token", str(from_token), action.get("fromToken")))
    if not _token_matches(to_token, action.get("toToken")):
        conflicts.append(_conflict("route.to_token", str(to_token), action.get("toToken")))

    quoted_slippage = action.get("slippage")
    if quoted_slippage not in (None, ""):
        try:
            parsed_slippage = float(quoted_slippage)
            if not math.isfinite(parsed_slippage) or abs(parsed_slippage - slippage) > 1e-12:
                conflicts.append(_conflict("route.slippage", slippage, quoted_slippage))
        except (TypeError, ValueError, OverflowError):
            conflicts.append(_conflict("route.slippage", slippage, quoted_slippage))

    to_amount_raw = estimate.get("toAmount")
    to_amount_min_raw = estimate.get("toAmountMin")
    to_amount = _positive_integer(to_amount_raw)
    minimum = _positive_integer(to_amount_min_raw) if to_amount_min_raw not in (None, "") else None
    if to_amount is None:
        conflicts.append(_conflict("route.to_amount", "positive integer", to_amount_raw))
    if to_amount_min_raw not in (None, "") and minimum is None:
        conflicts.append(_conflict("route.minimum_to_amount", "positive integer", to_amount_min_raw))
    if to_amount is not None and minimum is not None and minimum > to_amount:
        conflicts.append(_conflict("route.minimum_not_above_expected", f"<= {to_amount}", minimum))

    _, gas_costs_valid = _cost_total(estimate.get("gasCosts"))
    if not gas_costs_valid:
        conflicts.append(_conflict("route.gas_costs", "list of non-negative finite USD cost rows", estimate.get("gasCosts")))
    _, fee_costs_valid = _cost_total(estimate.get("feeCosts"))
    if not fee_costs_valid:
        conflicts.append(_conflict("route.fee_costs", "list of non-negative finite USD cost rows", estimate.get("feeCosts")))

    duration_raw = estimate.get("executionDuration")
    if _duration_seconds(duration_raw) is None:
        conflicts.append(_conflict("route.execution_duration", "non-negative finite seconds", duration_raw))

    _, steps_valid = _included_steps(raw_included_steps)
    if not steps_valid:
        conflicts.append(_conflict("route.included_steps", "list of non-empty step objects", raw_included_steps))
    return conflicts


def run_live_b5(input_data: dict[str, Any]) -> EngineResult:
    try:
        source = normalize_chain(input_data.get("source_chain") or input_data.get("fromChain"))
        destination = normalize_chain(input_data.get("destination_chain") or input_data.get("toChain"))
    except ValueError as exc:
        return _fail(str(exc), AnalysisStatus.UNSUPPORTED)

    from_token = input_data.get("source_token") or input_data.get("fromToken")
    to_token = input_data.get("destination_token") or input_data.get("toToken")
    amount_raw = input_data.get("amount") or input_data.get("fromAmount")
    wallet_raw = input_data.get("wallet") or input_data.get("fromAddress")
    to_address_raw = input_data.get("toAddress")
    slippage = input_data.get("slippage", 0.005)
    try:
        slippage = float(slippage)
    except (TypeError, ValueError, OverflowError):
        return _fail("slippage must be numeric")
    if not math.isfinite(slippage) or slippage < 0 or slippage > 0.5:
        return _fail("slippage must be between 0 and 0.5")
    if not all([from_token, to_token, amount_raw, wallet_raw]):
        return _fail("B5 live analysis requires source/destination chain, token, amount in smallest units, and wallet")

    amount = _positive_integer(amount_raw)
    if amount is None:
        return _fail("fromAmount must be a positive base-10 integer in smallest units")
    wallet = _evm_address(wallet_raw)
    if wallet is None:
        return _fail("fromAddress/wallet must be a valid EVM address")
    to_address = _evm_address(to_address_raw) if to_address_raw else wallet
    if to_address is None:
        return _fail("toAddress must be a valid EVM address")

    params = {
        "fromChain": source.chain_id,
        "toChain": destination.chain_id,
        "fromToken": str(from_token),
        "toToken": str(to_token),
        "fromAmount": str(amount),
        "fromAddress": wallet,
        "toAddress": to_address,
        "slippage": slippage,
        "order": input_data.get("order"),
        "allowBridges": input_data.get("allow_bridges"),
        "preferBridges": input_data.get("prefer_bridges"),
    }
    try:
        call = LifiClient().quote(params)
    except ProviderError as exc:
        return EngineResult(
            engine_id=EngineId.B5,
            engine_version="1.2.0",
            status=AnalysisStatus.PROVIDER_UNAVAILABLE,
            risk_score=0,
            data_confidence=0,
            engine_confidence=0,
            severity=Severity.UNKNOWN,
            summary="LI.FI route data is unavailable; no route was fabricated.",
            warnings=[f"{exc.code}: {exc}"],
            missing_data=["live cross-chain route quote"],
            provider_consensus="UNAVAILABLE",
            provider_status=[{"provider_id": "lifi", "status": "UNAVAILABLE", "detail": f"{exc.code}: {exc}"}],
        )

    body = call.result if isinstance(call.result, dict) else {}
    estimate = body.get("estimate") if isinstance(body.get("estimate"), dict) else {}
    action = body.get("action") if isinstance(body.get("action"), dict) else {}
    tool_details = body.get("toolDetails") if isinstance(body.get("toolDetails"), dict) else {}
    raw_included_steps = body.get("includedSteps")
    included, _ = _included_steps(raw_included_steps)
    gas_cost_usd, _ = _cost_total(estimate.get("gasCosts"))
    fee_cost_usd, _ = _cost_total(estimate.get("feeCosts"))
    execution_duration = _duration_seconds(estimate.get("executionDuration"))
    normalized = {
        "route_id": body.get("id"),
        "tool": body.get("tool"),
        "tool_name": tool_details.get("name"),
        "from_chain": action.get("fromChainId"),
        "to_chain": action.get("toChainId"),
        "from_token": ((action.get("fromToken") or {}).get("symbol") if isinstance(action.get("fromToken"), dict) else None),
        "to_token": ((action.get("toToken") or {}).get("symbol") if isinstance(action.get("toToken"), dict) else None),
        "from_amount": action.get("fromAmount"),
        "from_address": action.get("fromAddress"),
        "to_address": action.get("toAddress"),
        "quoted_slippage": action.get("slippage"),
        "expected_to_amount": estimate.get("toAmount"),
        "minimum_to_amount": estimate.get("toAmountMin"),
        "execution_duration_seconds": execution_duration,
        "gas_cost_usd": gas_cost_usd,
        "fee_cost_usd": fee_cost_usd,
        "included_steps": len(included),
        "approval_address": estimate.get("approvalAddress"),
        "requested": {
            "from_chain": source.chain_id,
            "to_chain": destination.chain_id,
            "from_token": str(from_token),
            "to_token": str(to_token),
            "from_amount": str(amount),
            "from_address": wallet,
            "to_address": to_address,
            "slippage": slippage,
        },
    }

    conflicts = _quote_integrity_conflicts(
        action=action,
        estimate=estimate,
        raw_included_steps=raw_included_steps,
        source_chain_id=source.chain_id,
        destination_chain_id=destination.chain_id,
        from_token=from_token,
        to_token=to_token,
        amount=amount,
        from_address=wallet,
        to_address=to_address,
        slippage=slippage,
    )
    evidence = [_evidence(call, normalized)]
    provider_status = [{"provider_id": "lifi", "status": "HEALTHY", "latency_ms": round(call.latency_ms, 2)}]
    if conflicts:
        normalized["integrity"] = {
            "status": "CONFLICTING",
            "conflict_count": len(conflicts),
            "conflict_metrics": [c.metric for c in conflicts],
        }
        return EngineResult(
            engine_id=EngineId.B5,
            engine_version="1.2.0",
            status=AnalysisStatus.CONFLICTING_DATA,
            risk_score=0,
            data_confidence=25,
            engine_confidence=0,
            severity=Severity.UNKNOWN,
            summary="LI.FI returned a route quote that does not match the requested route or contains internally inconsistent route/economic metadata. Rivexis discarded route scoring.",
            metrics=normalized,
            warnings=["Do not sign or execute this quote until request/response integrity conflicts are resolved."],
            safer_alternatives=["Request a fresh quote and re-run B5 integrity validation."],
            evidence=evidence,
            provider_consensus="CONFLICTING",
            provider_conflicts=conflicts,
            data_freshness={"status": "LIVE", "source": "LI.FI"},
            missing_data=["request-consistent and internally valid cross-chain route quote"],
            provider_status=provider_status,
            assumptions=["Rivexis treats caller route parameters and normalized provider economics/structure as trust-boundary evidence and does not silently accept malformed provider metadata."],
        )

    normalized["integrity"] = {"status": "MATCHED", "conflict_count": 0}
    score = 22.0
    if len(included) >= 4:
        score += 10
    if slippage > 0.03:
        score += 12
    if source.chain_id != destination.chain_id:
        score += 8
    warnings = ["Route quote is aggregator evidence, not an independent bridge-security assessment."]
    missing = [
        "independent bridge security intelligence",
        "independent liquidity/dependency risk validation",
        "historical bridge incident assessment",
    ]
    if estimate.get("toAmountMin") in (None, ""):
        missing.append("minimum received amount")
        warnings.append("LI.FI response did not provide a normalized minimum received amount.")
    return EngineResult(
        engine_id=EngineId.B5,
        engine_version="1.2.0",
        status=AnalysisStatus.PARTIAL,
        risk_score=min(100, score),
        data_confidence=84,
        engine_confidence=74,
        severity=_sev(score),
        summary="A live LI.FI route quote matched the requested route parameters and passed normalized route/economic integrity checks. Independent bridge-security/liquidity validation remains incomplete, so the route remains a partial analysis.",
        metrics=normalized,
        warnings=warnings,
        mitigations=["Cross-check bridge security and liquidity before signing a high-value cross-chain transaction."],
        safer_alternatives=["Request and compare additional routes after independent security providers are connected."],
        evidence=evidence,
        provider_consensus="SINGLE_SOURCE",
        data_freshness={"status": "LIVE", "source": "LI.FI"},
        missing_data=missing,
        provider_status=provider_status,
        assumptions=["Rivexis does not execute or sign the returned route; the wallet remains under explicit user control."],
    )


def _fail(message: str, status: AnalysisStatus = AnalysisStatus.INSUFFICIENT_DATA) -> EngineResult:
    return EngineResult(
        engine_id=EngineId.B5,
        engine_version="1.2.0",
        status=status,
        risk_score=0,
        data_confidence=0,
        engine_confidence=0,
        severity=Severity.UNKNOWN,
        summary=message,
        warnings=["No route was fabricated."],
        missing_data=["valid B5 route input"],
        provider_consensus="UNAVAILABLE",
    )
