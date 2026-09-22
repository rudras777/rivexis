from __future__ import annotations

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


def _valid_address(value: str | None) -> bool:
    if not isinstance(value, str) or len(value) != 42 or not value.startswith("0x"):
        return False
    try:
        int(value[2:], 16)
        return True
    except ValueError:
        return False


def _signed_word(word: str) -> int:
    value = int(word, 16)
    return value - 2**256 if value >= 2**255 else value


def _decode_round_data(data: str) -> dict[str, int]:
    if not isinstance(data, str) or not data.startswith("0x"):
        raise ValueError("Oracle returned non-hex round data")
    clean = data[2:]
    if len(clean) < 64 * 5:
        raise ValueError("Oracle latestRoundData response is too short")
    words = [clean[i:i+64] for i in range(0, 64 * 5, 64)]
    return {
        "round_id": int(words[0], 16),
        "answer": _signed_word(words[1]),
        "started_at": int(words[2], 16),
        "updated_at": int(words[3], 16),
        "answered_in_round": int(words[4], 16),
    }


def _freshness(updated_at: int) -> tuple[FreshnessStatus, int]:
    age = max(0, int(datetime.now(timezone.utc).timestamp()) - updated_at) if updated_at else 10**12
    if age <= 120:
        return FreshnessStatus.LIVE, age
    if age <= 900:
        return FreshnessStatus.CURRENT, age
    if age <= 3600:
        return FreshnessStatus.RECENT, age
    if age <= 21600:
        return FreshnessStatus.STALE, age
    return FreshnessStatus.EXPIRED, age


def _ev(call: ProviderCall, provider: str, source_type: str, normalized: Any, chain_id: int | None, block: int | None, confidence: float, endpoint: str, freshness: FreshnessStatus = FreshnessStatus.LIVE) -> EvidenceRecord:
    return EvidenceRecord(
        evidence_id=str(uuid4()), provider=provider, source_type=source_type, provider_endpoint=endpoint,
        provider_request_id=call.request_id, retrieved_at=datetime.now(timezone.utc), observed_at=datetime.now(timezone.utc),
        chain_id=chain_id, block_number=block, raw_reference=f"provider:{provider};request:{call.request_id}",
        normalized_value=normalized, calculation_version="f3-live-1.1.0", engine_version="1.1.0",
        confidence=confidence, freshness=freshness, license_classification="external-provider-evidence",
    )


def _severity(score: float) -> Severity:
    if score >= 80: return Severity.CRITICAL
    if score >= 60: return Severity.HIGH
    if score >= 35: return Severity.MODERATE
    return Severity.LOW


def _read_feed(rpc, provider_id: str, chain_id: int, block: int | None, address: str, label: str):
    dec_call = rpc.call("eth_call", [{"to": address, "data": DECIMALS_SELECTOR}, "latest"])
    decimals = int(str(dec_call.result), 16)
    if decimals < 0 or decimals > 36:
        raise ProviderError("Oracle decimals are outside supported bounds", provider_id=provider_id, code="MALFORMED_ORACLE")
    round_call = rpc.call("eth_call", [{"to": address, "data": LATEST_ROUND_DATA_SELECTOR}, "latest"])
    decoded = _decode_round_data(str(round_call.result))
    if decoded["answer"] <= 0:
        raise ProviderError("Oracle answer is non-positive", provider_id=provider_id, code="INVALID_ORACLE_ANSWER")
    freshness, age = _freshness(decoded["updated_at"])
    price = decoded["answer"] / (10 ** decimals)
    normalized = {
        "label": label, "feed_address": address, "decimals": decimals, "price": price,
        **decoded, "age_seconds": age, "freshness": freshness.value,
        "round_consistent": decoded["answered_in_round"] >= decoded["round_id"],
    }
    evidence = [
        _ev(dec_call, provider_id, "direct_oracle_state", {"feed_address": address, "decimals": decimals}, chain_id, block, 98, "eth_call decimals()", freshness),
        _ev(round_call, provider_id, "direct_oracle_state", normalized, chain_id, block, 98, "eth_call latestRoundData()", freshness),
    ]
    return normalized, evidence


