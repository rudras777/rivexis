from __future__ import annotations

import hashlib
import math
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
UINT256_MAX = 2**256 - 1
FUTURE_TIMESTAMP_TOLERANCE_SECONDS = 300


def _valid_address(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 42 or not value.startswith("0x"):
        return False
    try:
        int(value[2:], 16)
        return True
    except ValueError:
        return False


def _num(value: Any, default: float | None = None) -> float | None:
    if value in (None, "") or isinstance(value, bool):
        return default
    try:
        parsed = float(value)
    except (TypeError, ValueError, OverflowError):
        return default
    return parsed if math.isfinite(parsed) else default


def _nonnegative_int(value: Any, *, maximum: int = UINT256_MAX) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        parsed = value
    elif isinstance(value, str) and value.isdigit():
        try:
            parsed = int(value)
        except ValueError:
            return None
    else:
        return None
    return parsed if 0 <= parsed <= maximum else None


def _rpc_uint(value: Any, *, maximum: int = UINT256_MAX) -> int | None:
    try:
        parsed = hex_to_int(value)
    except (TypeError, ValueError, OverflowError):
        return None
    if parsed is None or isinstance(parsed, bool):
        return None
    return parsed if 0 <= parsed <= maximum else None


def _bytecode(value: Any) -> bytes | None:
    if not isinstance(value, str) or not value.startswith("0x"):
        return None
    raw = value[2:]
    if len(raw) % 2:
        return None
    try:
        return bytes.fromhex(raw)
    except ValueError:
        return None


def _valid_sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
        return True
    except ValueError:
        return False


def _monitor_thresholds(data: dict[str, Any]) -> tuple[dict[str, float] | None, str | None]:
    specs = {
        "oracle_max_age_seconds": (3600.0, False),
        "balance_change_threshold_pct": (20.0, True),
        "supply_change_threshold_pct": (5.0, True),
        "oracle_change_threshold_pct": (10.0, True),
    }
    out: dict[str, float] = {}
    for key, (default, allow_zero) in specs.items():
        raw = data.get(key)
        if raw in (None, ""):
            out[key] = default
            continue
        parsed = _num(raw)
        if parsed is None or parsed < 0 or (not allow_zero and parsed <= 0):
            return None, key
        out[key] = parsed
    return out, None


def _invalid(message: str, missing: str) -> EngineResult:
    return EngineResult(
        engine_id=EngineId.B3,
        engine_version="1.1.0",
        status=AnalysisStatus.INSUFFICIENT_DATA,
        risk_score=0,
        data_confidence=0,
        engine_confidence=0,
        severity=Severity.UNKNOWN,
        summary=message,
        warnings=["No live monitoring conclusion was produced from invalid input."],
        missing_data=[missing],
        provider_consensus="UNAVAILABLE",
        demo=False,
    )


def _severity(score: float) -> Severity:
    return (
        Severity.CRITICAL
        if score >= 80
        else Severity.HIGH
        if score >= 60
        else Severity.MODERATE
        if score >= 35
        else Severity.LOW
    )


def _evidence(
    call: ProviderCall,
    *,
    source_type: str,
    normalized_value: Any,
    chain_id: int,
    block_number: int | None,
    method: str,
    confidence: float = 99,
    observed_at: datetime | None = None,
    freshness: FreshnessStatus = FreshnessStatus.LIVE,
) -> EvidenceRecord:
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
    current_num = _num(current)
    previous_num = _num(previous)
    if current_num is None or previous_num in (None, 0):
        return None
    result = ((current_num - previous_num) / abs(previous_num)) * 100.0
    return result if math.isfinite(result) else None


def _decode_signed_word(word_hex: str) -> int:
    value = int(word_hex, 16)
    return value - (1 << 256) if value >= (1 << 255) else value


def _read_chainlink(
    rpc, address: str
) -> tuple[dict[str, Any], list[tuple[ProviderCall, str]], datetime | None, FreshnessStatus]:
    decimals_call = rpc.call(
        "eth_call", [{"to": address, "data": DECIMALS_SELECTOR}, "latest"]
    )
    round_call = rpc.call(
        "eth_call", [{"to": address, "data": LATEST_ROUND_DATA_SELECTOR}, "latest"]
    )
    decimals = _rpc_uint(decimals_call.result, maximum=255)
    raw = round_call.result
    if not isinstance(raw, str) or not raw.startswith("0x"):
        raise ProviderError(
            "Malformed Chainlink AggregatorV3 response",
            provider_id=round_call.provider_id,
            code="MALFORMED_RESPONSE",
        )
    clean = raw[2:]
    if decimals is None or len(clean) != 64 * 5:
        raise ProviderError(
            "Malformed Chainlink AggregatorV3 response",
            provider_id=round_call.provider_id,
            code="MALFORMED_RESPONSE",
        )
    try:
        int(clean, 16)
        words = [clean[i : i + 64] for i in range(0, 64 * 5, 64)]
        round_id = int(words[0], 16)
        answer_raw = _decode_signed_word(words[1])
        started_at = int(words[2], 16)
        updated_at = int(words[3], 16)
        answered_in_round = int(words[4], 16)
    except ValueError as exc:
        raise ProviderError(
            "Malformed Chainlink AggregatorV3 response",
            provider_id=round_call.provider_id,
            code="MALFORMED_RESPONSE",
        ) from exc

    answer = answer_raw / (10**decimals)
    observed: datetime | None = None
    age: float | None = None
    timestamp_status = "MISSING"
    if updated_at > 0:
        try:
            observed = datetime.fromtimestamp(updated_at, tz=timezone.utc)
        except (OverflowError, OSError, ValueError) as exc:
            raise ProviderError(
                "Chainlink updatedAt is outside the supported timestamp range",
                provider_id=round_call.provider_id,
                code="MALFORMED_RESPONSE",
            ) from exc
        age = (datetime.now(timezone.utc) - observed).total_seconds()
        timestamp_status = (
            "FUTURE"
            if age < -FUTURE_TIMESTAMP_TOLERANCE_SECONDS
            else "OBSERVED"
        )

    effective_age = max(0.0, age) if age is not None else None
    if timestamp_status == "FUTURE":
        freshness = FreshnessStatus.UNKNOWN
    elif effective_age is None:
        freshness = FreshnessStatus.UNKNOWN
    elif effective_age <= 120:
        freshness = FreshnessStatus.LIVE
    elif effective_age <= 900:
        freshness = FreshnessStatus.CURRENT
    elif effective_age <= 3600:
        freshness = FreshnessStatus.RECENT
    elif effective_age <= 21600:
        freshness = FreshnessStatus.STALE
    else:
        freshness = FreshnessStatus.EXPIRED

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
        "timestamp_status": timestamp_status,
    }
    return (
        normalized,
        [(decimals_call, "decimals()"), (round_call, "latestRoundData()")],
        observed,
        freshness,
    )


