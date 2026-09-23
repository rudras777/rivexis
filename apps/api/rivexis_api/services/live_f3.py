from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from rivexis_api.chains import normalize_chain
from rivexis_api.models.engine import EngineResult
from rivexis_api.models.enums import AnalysisStatus, EngineId, FreshnessStatus, Severity
from rivexis_api.models.evidence import EvidenceRecord, SourceConflict
from rivexis_api.provider_clients import CoinGeckoClient, ProviderCall, ProviderError, hex_to_int
from rivexis_api.providers import select_rpc_client
from rivexis_api.services.protocol_native import collect_protocol_native, has_protocol_native_input

DECIMALS_SELECTOR = "0x313ce567"
LATEST_ROUND_DATA_SELECTOR = "0xfeaf968c"
FUTURE_TIMESTAMP_TOLERANCE_SECONDS = 300


def _valid_address(value: str | None) -> bool:
    if not isinstance(value, str) or len(value) != 42 or not value.startswith("0x"):
        return False
    try:
        int(value[2:], 16)
        return True
    except ValueError:
        return False


def _finite_number(value: object) -> float | None:
    if value in (None, "") or isinstance(value, bool):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return parsed if math.isfinite(parsed) else None


def _rpc_uint(value: object, *, maximum: int | None = None) -> int | None:
    try:
        parsed = hex_to_int(value)
    except (TypeError, ValueError, OverflowError):
        return None
    if parsed is None or isinstance(parsed, bool) or parsed < 0:
        return None
    if maximum is not None and parsed > maximum:
        return None
    return parsed


def _signed_word(word: str) -> int:
    value = int(word, 16)
    return value - 2**256 if value >= 2**255 else value


def _decode_round_data(data: str) -> dict[str, int]:
    if not isinstance(data, str) or not data.startswith("0x"):
        raise ValueError("Oracle returned non-hex round data")
    clean = data[2:]
    if len(clean) != 64 * 5:
        raise ValueError("Oracle latestRoundData response must contain exactly five ABI words")
    try:
        int(clean, 16)
    except ValueError as exc:
        raise ValueError("Oracle latestRoundData response contains non-hex data") from exc
    words = [clean[i:i+64] for i in range(0, 64 * 5, 64)]
    return {
        "round_id": int(words[0], 16),
        "answer": _signed_word(words[1]),
        "started_at": int(words[2], 16),
        "updated_at": int(words[3], 16),
        "answered_in_round": int(words[4], 16),
    }


def _freshness(updated_at: int) -> tuple[FreshnessStatus, float | None, str, datetime | None]:
    if updated_at <= 0:
        return FreshnessStatus.UNKNOWN, None, "MISSING", None
    try:
        observed = datetime.fromtimestamp(updated_at, tz=timezone.utc)
    except (OverflowError, OSError, ValueError):
        return FreshnessStatus.UNKNOWN, None, "INVALID", None
    age = (datetime.now(timezone.utc) - observed).total_seconds()
    if age < -FUTURE_TIMESTAMP_TOLERANCE_SECONDS:
        return FreshnessStatus.UNKNOWN, age, "FUTURE", observed
    effective_age = max(0.0, age)
    if effective_age <= 120:
        freshness = FreshnessStatus.LIVE
    elif effective_age <= 900:
        freshness = FreshnessStatus.CURRENT
    elif effective_age <= 3600:
        freshness = FreshnessStatus.RECENT
    elif effective_age <= 21600:
        freshness = FreshnessStatus.STALE
    else:
        freshness = FreshnessStatus.EXPIRED
    return freshness, age, "OBSERVED", observed


