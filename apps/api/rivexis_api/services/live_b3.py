from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from rivexis_api.chains import normalize_chain
from rivexis_api.models.engine import EngineResult
from rivexis_api.models.enums import AnalysisStatus, EngineId, FreshnessStatus, Severity
from rivexis_api.models.evidence import EvidenceRecord
from rivexis_api.provider_clients import BlockaidClient, ProviderCall, ProviderError, hex_to_int
from rivexis_api.providers import resolve_provider, select_rpc_client
from rivexis_api.services.security_intel import blockaid_risk, normalize_blockaid

TOTAL_SUPPLY_SELECTOR = "0x18160ddd"
DECIMALS_SELECTOR = "0x313ce567"
LATEST_ROUND_DATA_SELECTOR = "0xfeaf968c"


def _valid_address(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 42 or not value.startswith("0x"):
        return False
    try:
        int(value[2:], 16)
        return True
    except ValueError:
        return False


def _num(value: Any, default: float | None = None) -> float | None:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _severity(score: float) -> Severity:
    return Severity.CRITICAL if score >= 80 else Severity.HIGH if score >= 60 else Severity.MODERATE if score >= 35 else Severity.LOW


def _evidence(call: ProviderCall, *, source_type: str, normalized_value: Any, chain_id: int, block_number: int | None, method: str, confidence: float = 99, observed_at: datetime | None = None, freshness: FreshnessStatus = FreshnessStatus.LIVE) -> EvidenceRecord:
    return EvidenceRecord(
        evidence_id=str(uuid4()),
        provider=call.provider_id,
        source_type=source_type,
        provider_endpoint=method,
        provider_request_id=call.request_id,
        retrieved_at=datetime.now(timezone.utc),
        observed_at=observed_at or datetime.now(timezone.utc),
        block_number=block_number,
        chain_id=chain_id,
        raw_reference=f"provider:{call.provider_id};request:{call.request_id}",
        normalized_value=normalized_value,
        calculation_version="b3-live-1.1.0",
        engine_version="1.1.0",
        confidence=confidence,
        freshness=freshness,
        license_classification="direct-chain-state",
    )


def _pct_change(current: int | float | None, previous: int | float | None) -> float | None:
    if current is None or previous in (None, 0):
        return None
    return ((float(current) - float(previous)) / abs(float(previous))) * 100.0


def _decode_signed_word(word_hex: str) -> int:
    value = int(word_hex, 16)
    return value - (1 << 256) if value >= (1 << 255) else value


def _read_chainlink(rpc, address: str) -> tuple[dict[str, Any], list[tuple[ProviderCall, str]], datetime | None, FreshnessStatus]:
    decimals_call = rpc.call("eth_call", [{"to": address, "data": DECIMALS_SELECTOR}, "latest"])
    round_call = rpc.call("eth_call", [{"to": address, "data": LATEST_ROUND_DATA_SELECTOR}, "latest"])
    decimals = hex_to_int(decimals_call.result)
    raw = str(round_call.result)
    clean = raw[2:] if raw.startswith("0x") else raw
    if decimals is None or len(clean) < 64 * 5:
        raise ProviderError("Malformed Chainlink AggregatorV3 response", provider_id=round_call.provider_id, code="MALFORMED_RESPONSE")
    words = [clean[i : i + 64] for i in range(0, 64 * 5, 64)]
    round_id = int(words[0], 16)
    answer_raw = _decode_signed_word(words[1])
    started_at = int(words[2], 16)
    updated_at = int(words[3], 16)
    answered_in_round = int(words[4], 16)
    answer = answer_raw / (10 ** decimals)
    observed = datetime.fromtimestamp(updated_at, tz=timezone.utc) if updated_at > 0 else None
    age = (datetime.now(timezone.utc) - observed).total_seconds() if observed else None
    freshness = FreshnessStatus.LIVE if age is not None and age <= 120 else FreshnessStatus.CURRENT if age is not None and age <= 900 else FreshnessStatus.RECENT if age is not None and age <= 3600 else FreshnessStatus.STALE if age is not None and age <= 21600 else FreshnessStatus.EXPIRED if age is not None else FreshnessStatus.UNKNOWN
    normalized = {
        "feed": address,
        "decimals": decimals,
        "round_id": round_id,
        "answer": answer,
        "answer_raw": answer_raw,
        "started_at": started_at,
        "updated_at": updated_at,
        "answered_in_round": answered_in_round,
        "age_seconds": age,
    }
    return normalized, [(decimals_call, "decimals()"), (round_call, "latestRoundData()")], observed, freshness


def run_live_b3(data: dict[str, Any]) -> EngineResult:
    try:
        chain = normalize_chain(data.get("chain") or data.get("network"))
    except ValueError as exc:
        return EngineResult(engine_id=EngineId.B3, engine_version="1.1.0", status=AnalysisStatus.UNSUPPORTED, risk_score=0, data_confidence=0, engine_confidence=0, severity=Severity.UNKNOWN, summary=str(exc), warnings=["No live monitoring snapshot was collected."], missing_data=["supported chain"], provider_consensus="UNAVAILABLE", demo=False)

    entity = data.get("entity") or data.get("address") or data.get("wallet") or data.get("contract")
    if not _valid_address(entity):
        return EngineResult(engine_id=EngineId.B3, engine_version="1.1.0", status=AnalysisStatus.INSUFFICIENT_DATA, risk_score=0, data_confidence=0, engine_confidence=0, severity=Severity.UNKNOWN, summary="B3 live monitoring requires a valid EVM entity address.", warnings=["No fabricated threat state was produced."], missing_data=["entity address"], provider_consensus="UNAVAILABLE", demo=False)

    token_contract = data.get("token_contract")
    oracle_feed = data.get("oracle_feed")
    if token_contract and not _valid_address(token_contract):
        return EngineResult(engine_id=EngineId.B3, engine_version="1.1.0", status=AnalysisStatus.INSUFFICIENT_DATA, risk_score=0, data_confidence=0, engine_confidence=0, severity=Severity.UNKNOWN, summary="token_contract must be a valid EVM address.", missing_data=["valid token_contract"], demo=False)
    if oracle_feed and not _valid_address(oracle_feed):
        return EngineResult(engine_id=EngineId.B3, engine_version="1.1.0", status=AnalysisStatus.INSUFFICIENT_DATA, risk_score=0, data_confidence=0, engine_confidence=0, severity=Severity.UNKNOWN, summary="oracle_feed must be a valid EVM address.", missing_data=["valid oracle_feed"], demo=False)

    try:
        rpc_provider, rpc, chain_probe, fallback_errors = select_rpc_client(chain.key)
    except ProviderError as exc:
        return EngineResult(engine_id=EngineId.B3, engine_version="1.1.0", status=AnalysisStatus.PROVIDER_UNAVAILABLE, risk_score=0, data_confidence=0, engine_confidence=0, severity=Severity.UNKNOWN, summary=f"B3 could not obtain live chain state for {chain.name}.", warnings=[str(exc)], missing_data=["healthy EVM RPC"], provider_consensus="UNAVAILABLE", provider_status=[{"provider_id": exc.provider_id, "status": exc.code}], demo=False)

    evidence: list[EvidenceRecord] = []
    provider_status = [{"provider_id": x["provider_id"], "status": "FAILED_OR_UNAVAILABLE", "detail": x["error"]} for x in fallback_errors]
    provider_status.append({"provider_id": rpc_provider, "status": "HEALTHY", "latency_ms": round(chain_probe.latency_ms, 2)})
    evidence.append(_evidence(chain_probe, source_type="direct_state", normalized_value={"chain_id": chain.chain_id}, chain_id=chain.chain_id, block_number=None, method="eth_chainId"))

    try:
        block_call = rpc.call("eth_blockNumber")
        block = hex_to_int(block_call.result)
        balance_call = rpc.call("eth_getBalance", [entity, "latest"])
        balance = hex_to_int(balance_call.result) or 0
        code_call = rpc.call("eth_getCode", [entity, "latest"])
        code = str(code_call.result or "0x")
    except ProviderError as exc:
        return EngineResult(engine_id=EngineId.B3, engine_version="1.1.0", status=AnalysisStatus.PROVIDER_UNAVAILABLE, risk_score=0, data_confidence=20, engine_confidence=0, severity=Severity.UNKNOWN, summary="B3 RPC was selected but the monitoring snapshot failed.", warnings=[str(exc)], missing_data=["current chain snapshot"], provider_consensus="UNAVAILABLE", provider_status=provider_status + [{"provider_id": exc.provider_id, "status": exc.code}], evidence=evidence, demo=False)

    code_bytes = bytes.fromhex(code[2:]) if code.startswith("0x") and len(code) % 2 == 0 else code.encode()
    code_hash = hashlib.sha256(code_bytes).hexdigest()
    snapshot: dict[str, Any] = {
        "chain_id": chain.chain_id,
        "block_number": block,
        "entity": entity,
        "native_balance_wei": balance,
        "code_size_bytes": len(code_bytes),
        "code_sha256": code_hash,
        "captured_at": datetime.now(timezone.utc).isoformat(),
    }
    evidence.extend([
        _evidence(block_call, source_type="direct_state", normalized_value={"block_number": block}, chain_id=chain.chain_id, block_number=block, method="eth_blockNumber"),
        _evidence(balance_call, source_type="direct_state", normalized_value={"entity": entity, "native_balance_wei": balance}, chain_id=chain.chain_id, block_number=block, method="eth_getBalance"),
        _evidence(code_call, source_type="direct_state", normalized_value={"entity": entity, "code_size_bytes": len(code_bytes), "code_sha256": code_hash}, chain_id=chain.chain_id, block_number=block, method="eth_getCode"),
    ])

    warnings: list[str] = []
    signals: list[dict[str, Any]] = []
    blockers: list[str] = []
    mitigations: list[str] = []
    missing: list[str] = []
    risk = 10.0

    if token_contract:
        try:
            supply_call = rpc.call("eth_call", [{"to": token_contract, "data": TOTAL_SUPPLY_SELECTOR}, "latest"])
            total_supply = hex_to_int(supply_call.result)
            snapshot["token_contract"] = token_contract
            snapshot["token_total_supply_raw"] = total_supply
            evidence.append(_evidence(supply_call, source_type="direct_state", normalized_value={"token_contract": token_contract, "total_supply_raw": total_supply}, chain_id=chain.chain_id, block_number=block, method="totalSupply()"))
        except ProviderError as exc:
            missing.append("token total supply")
            warnings.append(f"Token supply state could not be read: {exc}")

    oracle_freshness = FreshnessStatus.UNKNOWN
    if oracle_feed:
        try:
            oracle, calls, observed_at, oracle_freshness = _read_chainlink(rpc, oracle_feed)
            snapshot["oracle"] = oracle
            for call, method in calls:
                evidence.append(_evidence(call, source_type="direct_oracle_state", normalized_value=oracle, chain_id=chain.chain_id, block_number=block, method=method, confidence=96, observed_at=observed_at, freshness=oracle_freshness))
            max_age = _num(data.get("oracle_max_age_seconds"), 3600.0) or 3600.0
            if oracle["answer"] <= 0:
                blockers.append("Oracle returned a non-positive answer.")
                signals.append({"type": "oracle_invalid_answer", "severity": "critical", "answer": oracle["answer"]})
                risk = max(risk, 90)
                mitigations.append("Do not rely on this oracle state until a valid positive round is observed and the dependency is verified.")
            if oracle.get("age_seconds") is not None and float(oracle["age_seconds"]) > max_age:
                signals.append({"type": "oracle_stale", "severity": "high", "age_seconds": oracle["age_seconds"], "threshold_seconds": max_age})
                warnings.append("Oracle update age exceeds the configured monitoring threshold.")
                risk = max(risk, 65)
                mitigations.append("Pause dependent execution until the oracle feed updates or the protocol's verified fallback mechanism is confirmed.")
            if oracle["answered_in_round"] < oracle["round_id"]:
                signals.append({"type": "oracle_round_incomplete", "severity": "high"})
                warnings.append("Oracle answeredInRound is behind the current round id.")
                risk = max(risk, 70)
        except (ProviderError, ValueError, OverflowError) as exc:
            missing.append("oracle state")
            warnings.append(f"Oracle state could not be normalized: {exc}")

    previous = data.get("previous_snapshot") if isinstance(data.get("previous_snapshot"), dict) else None
    if previous:
        balance_delta = _pct_change(balance, previous.get("native_balance_wei"))
        if balance_delta is not None:
            snapshot["native_balance_change_pct"] = balance_delta
            threshold = abs(_num(data.get("balance_change_threshold_pct"), 20.0) or 20.0)
            if balance_delta <= -threshold:
                signals.append({"type": "large_native_balance_withdrawal", "severity": "high", "change_pct": balance_delta, "threshold_pct": threshold})
                warnings.append("Native balance decreased beyond the configured monitoring threshold.")
                risk = max(risk, 60)
                mitigations.append("Review recent transactions and counterparties before further capital movement.")
        old_hash = previous.get("code_sha256")
        if old_hash and old_hash != code_hash:
            signals.append({"type": "runtime_bytecode_changed", "severity": "critical", "previous_sha256": old_hash, "current_sha256": code_hash})
            blockers.append("Runtime bytecode changed since the previous B3 snapshot.")
            risk = max(risk, 88)
            mitigations.append("Treat the entity as materially changed until upgrade/redeployment provenance is verified.")
        if snapshot.get("token_total_supply_raw") is not None:
            supply_delta = _pct_change(snapshot.get("token_total_supply_raw"), previous.get("token_total_supply_raw"))
            if supply_delta is not None:
                snapshot["token_supply_change_pct"] = supply_delta
                threshold = abs(_num(data.get("supply_change_threshold_pct"), 5.0) or 5.0)
                if abs(supply_delta) >= threshold:
                    signals.append({"type": "token_supply_change", "severity": "high", "change_pct": supply_delta, "threshold_pct": threshold})
                    warnings.append("Token total supply changed beyond the configured threshold.")
                    risk = max(risk, 55)
        prev_oracle = previous.get("oracle") if isinstance(previous.get("oracle"), dict) else None
        if prev_oracle and isinstance(snapshot.get("oracle"), dict):
            current_answer = _num(snapshot["oracle"].get("answer"))
            previous_answer = _num(prev_oracle.get("answer"))
            oracle_delta = _pct_change(current_answer, previous_answer)
            if oracle_delta is not None:
                snapshot["oracle_change_pct"] = oracle_delta
                threshold = abs(_num(data.get("oracle_change_threshold_pct"), 10.0) or 10.0)
                if abs(oracle_delta) >= threshold:
                    signals.append({"type": "oracle_large_change", "severity": "high", "change_pct": oracle_delta, "threshold_pct": threshold})
                    warnings.append("Oracle value moved beyond the configured snapshot-to-snapshot threshold.")
                    risk = max(risk, 55)
    else:
        missing.append("prior monitoring snapshot for change detection")

    if not oracle_feed:
        missing.append("verified oracle dependency/feed address")

    threat_intelligence_consumed = False
    threat_resolution = resolve_provider("threat", chain=chain.key)
    if threat_resolution.provider_id == "blockaid":
        try:
            call = BlockaidClient().scan_address(
                chain=chain.key,
                address=entity,
                domain=str(data.get("domain") or data.get("dapp_domain")) if (data.get("domain") or data.get("dapp_domain")) else None,
            )
            normalized_threat = normalize_blockaid(call.result)
            score_add, malicious, messages = blockaid_risk(normalized_threat)
            risk = max(risk, score_add if malicious else min(75.0, risk + score_add))
            warnings.extend(messages)
            signals.append({"type": "external_address_security", "provider": "blockaid", **normalized_threat})
            evidence.append(EvidenceRecord(
                evidence_id=str(uuid4()), provider="blockaid", source_type="external_threat_intelligence",
                provider_endpoint=call.endpoint, provider_request_id=call.request_id,
                retrieved_at=datetime.now(timezone.utc), observed_at=datetime.now(timezone.utc),
                block_number=block, chain_id=chain.chain_id, raw_reference=f"provider:blockaid;request:{call.request_id};address:{entity}",
                normalized_value=normalized_threat, calculation_version="b3-live-1.2.0", engine_version="1.2.0",
                confidence=90, freshness=FreshnessStatus.CURRENT, license_classification="external-provider-attributed",
            ))
            provider_status.append({"provider_id": "blockaid", "status": "HEALTHY", "latency_ms": round(call.latency_ms, 2)})
            threat_intelligence_consumed = True
            if malicious:
                blockers.append("Blockaid explicitly classified the monitored address as malicious.")
                mitigations.append("Escalate the monitored entity for immediate security review and suspend dependent execution until independently resolved.")
        except ProviderError as exc:
            provider_status.append({"provider_id": "blockaid", "status": exc.code, "detail": str(exc)})
            missing.append("Blockaid external threat intelligence")
    elif threat_resolution.provider_id == "hypernative":
        provider_status.append({"provider_id": "hypernative", "status": "CUSTOMER_SCHEMA_REQUIRED"})
        missing.append("Hypernative certified customer API/webhook contract")
        warnings.append("Hypernative is configured conceptually, but Rivexis will not invent its access-controlled customer request schema. Use the staging certification/integration boundary before consuming Hypernative evidence.")
    else:
        missing.append("commercial threat-intelligence feed (Hypernative/Blockaid) for exploit/phishing/security classifications")

    missing.append("continuous WebSocket/SSE event ingestion; this endpoint remains a point-in-time snapshot even when external screening is available")

    data_conf = 78 if previous else 68
    if threat_intelligence_consumed:
        data_conf = min(94, data_conf + 10)
    if oracle_feed and oracle_freshness in {FreshnessStatus.LIVE, FreshnessStatus.CURRENT}:
        data_conf += 6
    if signals:
        summary = f"B3 collected a live {chain.name} monitoring snapshot and detected {len(signals)} threshold or state-change signal(s)."
    else:
        summary = f"B3 collected a live {chain.name} monitoring snapshot. No configured point-in-time change threshold fired; this does not establish absence of external threats."
    return EngineResult(
        engine_id=EngineId.B3,
        engine_version="1.2.0",
        block_reference=block,
        status=AnalysisStatus.PARTIAL,
        risk_score=min(100.0, risk),
        data_confidence=min(100.0, data_conf),
        engine_confidence=(80 if previous else 68) if threat_intelligence_consumed else (70 if previous else 58),
        severity=_severity(risk),
        summary=summary,
        metrics={"snapshot": snapshot, "signals_detected": len(signals)},
        signals=signals,
        warnings=warnings,
        hard_blockers=blockers,
        mitigations=mitigations,
        safer_alternatives=["Configure a continuous threat provider and event stream for real-time incident coverage."],
        evidence=evidence,
        provider_consensus="MULTI_SOURCE" if threat_intelligence_consumed else ("SINGLE SOURCE" if not oracle_feed else "MULTI_SIGNAL_SINGLE_RPC"),
        data_freshness={"status": "LIVE", "block_number": block, "oracle": oracle_freshness.value if oracle_feed else "NOT_PROVIDED"},
        missing_data=missing,
        provider_status=provider_status,
        assumptions=["RPC snapshots detect state changes only when compared with a prior snapshot; they are not a replacement for continuous threat intelligence.", "An oracle feed supplied by the caller is monitored as an address; Rivexis does not assert that it is the protocol's authoritative oracle unless separately verified."],
        demo=False,
    )