def run_live_b3(data: dict[str, Any]) -> EngineResult:
    try:
        chain = normalize_chain(data.get("chain") or data.get("network"))
    except ValueError as exc:
        return EngineResult(
            engine_id=EngineId.B3,
            engine_version="1.1.0",
            status=AnalysisStatus.UNSUPPORTED,
            risk_score=0,
            data_confidence=0,
            engine_confidence=0,
            severity=Severity.UNKNOWN,
            summary=str(exc),
            warnings=["No live monitoring snapshot was collected."],
            missing_data=["supported chain"],
            provider_consensus="UNAVAILABLE",
            demo=False,
        )

    entity = data.get("entity") or data.get("address") or data.get("wallet") or data.get("contract")
    if not _valid_address(entity):
        return _invalid("B3 live monitoring requires a valid EVM entity address.", "entity address")

    token_contract = data.get("token_contract")
    oracle_feed = data.get("oracle_feed")
    if token_contract and not _valid_address(token_contract):
        return _invalid("token_contract must be a valid EVM address.", "valid token_contract")
    if oracle_feed and not _valid_address(oracle_feed):
        return _invalid("oracle_feed must be a valid EVM address.", "valid oracle_feed")

    thresholds, invalid_threshold = _monitor_thresholds(data)
    if thresholds is None:
        return _invalid(
            f"{invalid_threshold} must be a finite non-negative monitoring threshold"
            + (" greater than zero." if invalid_threshold == "oracle_max_age_seconds" else "."),
            f"valid {invalid_threshold}",
        )

    try:
        rpc_provider, rpc, chain_probe, fallback_errors = select_rpc_client(chain.key)
    except ProviderError as exc:
        return EngineResult(
            engine_id=EngineId.B3,
            engine_version="1.1.0",
            status=AnalysisStatus.PROVIDER_UNAVAILABLE,
            risk_score=0,
            data_confidence=0,
            engine_confidence=0,
            severity=Severity.UNKNOWN,
            summary=f"B3 could not obtain live chain state for {chain.name}.",
            warnings=[str(exc)],
            missing_data=["healthy EVM RPC"],
            provider_consensus="UNAVAILABLE",
            provider_status=[{"provider_id": exc.provider_id, "status": exc.code}],
            demo=False,
        )

    evidence: list[EvidenceRecord] = []
    provider_status = [
        {
            "provider_id": row["provider_id"],
            "status": "FAILED_OR_UNAVAILABLE",
            "detail": row["error"],
        }
        for row in fallback_errors
    ]
    provider_status.append(
        {
            "provider_id": rpc_provider,
            "status": "HEALTHY",
            "latency_ms": round(chain_probe.latency_ms, 2),
        }
    )
    evidence.append(
        _evidence(
            chain_probe,
            source_type="direct_state",
            normalized_value={"chain_id": chain.chain_id},
            chain_id=chain.chain_id,
            block_number=None,
            method="eth_chainId",
        )
    )

    try:
        block_call = rpc.call("eth_blockNumber")
        block = _rpc_uint(block_call.result)
        balance_call = rpc.call("eth_getBalance", [entity, "latest"])
        balance = _rpc_uint(balance_call.result)
        code_call = rpc.call("eth_getCode", [entity, "latest"])
        code_bytes = _bytecode(code_call.result)
        if block is None or balance is None or code_bytes is None:
            raise ProviderError(
                "RPC returned malformed block, balance, or bytecode state",
                provider_id=rpc_provider,
                code="MALFORMED_RESPONSE",
            )
    except ProviderError as exc:
        return EngineResult(
            engine_id=EngineId.B3,
            engine_version="1.1.0",
            status=AnalysisStatus.PROVIDER_UNAVAILABLE,
            risk_score=0,
            data_confidence=20,
            engine_confidence=0,
            severity=Severity.UNKNOWN,
            summary="B3 RPC was selected but the monitoring snapshot failed.",
            warnings=[str(exc)],
            missing_data=["current chain snapshot"],
            provider_consensus="UNAVAILABLE",
            provider_status=provider_status
            + [{"provider_id": exc.provider_id, "status": exc.code}],
            evidence=evidence,
            demo=False,
        )

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
    evidence.extend(
        [
            _evidence(
                block_call,
                source_type="direct_state",
                normalized_value={"block_number": block},
                chain_id=chain.chain_id,
                block_number=block,
                method="eth_blockNumber",
            ),
            _evidence(
                balance_call,
                source_type="direct_state",
                normalized_value={"entity": entity, "native_balance_wei": balance},
                chain_id=chain.chain_id,
                block_number=block,
                method="eth_getBalance",
            ),
            _evidence(
                code_call,
                source_type="direct_state",
                normalized_value={
                    "entity": entity,
                    "code_size_bytes": len(code_bytes),
                    "code_sha256": code_hash,
                },
                chain_id=chain.chain_id,
                block_number=block,
                method="eth_getCode",
            ),
        ]
    )

    warnings: list[str] = []
    signals: list[dict[str, Any]] = []
    blockers: list[str] = []
    mitigations: list[str] = []
    missing: list[str] = []
    risk = 10.0

    if token_contract:
        try:
            supply_call = rpc.call(
                "eth_call",
                [{"to": token_contract, "data": TOTAL_SUPPLY_SELECTOR}, "latest"],
            )
            total_supply = _rpc_uint(supply_call.result)
            if total_supply is None:
                raise ProviderError(
                    "Token totalSupply() returned a malformed EVM quantity",
                    provider_id=supply_call.provider_id,
                    code="MALFORMED_RESPONSE",
                )
            snapshot["token_contract"] = token_contract
            snapshot["token_total_supply_raw"] = total_supply
            evidence.append(
                _evidence(
                    supply_call,
                    source_type="direct_state",
                    normalized_value={
                        "token_contract": token_contract,
                        "total_supply_raw": total_supply,
                    },
                    chain_id=chain.chain_id,
                    block_number=block,
                    method="totalSupply()",
                )
            )
        except ProviderError as exc:
            missing.append("token total supply")
            warnings.append(f"Token supply state could not be normalized: {exc}")

    oracle_freshness = FreshnessStatus.UNKNOWN
    oracle_threshold_stale = False
    if oracle_feed:
        try:
            oracle, calls, observed_at, oracle_freshness = _read_chainlink(rpc, oracle_feed)
            snapshot["oracle"] = oracle
            for call, method in calls:
                evidence.append(
                    _evidence(
                        call,
                        source_type="direct_oracle_state",
                        normalized_value=oracle,
                        chain_id=chain.chain_id,
                        block_number=block,
                        method=method,
                        confidence=96,
                        observed_at=observed_at,
                        freshness=oracle_freshness,
                    )
                )
            if oracle["timestamp_status"] == "FUTURE":
                warnings.append(
                    "Oracle updatedAt is materially in the future; Rivexis did not classify that observation as fresh."
                )
                missing.append("credible oracle observation timestamp")
            if oracle["answer"] <= 0:
                blockers.append("Oracle returned a non-positive answer.")
                signals.append(
                    {
                        "type": "oracle_invalid_answer",
                        "severity": "critical",
                        "answer": oracle["answer"],
                    }
                )
                risk = max(risk, 90)
                mitigations.append(
                    "Do not rely on this oracle state until a valid positive round is observed and the dependency is verified."
                )
            if (
                oracle.get("age_seconds") is not None
                and oracle["age_seconds"] >= 0
                and float(oracle["age_seconds"])
                > thresholds["oracle_max_age_seconds"]
            ):
                oracle_threshold_stale = True
                signals.append(
                    {
                        "type": "oracle_stale",
                        "severity": "high",
                        "age_seconds": oracle["age_seconds"],
                        "threshold_seconds": thresholds["oracle_max_age_seconds"],
                    }
                )
                warnings.append(
                    "Oracle update age exceeds the configured monitoring threshold."
                )
                risk = max(risk, 65)
                mitigations.append(
                    "Pause dependent execution until the oracle feed updates or the protocol's verified fallback mechanism is confirmed."
                )
            if oracle["answered_in_round"] < oracle["round_id"]:
                signals.append({"type": "oracle_round_incomplete", "severity": "high"})
                warnings.append("Oracle answeredInRound is behind the current round id.")
                risk = max(risk, 70)
        except (ProviderError, ValueError, OverflowError) as exc:
            missing.append("oracle state")
            warnings.append(f"Oracle state could not be normalized: {exc}")

    previous = data.get("previous_snapshot") if isinstance(data.get("previous_snapshot"), dict) else None
    previous_integrity_gaps = 0
    if previous:
        previous_balance = _nonnegative_int(previous.get("native_balance_wei"))
        if previous_balance is None:
            previous_integrity_gaps += 1
            missing.append("valid previous native balance")
            warnings.append(
                "Previous snapshot native_balance_wei is missing or malformed; native-balance delta was not calculated."
            )
        else:
            balance_delta = _pct_change(balance, previous_balance)
            if balance_delta is not None:
                snapshot["native_balance_change_pct"] = balance_delta
                if balance_delta <= -thresholds["balance_change_threshold_pct"]:
                    signals.append(
                        {
                            "type": "large_native_balance_withdrawal",
                            "severity": "high",
                            "change_pct": balance_delta,
                            "threshold_pct": thresholds[
                                "balance_change_threshold_pct"
                            ],
                        }
                    )
                    warnings.append(
                        "Native balance decreased beyond the configured monitoring threshold."
                    )
                    risk = max(risk, 60)
                    mitigations.append(
                        "Review recent transactions and counterparties before further capital movement."
                    )

        old_hash = previous.get("code_sha256")
        if not _valid_sha256(old_hash):
            previous_integrity_gaps += 1
            missing.append("valid previous runtime bytecode hash")
            warnings.append(
                "Previous snapshot code_sha256 is missing or malformed; bytecode-change detection was not run."
            )
        elif old_hash.lower() != code_hash:
            signals.append(
                {
                    "type": "runtime_bytecode_changed",
                    "severity": "critical",
                    "previous_sha256": old_hash.lower(),
                    "current_sha256": code_hash,
                }
            )
            blockers.append("Runtime bytecode changed since the previous B3 snapshot.")
            risk = max(risk, 88)
            mitigations.append(
                "Treat the entity as materially changed until upgrade/redeployment provenance is verified."
            )

        if snapshot.get("token_total_supply_raw") is not None:
            previous_supply = _nonnegative_int(previous.get("token_total_supply_raw"))
            if previous_supply is None:
                previous_integrity_gaps += 1
                missing.append("valid previous token total supply")
                warnings.append(
                    "Previous snapshot token_total_supply_raw is missing or malformed; supply delta was not calculated."
                )
            else:
                supply_delta = _pct_change(
                    snapshot.get("token_total_supply_raw"), previous_supply
                )
                if supply_delta is not None:
                    snapshot["token_supply_change_pct"] = supply_delta
                    if abs(supply_delta) >= thresholds["supply_change_threshold_pct"]:
                        signals.append(
                            {
                                "type": "token_supply_change",
                                "severity": "high",
                                "change_pct": supply_delta,
                                "threshold_pct": thresholds[
                                    "supply_change_threshold_pct"
                                ],
                            }
                        )
                        warnings.append(
                            "Token total supply changed beyond the configured threshold."
                        )
                        risk = max(risk, 55)

        prev_oracle = previous.get("oracle") if isinstance(previous.get("oracle"), dict) else None
        if prev_oracle and isinstance(snapshot.get("oracle"), dict):
            current_answer = _num(snapshot["oracle"].get("answer"))
            previous_answer = _num(prev_oracle.get("answer"))
            if current_answer is None or previous_answer is None:
                previous_integrity_gaps += 1
                missing.append("valid previous oracle answer")
                warnings.append(
                    "Previous/current oracle answer is non-finite or malformed; oracle delta was not calculated."
                )
            else:
                oracle_delta = _pct_change(current_answer, previous_answer)
                if oracle_delta is not None:
                    snapshot["oracle_change_pct"] = oracle_delta
                    if abs(oracle_delta) >= thresholds["oracle_change_threshold_pct"]:
                        signals.append(
                            {
                                "type": "oracle_large_change",
                                "severity": "high",
                                "change_pct": oracle_delta,
                                "threshold_pct": thresholds[
                                    "oracle_change_threshold_pct"
                                ],
                            }
                        )
                        warnings.append(
                            "Oracle value moved beyond the configured snapshot-to-snapshot threshold."
                        )
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
                domain=(
                    str(data.get("domain") or data.get("dapp_domain"))
                    if (data.get("domain") or data.get("dapp_domain"))
                    else None
                ),
            )
            normalized_threat = normalize_blockaid(call.result)
            score_add, malicious, messages = blockaid_risk(normalized_threat)
            risk = max(risk, score_add if malicious else min(75.0, risk + score_add))
            warnings.extend(messages)
            signals.append(
                {
                    "type": "external_address_security",
                    "provider": "blockaid",
                    **normalized_threat,
                }
            )
            evidence.append(
                EvidenceRecord(
                    evidence_id=str(uuid4()),
                    provider="blockaid",
                    source_type="external_threat_intelligence",
                    provider_endpoint=call.endpoint,
                    provider_request_id=call.request_id,
                    retrieved_at=datetime.now(timezone.utc),
                    observed_at=datetime.now(timezone.utc),
                    block_number=block,
                    chain_id=chain.chain_id,
                    raw_reference=(
                        f"provider:blockaid;request:{call.request_id};address:{entity}"
                    ),
                    normalized_value=normalized_threat,
                    calculation_version="b3-live-1.1.0",
                    engine_version="1.1.0",
                    confidence=90,
                    freshness=FreshnessStatus.CURRENT,
                    license_classification="external-provider-attributed",
                )
            )
            provider_status.append(
                {
                    "provider_id": "blockaid",
                    "status": "HEALTHY",
                    "latency_ms": round(call.latency_ms, 2),
                }
            )
            threat_intelligence_consumed = True
            if malicious:
                blockers.append(
                    "Blockaid explicitly classified the monitored address as malicious."
                )
                mitigations.append(
                    "Escalate the monitored entity for immediate security review and suspend dependent execution until independently resolved."
                )
        except ProviderError as exc:
            provider_status.append(
                {
                    "provider_id": "blockaid",
                    "status": exc.code,
                    "detail": str(exc),
                }
            )
            missing.append("Blockaid external threat intelligence")
    elif threat_resolution.provider_id == "hypernative":
        provider_status.append(
            {"provider_id": "hypernative", "status": "CUSTOMER_SCHEMA_REQUIRED"}
        )
        missing.append("Hypernative certified customer API/webhook contract")
        warnings.append(
            "Hypernative is configured conceptually, but Rivexis will not invent its access-controlled customer request schema. Use the staging certification/integration boundary before consuming Hypernative evidence."
        )
    else:
        missing.append(
            "commercial threat-intelligence feed (Hypernative/Blockaid) for exploit/phishing/security classifications"
        )

    missing.append(
        "continuous WebSocket/SSE event ingestion; this endpoint remains a point-in-time snapshot even when external screening is available"
    )

    data_conf = 78 if previous else 68
    if previous_integrity_gaps:
        data_conf = max(50, data_conf - 5 * previous_integrity_gaps)
    if threat_intelligence_consumed:
        data_conf = min(94, data_conf + 10)
    if oracle_feed and oracle_freshness in {
        FreshnessStatus.LIVE,
        FreshnessStatus.CURRENT,
    }:
        data_conf += 6

    if signals:
        summary = (
            f"B3 collected a live {chain.name} monitoring snapshot and detected "
            f"{len(signals)} threshold, state-change, or external-security signal(s)."
        )
    else:
        summary = (
            f"B3 collected a live {chain.name} monitoring snapshot. No configured "
            "point-in-time change threshold fired; this does not establish absence of external threats."
        )

    status = (
        AnalysisStatus.STALE_DATA
        if oracle_feed
        and (
            oracle_threshold_stale
            or oracle_freshness in {FreshnessStatus.STALE, FreshnessStatus.EXPIRED}
        )
        else AnalysisStatus.PARTIAL
    )
    if status == AnalysisStatus.STALE_DATA:
        overall_freshness = (
            oracle_freshness.value
            if oracle_freshness in {FreshnessStatus.STALE, FreshnessStatus.EXPIRED}
            else FreshnessStatus.STALE.value
        )
    else:
        overall_freshness = FreshnessStatus.LIVE.value

    return EngineResult(
        engine_id=EngineId.B3,
        engine_version="1.1.0",
        block_reference=block,
        status=status,
        risk_score=min(100.0, risk),
        data_confidence=min(100.0, data_conf),
        engine_confidence=(80 if previous else 68)
        if threat_intelligence_consumed
        else (70 if previous else 58),
        severity=_severity(risk),
        summary=summary,
        metrics={"snapshot": snapshot, "signals_detected": len(signals)},
        signals=signals,
        warnings=warnings,
        hard_blockers=blockers,
        mitigations=mitigations,
        safer_alternatives=[
            "Configure a continuous threat provider and event stream for real-time incident coverage."
        ],
        evidence=evidence,
        provider_consensus=(
            "MULTI_SOURCE"
            if threat_intelligence_consumed
            else ("SINGLE_SOURCE" if not oracle_feed else "MULTI_SIGNAL_SINGLE_RPC")
        ),
        data_freshness={
            "status": overall_freshness,
            "block_number": block,
            "oracle": oracle_freshness.value if oracle_feed else "NOT_PROVIDED",
        },
        missing_data=sorted(set(missing)),
        provider_status=provider_status,
        assumptions=[
            "RPC snapshots detect state changes only when compared with a prior snapshot; they are not a replacement for continuous threat intelligence.",
            "An oracle feed supplied by the caller is monitored as an address; Rivexis does not assert that it is the protocol's authoritative oracle unless separately verified.",
        ],
        demo=False,
    )