def _ev(
    call: ProviderCall,
    provider: str,
    source_type: str,
    normalized: Any,
    chain_id: int | None,
    block: int | None,
    confidence: float,
    endpoint: str,
    freshness: FreshnessStatus = FreshnessStatus.LIVE,
    observed_at: datetime | None = None,
) -> EvidenceRecord:
    now = datetime.now(timezone.utc)
    return EvidenceRecord(
        evidence_id=str(uuid4()),
        provider=provider,
        source_type=source_type,
        provider_endpoint=endpoint,
        provider_request_id=call.request_id,
        retrieved_at=now,
        observed_at=observed_at or now,
        chain_id=chain_id,
        block_number=block,
        raw_reference=f"provider:{provider};request:{call.request_id}",
        normalized_value=normalized,
        calculation_version="f3-live-1.3.0",
        engine_version="1.3.0",
        confidence=confidence,
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


def _read_feed(
    rpc,
    provider_id: str,
    chain_id: int,
    block: int,
    block_tag: str,
    address: str,
    label: str,
):
    dec_call = rpc.call("eth_call", [{"to": address, "data": DECIMALS_SELECTOR}, block_tag])
    decimals = _rpc_uint(dec_call.result, maximum=36)
    if decimals is None:
        raise ProviderError(
            "Oracle decimals are malformed or outside supported bounds",
            provider_id=provider_id,
            code="MALFORMED_ORACLE",
        )
    round_call = rpc.call("eth_call", [{"to": address, "data": LATEST_ROUND_DATA_SELECTOR}, block_tag])
    try:
        decoded = _decode_round_data(str(round_call.result))
    except ValueError as exc:
        raise ProviderError(
            str(exc), provider_id=provider_id, code="MALFORMED_ORACLE"
        ) from exc
    if decoded["answer"] <= 0:
        raise ProviderError(
            "Oracle answer is non-positive",
            provider_id=provider_id,
            code="INVALID_ORACLE_ANSWER",
        )
    freshness, age, timestamp_status, observed_at = _freshness(decoded["updated_at"])
    price = decoded["answer"] / (10 ** decimals)
    if not math.isfinite(price) or price <= 0:
        raise ProviderError(
            "Oracle normalized price is non-positive or non-finite",
            provider_id=provider_id,
            code="INVALID_ORACLE_ANSWER",
        )
    normalized = {
        "label": label,
        "feed_address": address,
        "decimals": decimals,
        "price": price,
        **decoded,
        "age_seconds": age,
        "freshness": freshness.value,
        "timestamp_status": timestamp_status,
        "round_consistent": decoded["answered_in_round"] >= decoded["round_id"],
        "block_tag": block_tag,
    }
    evidence = [
        _ev(
            dec_call,
            provider_id,
            "direct_oracle_state",
            {"feed_address": address, "decimals": decimals, "block_tag": block_tag},
            chain_id,
            block,
            98,
            "eth_call decimals()",
            freshness,
            observed_at,
        ),
        _ev(
            round_call,
            provider_id,
            "direct_oracle_state",
            normalized,
            chain_id,
            block,
            98,
            "eth_call latestRoundData()",
            freshness,
            observed_at,
        ),
    ]
    return normalized, evidence


def run_live_f3(input_data: dict[str, Any]) -> EngineResult:
    try:
        chain = normalize_chain(input_data.get("chain") or "ethereum")
    except ValueError as exc:
        return _fail(str(exc), AnalysisStatus.UNSUPPORTED)

    if input_data.get("protocol_adapter") and (input_data.get("user_address") or input_data.get("wallet")):
        try:
            native = collect_protocol_native(input_data)
            adapter = (native.metrics or {}).get("protocol_adapter") if isinstance(native.metrics, dict) else None
            if isinstance(adapter, dict) and isinstance(adapter.get("position"), dict):
                position = adapter["position"]
                adapter_name = str(adapter.get("adapter") or "protocol")
                health = position.get("health_factor")
                is_liquidatable = position.get("is_liquidatable")
                if health is not None or is_liquidatable is not None:
                    score = 22.0
                    blockers: list[str] = []
                    mitigations: list[str] = []
                    if is_liquidatable is True:
                        score = 96.0
                        blockers.append("Protocol-native state reports the position as presently liquidatable.")
                        mitigations.append("Reduce debt or add collateral before further risk-taking.")
                    elif health is not None:
                        hf = _finite_number(health)
                        if hf is None or hf < 0:
                            raise ProviderError(
                                "Protocol-native health factor is malformed",
                                provider_id=adapter_name,
                                code="MALFORMED_RESPONSE",
                            )
                        score = 95.0 if hf <= 1 else 86.0 if hf < 1.05 else 72.0 if hf < 1.2 else 48.0 if hf < 1.5 else 22.0
                        if hf <= 1:
                            blockers.append("Protocol-native health factor is at or below 1.0.")
                        if hf < 1.5:
                            mitigations.append("Increase the protocol-native liquidation buffer by adding collateral or reducing debt.")
                    score = min(100.0, score + min(20.0, native.risk_delta))
                    return EngineResult(
                        engine_id=EngineId.F3,
                        engine_version="1.3.0",
                        block_reference=native.block_number,
                        status=AnalysisStatus.PARTIAL,
                        risk_score=score,
                        data_confidence=max(88.0, native.confidence),
                        engine_confidence=92,
                        severity=_severity(score),
                        summary=f"F3 used {adapter_name} protocol-native position and liquidation configuration instead of caller-modeled balances/thresholds.",
                        metrics={"chain": chain.key, "protocol_native": native.metrics, "position": position, "authoritative_adapter": adapter_name},
                        warnings=native.warnings,
                        hard_blockers=blockers,
                        mitigations=mitigations,
                        safer_alternatives=([] if not blockers else ["Re-evaluate after the protocol itself reports a restored liquidation buffer."]),
                        evidence=native.evidence,
                        provider_consensus=("MULTI_SOURCE" if len({e.provider for e in native.evidence}) > 1 else "SINGLE_SOURCE"),
                        data_freshness={"status": FreshnessStatus.LIVE.value, "block_number": native.block_number},
                        missing_data=sorted(set(native.missing_data)),
                        provider_status=native.provider_status,
                        assumptions=native.assumptions,
                    )
        except (ValueError, ProviderError):
            pass

    collateral_feed = input_data.get("collateral_price_feed") or input_data.get("oracle_feed_address")
    if not _valid_address(collateral_feed):
        return _fail("F3 live mode requires a valid collateral_price_feed/oracle_feed_address")
    debt_feed = input_data.get("debt_price_feed")
    if debt_feed is not None and not _valid_address(str(debt_feed)):
        return _fail("debt_price_feed must be a valid EVM address when supplied")

    collateral_units = _finite_number(input_data.get("collateral_units"))
    debt_units = _finite_number(input_data.get("debt_units"))
    liquidation_threshold = _finite_number(input_data.get("liquidation_threshold"))
    if collateral_units is None or debt_units is None or liquidation_threshold is None:
        return _fail("F3 live mode requires finite numeric collateral_units, debt_units and liquidation_threshold; booleans are not numeric position values")
    if collateral_units <= 0 or debt_units <= 0 or not (0 < liquidation_threshold <= 1.5):
        return _fail("F3 position quantities must be positive and liquidation_threshold must be >0 and <=1.5")

    tolerance = _finite_number(input_data.get("price_conflict_tolerance_pct", 3.0))
    if tolerance is None or tolerance < 0:
        return _fail("price_conflict_tolerance_pct must be a finite non-negative number")

    evidence: list[EvidenceRecord] = []
    conflicts: list[SourceConflict] = []
    warnings: list[str] = []
    missing: list[str] = [
        "independent verification that supplied feed address is the protocol-native oracle dependency",
        "protocol-native collateral/debt balances and liquidation parameters",
    ]
    statuses: list[dict[str, Any]] = []
    try:
        pid, rpc, probe, fallback_errors = select_rpc_client(chain.key)
        statuses.extend({"provider_id": x["provider_id"], "status": "FAILED_OR_UNAVAILABLE", "detail": x["error"]} for x in fallback_errors)
        block_call = rpc.call("eth_blockNumber")
        block = _rpc_uint(block_call.result)
        if block is None:
            raise ProviderError(
                "RPC returned a malformed block number",
                provider_id=pid,
                code="MALFORMED_RESPONSE",
            )
        block_tag = hex(block)
        evidence.append(_ev(block_call, pid, "direct_state", {"block_number": block, "block_tag": block_tag}, chain.chain_id, block, 99, "eth_blockNumber"))
        collateral, cev = _read_feed(rpc, pid, chain.chain_id, block, block_tag, str(collateral_feed), "collateral")
        evidence.extend(cev)
        if debt_feed:
            debt, dev = _read_feed(rpc, pid, chain.chain_id, block, block_tag, str(debt_feed), "debt")
            debt_price = _finite_number(debt["price"])
            if debt_price is None or debt_price <= 0:
                raise ProviderError("Debt oracle price is invalid", provider_id=pid, code="INVALID_ORACLE_ANSWER")
            evidence.extend(dev)
        else:
            debt_price = _finite_number(input_data.get("debt_price_usd", 1.0))
            if debt_price is None or debt_price <= 0:
                return _fail("debt_price_usd must be a positive finite number when debt_price_feed is absent")
            debt = {"price": debt_price, "source": "user_assumption", "freshness": "UNKNOWN"}
            missing.append("live debt oracle price")
        statuses.append({"provider_id": pid, "status": "HEALTHY", "latency_ms": round(probe.latency_ms, 2)})
    except (ProviderError, ValueError) as exc:
        detail = f"{getattr(exc, 'code', 'ORACLE_DECODE')}: {exc}"
        return EngineResult(
            engine_id=EngineId.F3,
            engine_version="1.3.0",
            status=AnalysisStatus.PROVIDER_UNAVAILABLE,
            risk_score=0,
            data_confidence=0,
            engine_confidence=0,
            severity=Severity.UNKNOWN,
            summary="F3 could not read the supplied live oracle feed.",
            warnings=[detail],
            missing_data=["live oracle evidence"],
            provider_consensus="UNAVAILABLE",
            provider_status=statuses + [{"provider_id": getattr(exc, "provider_id", "rpc"), "status": "UNAVAILABLE", "detail": detail}],
        )

    collateral_price = _finite_number(collateral["price"])
    if collateral_price is None or collateral_price <= 0:
        return _fail("Collateral oracle normalized to a non-positive or non-finite price")

    if collateral.get("timestamp_status") == "FUTURE":
        warnings.append("Collateral oracle updatedAt is materially in the future; Rivexis did not classify it as fresh.")
        missing.append("credible collateral oracle observation timestamp")
    elif collateral.get("timestamp_status") in {"MISSING", "INVALID"}:
        warnings.append("Collateral oracle does not provide a credible observation timestamp; freshness remains UNKNOWN.")
        missing.append("credible collateral oracle observation timestamp")

    cg_id = input_data.get("collateral_coingecko_id")
    if cg_id:
        try:
            cg_call = CoinGeckoClient().simple_price([str(cg_id)], "usd")
            body = cg_call.result if isinstance(cg_call.result, dict) else {}
            market = body.get(str(cg_id)) if isinstance(body.get(str(cg_id)), dict) else {}
            market_price = _finite_number(market.get("usd"))
            if market_price is not None and market_price > 0:
                diff_pct = abs(collateral_price - market_price) / max(abs(collateral_price), 1e-12) * 100
                market_timestamp_raw = market.get("last_updated_at")
                market_timestamp = None
                if not isinstance(market_timestamp_raw, bool):
                    try:
                        market_timestamp = int(market_timestamp_raw) if market_timestamp_raw is not None else None
                    except (TypeError, ValueError, OverflowError):
                        market_timestamp = None
                if market_timestamp is not None:
                    market_freshness, market_age, market_timestamp_status, market_observed = _freshness(market_timestamp)
                else:
                    market_freshness, market_age, market_timestamp_status, market_observed = (FreshnessStatus.UNKNOWN, None, "MISSING", None)
                normalized_market = {
                    "coingecko_id": str(cg_id),
                    "usd": market_price,
                    "last_updated_at": market_timestamp_raw,
                    "age_seconds": market_age,
                    "timestamp_status": market_timestamp_status,
                    "difference_from_oracle_pct": diff_pct,
                }
                evidence.append(_ev(cg_call, "coingecko", "professional_market_reference", normalized_market, None, None, 90, "GET /api/v3/simple/price", market_freshness, market_observed))
                statuses.append({"provider_id": "coingecko", "status": "HEALTHY", "latency_ms": round(cg_call.latency_ms, 2)})
                if market_freshness == FreshnessStatus.UNKNOWN:
                    warnings.append("CoinGecko market-reference timestamp is missing, invalid, or materially future; market freshness remains UNKNOWN.")
                    missing.append("credible CoinGecko collateral market timestamp")
                if diff_pct > tolerance:
                    conflicts.append(SourceConflict(
                        metric="collateral_price_usd",
                        source_a=f"onchain_feed:{collateral_feed}",
                        value_a=collateral_price,
                        source_b="coingecko",
                        value_b=market_price,
                        difference=abs(collateral_price - market_price),
                        difference_percentage=diff_pct,
                        expected_tolerance=tolerance,
                        severity="high" if diff_pct > 10 else "moderate",
                        resolution_method="unresolved",
                        resolution_confidence=0,
                    ))
                    warnings.append(f"Oracle and market reference prices differ by {diff_pct:.2f}%.")
            else:
                statuses.append({"provider_id": "coingecko", "status": "MALFORMED_RESPONSE"})
                warnings.append("CoinGecko collateral market price was missing, non-positive, or non-finite and was excluded.")
                missing.append("CoinGecko collateral market reference")
        except ProviderError as exc:
            statuses.append({"provider_id": "coingecko", "status": "UNAVAILABLE", "detail": f"{exc.code}: {exc}"})
            missing.append("CoinGecko collateral market reference")

    collateral_value = collateral_units * collateral_price
    debt_value = debt_units * debt_price
    if not math.isfinite(collateral_value) or not math.isfinite(debt_value) or debt_value <= 0:
        return _fail("F3 modeled position produced non-finite or non-positive economic values")
    health_factor = collateral_value * liquidation_threshold / debt_value
    liquidation_price = debt_value / (collateral_units * liquidation_threshold)
    distance_pct = (collateral_price - liquidation_price) / collateral_price * 100
    if not all(math.isfinite(value) for value in (health_factor, liquidation_price, distance_pct)):
        return _fail("F3 modeled liquidation metrics are non-finite")

    scenarios = []
    for shock in (-5, -10, -20, -30):
        shocked = collateral_price * (1 + shock / 100)
        hf = (collateral_units * shocked * liquidation_threshold) / debt_value
        scenarios.append({"collateral_price_shock_pct": shock, "collateral_price": round(shocked, 8), "health_factor": round(hf, 4), "liquidatable": hf < 1.0})

    score = 92 if health_factor < 1.0 else 85 if health_factor < 1.05 else 72 if health_factor < 1.2 else 48 if health_factor < 1.5 else 22
    if distance_pct < 10:
        warnings.append("Liquidation buffer is below 10% on the supplied position model.")
    metrics = {
        "chain": chain.key,
        "collateral_price_usd": collateral_price,
        "debt_price_usd": debt_price,
        "collateral_value_usd": round(collateral_value, 6),
        "debt_value_usd": round(debt_value, 6),
        "liquidation_threshold": liquidation_threshold,
        "health_factor": round(health_factor, 6),
        "liquidation_price": round(liquidation_price, 8),
        "liquidation_distance_pct": round(distance_pct, 4),
        "stress_scenarios": scenarios,
        "oracle": collateral,
        "block_tag": block_tag,
    }
    assumptions = [
        "Position quantities and liquidation threshold are user-supplied until protocol-native state adapters are connected.",
        "The supplied feed address is not assumed to be the protocol's actual oracle without separate verification.",
        f"All direct oracle reads for this modeled position are pinned to captured RPC block {block_tag}.",
    ]
    if has_protocol_native_input(input_data):
        try:
            native = collect_protocol_native(input_data)
            metrics["protocol_native"] = native.metrics
            evidence.extend(native.evidence)
            statuses.extend(native.provider_status)
            warnings.extend(native.warnings)
            missing.extend(native.missing_data)
            assumptions.extend(native.assumptions)
            score = min(100.0, score + native.risk_delta)
        except (ValueError, ProviderError) as exc:
            warnings.append(f"Additional protocol-native position evidence could not be collected: {exc}")
            missing.append("additional protocol-native position evidence")

    oracle_fresh = collateral.get("freshness")
    status = AnalysisStatus.PARTIAL
    if conflicts:
        status = AnalysisStatus.CONFLICTING_DATA
    elif oracle_fresh in {FreshnessStatus.STALE.value, FreshnessStatus.EXPIRED.value}:
        status = AnalysisStatus.STALE_DATA
    data_conf = 84 - min(20, len(conflicts) * 12) - (15 if status == AnalysisStatus.STALE_DATA else 0)
    if oracle_fresh == FreshnessStatus.UNKNOWN.value:
        data_conf = max(45, data_conf - 15)
    if metrics.get("protocol_native"):
        data_conf = min(94, data_conf + 5)
    return EngineResult(
        engine_id=EngineId.F3,
        engine_version="1.3.0",
        block_reference=block,
        status=status,
        risk_score=score,
        data_confidence=max(0, data_conf),
        engine_confidence=84 if metrics.get("protocol_native") else 80,
        severity=_severity(score),
        summary=f"F3 calculated a modeled health factor of {health_factor:.3f} using live on-chain oracle evidence and user-supplied position parameters; declared protocol-native evidence was incorporated when supplied.",
        metrics=metrics,
        warnings=warnings,
        hard_blockers=(["Modeled position is at or beyond the liquidation threshold."] if health_factor < 1.0 else []),
        mitigations=(["Add collateral or reduce debt to increase liquidation buffer."] if health_factor < 1.5 else []),
        safer_alternatives=(["Re-run with protocol-native balances and independently verified oracle dependency before acting."] if missing else []),
        evidence=evidence,
        provider_consensus="CONFLICTING" if conflicts else ("MULTI_SOURCE" if len({e.provider for e in evidence}) > 1 else "SINGLE_SOURCE"),
        provider_conflicts=conflicts,
        data_freshness={"status": oracle_fresh, "oracle_age_seconds": collateral.get("age_seconds"), "block_number": block},
        missing_data=sorted(set(missing)),
        provider_status=statuses,
        assumptions=assumptions,
    )


def _fail(message: str, status: AnalysisStatus = AnalysisStatus.INSUFFICIENT_DATA) -> EngineResult:
    return EngineResult(
        engine_id=EngineId.F3,
        engine_version="1.3.0",
        status=status,
        risk_score=0,
        data_confidence=0,
        engine_confidence=0,
        severity=Severity.UNKNOWN,
        summary=message,
        warnings=["No liquidation metric was fabricated."],
        missing_data=["valid F3 live input"],
        provider_consensus="UNAVAILABLE",
    )