def run_live_f3(input_data: dict[str, Any]) -> EngineResult:
    try:
        chain = normalize_chain(input_data.get("chain") or "ethereum")
    except ValueError as exc:
        return _fail(str(exc), AnalysisStatus.UNSUPPORTED)

    # Protocol-specific adapters can provide authoritative liquidation state without
    # requiring the caller to manually re-enter balances, thresholds or oracle addresses.
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
                        hf = float(health)
                        score = 95.0 if hf <= 1 else 86.0 if hf < 1.05 else 72.0 if hf < 1.2 else 48.0 if hf < 1.5 else 22.0
                        if hf <= 1:
                            blockers.append("Protocol-native health factor is at or below 1.0.")
                        if hf < 1.5:
                            mitigations.append("Increase the protocol-native liquidation buffer by adding collateral or reducing debt.")
                    score = min(100.0, score + min(20.0, native.risk_delta))
                    return EngineResult(
                        engine_id=EngineId.F3, engine_version="1.3.0", block_reference=native.block_number,
                        status=AnalysisStatus.PARTIAL, risk_score=score,
                        data_confidence=max(88.0, native.confidence), engine_confidence=92, severity=_severity(score),
                        summary=f"F3 used {adapter_name} protocol-native position and liquidation configuration instead of caller-modeled balances/thresholds.",
                        metrics={"chain": chain.key, "protocol_native": native.metrics, "position": position, "authoritative_adapter": adapter_name},
                        warnings=native.warnings, hard_blockers=blockers, mitigations=mitigations,
                        safer_alternatives=([] if not blockers else ["Re-evaluate after the protocol itself reports a restored liquidation buffer."]),
                        evidence=native.evidence, provider_consensus=("MULTI_SOURCE" if len({e.provider for e in native.evidence}) > 1 else "SINGLE_SOURCE"),
                        data_freshness={"status": FreshnessStatus.LIVE.value, "block_number": native.block_number},
                        missing_data=sorted(set(native.missing_data)), provider_status=native.provider_status, assumptions=native.assumptions,
                    )
        except (ValueError, ProviderError):
            # Fall through to the generic model, which retains strict input validation.
            pass

    collateral_feed = input_data.get("collateral_price_feed") or input_data.get("oracle_feed_address")
    if not _valid_address(collateral_feed):
        return _fail("F3 live mode requires a valid collateral_price_feed/oracle_feed_address")
    debt_feed = input_data.get("debt_price_feed")
    if debt_feed is not None and not _valid_address(str(debt_feed)):
        return _fail("debt_price_feed must be a valid EVM address when supplied")

    try:
        collateral_units = float(input_data["collateral_units"])
        debt_units = float(input_data["debt_units"])
        liquidation_threshold = float(input_data["liquidation_threshold"])
    except (KeyError, TypeError, ValueError):
        return _fail("F3 live mode requires numeric collateral_units, debt_units and liquidation_threshold")
    if collateral_units <= 0 or debt_units <= 0 or not (0 < liquidation_threshold <= 1.5):
        return _fail("F3 position quantities must be positive and liquidation_threshold must be >0 and <=1.5")

    evidence: list[EvidenceRecord] = []
    conflicts: list[SourceConflict] = []
    warnings: list[str] = []
    missing: list[str] = ["independent verification that supplied feed address is the protocol-native oracle dependency", "protocol-native collateral/debt balances and liquidation parameters"]
    statuses: list[dict[str, Any]] = []
    try:
        pid, rpc, probe, fallback_errors = select_rpc_client(chain.key)
        statuses.extend({"provider_id":x["provider_id"],"status":"FAILED_OR_UNAVAILABLE","detail":x["error"]} for x in fallback_errors)
        block_call = rpc.call("eth_blockNumber")
        block = hex_to_int(block_call.result)
        evidence.append(_ev(block_call, pid, "direct_state", {"block_number": block}, chain.chain_id, block, 99, "eth_blockNumber"))
        collateral, cev = _read_feed(rpc, pid, chain.chain_id, block, str(collateral_feed), "collateral")
        evidence.extend(cev)
        if debt_feed:
            debt, dev = _read_feed(rpc, pid, chain.chain_id, block, str(debt_feed), "debt")
            debt_price = float(debt["price"]); evidence.extend(dev)
        else:
            try:
                debt_price = float(input_data.get("debt_price_usd", 1.0))
            except (TypeError, ValueError):
                return _fail("debt_price_usd must be numeric when debt_price_feed is absent")
            debt = {"price": debt_price, "source": "user_assumption", "freshness": "UNKNOWN"}
            missing.append("live debt oracle price")
        statuses.append({"provider_id":pid,"status":"HEALTHY","latency_ms":round(probe.latency_ms,2)})
    except (ProviderError, ValueError) as exc:
        detail = f"{getattr(exc, 'code', 'ORACLE_DECODE')}: {exc}"
        return EngineResult(engine_id=EngineId.F3,engine_version="1.1.0",status=AnalysisStatus.PROVIDER_UNAVAILABLE,risk_score=0,data_confidence=0,engine_confidence=0,severity=Severity.UNKNOWN,summary="F3 could not read the supplied live oracle feed.",warnings=[detail],missing_data=["live oracle evidence"],provider_consensus="UNAVAILABLE",provider_status=statuses+[{"provider_id":getattr(exc,'provider_id','rpc'),"status":"UNAVAILABLE","detail":detail}])

    collateral_price = float(collateral["price"])
    cg_id = input_data.get("collateral_coingecko_id")
    if cg_id:
        try:
            cg_call = CoinGeckoClient().simple_price([str(cg_id)], "usd")
            body = cg_call.result if isinstance(cg_call.result, dict) else {}
            market = body.get(str(cg_id)) if isinstance(body.get(str(cg_id)), dict) else {}
            market_price = market.get("usd")
            if market_price is not None:
                market_price = float(market_price)
                diff_pct = abs(collateral_price-market_price)/max(abs(collateral_price),1e-12)*100
                normalized_market={"coingecko_id":str(cg_id),"usd":market_price,"last_updated_at":market.get("last_updated_at"),"difference_from_oracle_pct":diff_pct}
                evidence.append(_ev(cg_call,"coingecko","professional_market_reference",normalized_market,None,None,90,"GET /api/v3/simple/price",FreshnessStatus.CURRENT))
                statuses.append({"provider_id":"coingecko","status":"HEALTHY","latency_ms":round(cg_call.latency_ms,2)})
                if diff_pct > float(input_data.get("price_conflict_tolerance_pct",3.0)):
                    conflicts.append(SourceConflict(metric="collateral_price_usd",source_a=f"onchain_feed:{collateral_feed}",value_a=collateral_price,source_b="coingecko",value_b=market_price,difference=abs(collateral_price-market_price),difference_percentage=diff_pct,expected_tolerance=float(input_data.get("price_conflict_tolerance_pct",3.0)),severity="high" if diff_pct>10 else "moderate",resolution_method="unresolved",resolution_confidence=0))
                    warnings.append(f"Oracle and market reference prices differ by {diff_pct:.2f}%.")
            else:
                missing.append("CoinGecko collateral market reference")
        except ProviderError as exc:
            statuses.append({"provider_id":"coingecko","status":"UNAVAILABLE","detail":f"{exc.code}: {exc}"})
            missing.append("CoinGecko collateral market reference")

    collateral_value = collateral_units * collateral_price
    debt_value = debt_units * debt_price
    health_factor = collateral_value * liquidation_threshold / debt_value if debt_value > 0 else 999.0
    liquidation_price = debt_value / (collateral_units * liquidation_threshold)
    distance_pct = (collateral_price-liquidation_price)/collateral_price*100
    scenarios=[]
    for shock in (-5,-10,-20,-30):
        shocked=collateral_price*(1+shock/100)
        hf=(collateral_units*shocked*liquidation_threshold)/debt_value
        scenarios.append({"collateral_price_shock_pct":shock,"collateral_price":round(shocked,8),"health_factor":round(hf,4),"liquidatable":hf<1.0})
    score = 92 if health_factor<1.0 else 85 if health_factor<1.05 else 72 if health_factor<1.2 else 48 if health_factor<1.5 else 22
    if distance_pct < 10: warnings.append("Liquidation buffer is below 10% on the supplied position model.")
    metrics={"chain":chain.key,"collateral_price_usd":collateral_price,"debt_price_usd":debt_price,"collateral_value_usd":round(collateral_value,6),"debt_value_usd":round(debt_value,6),"liquidation_threshold":liquidation_threshold,"health_factor":round(health_factor,6),"liquidation_price":round(liquidation_price,8),"liquidation_distance_pct":round(distance_pct,4),"stress_scenarios":scenarios,"oracle":collateral}
    assumptions=["Position quantities and liquidation threshold are user-supplied until protocol-native state adapters are connected.","The supplied feed address is not assumed to be the protocol's actual oracle without separate verification."]
    if has_protocol_native_input(input_data):
        try:
            native=collect_protocol_native(input_data)
            metrics["protocol_native"]=native.metrics
            evidence.extend(native.evidence)
            statuses.extend(native.provider_status)
            warnings.extend(native.warnings)
            missing.extend(native.missing_data)
            assumptions.extend(native.assumptions)
            score=min(100.0,score+native.risk_delta)
        except (ValueError,ProviderError) as exc:
            warnings.append(f"Additional protocol-native position evidence could not be collected: {exc}")
            missing.append("additional protocol-native position evidence")
    oracle_fresh = collateral.get("freshness")
    status = AnalysisStatus.PARTIAL
    if conflicts: status = AnalysisStatus.CONFLICTING_DATA
    elif oracle_fresh in {FreshnessStatus.STALE.value, FreshnessStatus.EXPIRED.value}: status = AnalysisStatus.STALE_DATA
    data_conf = 84 - min(20,len(conflicts)*12) - (15 if status==AnalysisStatus.STALE_DATA else 0)
    if metrics.get("protocol_native"):
        data_conf=min(94,data_conf+5)
    return EngineResult(
        engine_id=EngineId.F3,engine_version="1.2.0",block_reference=block,status=status,risk_score=score,data_confidence=max(0,data_conf),engine_confidence=84 if metrics.get("protocol_native") else 80,severity=_severity(score),
        summary=f"F3 calculated a modeled health factor of {health_factor:.3f} using live on-chain oracle evidence and user-supplied position parameters; declared protocol-native evidence was incorporated when supplied.",
        metrics=metrics,
        warnings=warnings,hard_blockers=(["Modeled position is at or beyond the liquidation threshold."] if health_factor<1.0 else []),mitigations=(["Add collateral or reduce debt to increase liquidation buffer."] if health_factor<1.5 else []),safer_alternatives=(["Re-run with protocol-native balances and independently verified oracle dependency before acting."] if missing else []),evidence=evidence,provider_consensus="CONFLICTING" if conflicts else ("MULTI_SOURCE" if len({e.provider for e in evidence})>1 else "SINGLE_SOURCE"),provider_conflicts=conflicts,data_freshness={"status":oracle_fresh,"oracle_age_seconds":collateral.get("age_seconds"),"block_number":block},missing_data=sorted(set(missing)),provider_status=statuses,assumptions=assumptions)


def _fail(message: str, status: AnalysisStatus=AnalysisStatus.INSUFFICIENT_DATA) -> EngineResult:
    return EngineResult(engine_id=EngineId.F3,engine_version="1.1.0",status=status,risk_score=0,data_confidence=0,engine_confidence=0,severity=Severity.UNKNOWN,summary=message,warnings=["No liquidation metric was fabricated."],missing_data=["valid F3 live input"],provider_consensus="UNAVAILABLE")
