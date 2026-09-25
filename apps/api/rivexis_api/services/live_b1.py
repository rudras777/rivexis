from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from typing import Any
from uuid import uuid4

from rivexis_api.chains import normalize_chain
from rivexis_api.models.engine import EngineResult
from rivexis_api.models.enums import AnalysisStatus, EngineId, FreshnessStatus, Severity
from rivexis_api.models.evidence import EvidenceRecord
from rivexis_api.provider_clients import EtherscanClient, ProviderCall, ProviderError, TenderlyClient, hex_to_int, quantity_to_hex
from rivexis_api.services.evm_decode import decode_common_calldata, decode_verified_abi_calldata, normalize_call_trace, summarize_prestate_diff
from rivexis_api.services.evm_events import normalize_standard_event_logs
from rivexis_api.providers import ADAPTERS, resolve_provider, select_rpc_client


def _valid_address(value: str | None) -> bool:
    if value is None:
        return True
    if not isinstance(value, str) or len(value) != 42 or not value.startswith("0x"):
        return False
    try:
        int(value[2:], 16)
        return True
    except ValueError:
        return False


def _valid_hash(value: str) -> bool:
    if not isinstance(value, str) or len(value) != 66 or not value.startswith("0x"):
        return False
    try:
        int(value[2:], 16)
        return True
    except ValueError:
        return False


def _safe_quantity(value: Any) -> int | None:
    try:
        return hex_to_int(value)
    except (TypeError, ValueError):
        return None


def _tx_for_rpc(raw: dict[str, Any]) -> dict[str, Any]:
    allowed = {"from", "to", "gas", "gasPrice", "maxFeePerGas", "maxPriorityFeePerGas", "value", "data", "input"}
    tx = {k: v for k, v in raw.items() if k in allowed and v is not None}
    if "input" in tx and "data" not in tx:
        tx["data"] = tx.pop("input")
    for key in ("gas", "gasPrice", "maxFeePerGas", "maxPriorityFeePerGas", "value"):
        if key in tx:
            tx[key] = quantity_to_hex(tx[key])
    tx.setdefault("data", "0x")
    return tx


def _evidence(
    call: ProviderCall,
    *,
    source_type: str,
    normalized_value: Any,
    chain_id: int,
    block_number: int | None,
    confidence: float,
    endpoint_method: str,
    freshness: FreshnessStatus = FreshnessStatus.LIVE,
) -> EvidenceRecord:
    return EvidenceRecord(
        evidence_id=str(uuid4()),
        provider=call.provider_id,
        source_type=source_type,
        provider_endpoint=endpoint_method,
        provider_request_id=call.request_id,
        retrieved_at=datetime.now(timezone.utc),
        observed_at=datetime.now(timezone.utc),
        block_number=block_number,
        chain_id=chain_id,
        raw_reference=f"provider:{call.provider_id};request:{call.request_id}",
        normalized_value=normalized_value,
        calculation_version="b1-live-1.8.0",
        engine_version="1.3.0",
        confidence=confidence,
        freshness=freshness,
        license_classification="external-provider-evidence",
    )


def _provider_status(provider_id: str, status: str, detail: str | None = None, latency_ms: float | None = None) -> dict[str, Any]:
    out: dict[str, Any] = {"provider_id": provider_id, "status": status}
    if detail:
        out["detail"] = detail
    if latency_ms is not None:
        out["latency_ms"] = round(latency_ms, 2)
    return out


def _tenderly_event_logs(body: object) -> tuple[list[Any] | None, str | None]:
    if not isinstance(body, dict):
        return None, None
    transaction = body.get("transaction") if isinstance(body.get("transaction"), dict) else {}
    simulation = body.get("simulation") if isinstance(body.get("simulation"), dict) else {}
    receipt = transaction.get("receipt") if isinstance(transaction.get("receipt"), dict) else {}
    transaction_info = transaction.get("transaction_info") if isinstance(transaction.get("transaction_info"), dict) else {}
    info_trace = transaction_info.get("call_trace") if isinstance(transaction_info.get("call_trace"), dict) else {}
    direct_trace = transaction.get("call_trace") if isinstance(transaction.get("call_trace"), dict) else {}
    candidates = [
        ("transaction.logs", transaction.get("logs")),
        ("transaction.receipt.logs", receipt.get("logs")),
        ("transaction.transaction_info.call_trace.logs", info_trace.get("logs")),
        ("transaction.call_trace.logs", direct_trace.get("logs")),
        ("simulation.logs", simulation.get("logs")),
        ("response.logs", body.get("logs")),
    ]
    first_empty: tuple[list[Any], str] | None = None
    for path, value in candidates:
        if isinstance(value, list):
            if value:
                return value, path
            if first_empty is None:
                first_empty = (value, path)
    return first_empty if first_empty is not None else (None, None)


def _event_effect_gaps(effects: dict[str, Any] | None) -> list[str]:
    if not effects or not effects.get("logs_available"):
        return [
            "canonical standard token/NFT event-log effects",
            "canonical standard approval event-log effects",
        ]
    gaps: list[str] = []
    if effects.get("malformed_log_count"):
        gaps.append("complete normalization of malformed event logs")
    if effects.get("unknown_log_count"):
        gaps.append("semantics for unrecognized/non-standard event logs")
    if effects.get("truncated"):
        gaps.append("complete expansion of large event-effect batches")
    return gaps


def _append_event_warnings(warnings: list[str], effects: dict[str, Any] | None) -> None:
    if not effects or not effects.get("logs_available"):
        return
    if effects.get("unknown_log_count"):
        warnings.append("Some emitted logs use unrecognized/non-standard signatures; Rivexis did not infer asset or approval semantics for them.")
    if effects.get("malformed_log_count"):
        warnings.append("Some standard-signature logs had malformed topic/data encoding and were excluded from canonical event effects.")
    if effects.get("truncated"):
        warnings.append("A large event batch exceeded the canonical output-row cap; total effect counts are retained while displayed rows are truncated.")


def _tenderly_success(body: dict[str, Any]) -> tuple[bool, str | None, int | None, dict[str, Any]]:
    transaction = body.get("transaction") if isinstance(body.get("transaction"), dict) else {}
    simulation = body.get("simulation") if isinstance(body.get("simulation"), dict) else {}
    error_info = transaction.get("error_info") if isinstance(transaction.get("error_info"), dict) else None
    success = not bool(error_info) and transaction.get("status", True) not in {False, 0, "0", "failed", "reverted"}
    revert_reason = None
    if error_info:
        revert_reason = str(error_info.get("error_message") or error_info.get("error_reason") or "Simulation reverted")
    gas_used = _safe_quantity(transaction.get("gas_used") or transaction.get("gasUsed") or simulation.get("gas_used"))
    event_logs, event_log_path = _tenderly_event_logs(body)
    summary = {
        "simulation_id": simulation.get("id"),
        "network_id": simulation.get("network_id") or body.get("network_id"),
        "block_number": simulation.get("block_number") or transaction.get("block_number"),
        "gas_used": gas_used,
        "status": "success" if success else "reverted",
        "revert_reason": revert_reason,
        "logs_count": len(event_logs) if event_logs is not None else None,
        "event_log_path": event_log_path,
    }
    return success, revert_reason, gas_used, summary


def run_live_b1(input_data: dict[str, Any]) -> EngineResult:
    try:
        chain = normalize_chain(input_data.get("chain") or input_data.get("network"))
    except ValueError as exc:
        return EngineResult(
            engine_id=EngineId.B1,
            engine_version="1.3.0",
            status=AnalysisStatus.UNSUPPORTED,
            risk_score=0,
            data_confidence=0,
            engine_confidence=0,
            severity=Severity.UNKNOWN,
            summary=str(exc),
            warnings=["No live simulation was executed."],
            missing_data=["supported chain"],
            provider_consensus="UNAVAILABLE",
        )

    tx_hash = input_data.get("transaction_hash") or input_data.get("tx_hash")
    transaction = input_data.get("transaction") if isinstance(input_data.get("transaction"), dict) else dict(input_data)
    for key in ("chain", "network", "transaction_hash", "tx_hash", "transaction", "block_tag", "state_block"):
        transaction.pop(key, None)

    if tx_hash and not _valid_hash(tx_hash):
        return _invalid("transaction_hash must be a 32-byte 0x-prefixed hexadecimal value")
    if not tx_hash and not transaction.get("to"):
        return _invalid("Provide transaction.to or transaction_hash for B1 live simulation")
    if not _valid_address(transaction.get("from")) or not _valid_address(transaction.get("to")):
        return _invalid("Transaction from/to must be valid EVM addresses")

    evidence: list[EvidenceRecord] = []
    provider_status: list[dict[str, Any]] = []
    warnings: list[str] = []
    assumptions: list[str] = []
    missing: list[str] = []
    block_number: int | None = None
    rpc_provider_id: str | None = None
    receipt_event_effects: dict[str, Any] | None = None

    try:
        rpc_provider_id, rpc, chain_probe, fallback_errors = select_rpc_client(chain.key)
        provider_status.extend(_provider_status(x["provider_id"], "FAILED_OR_UNAVAILABLE", x["error"]) for x in fallback_errors)
        provider_status.append(_provider_status(rpc_provider_id, "HEALTHY", f"chain_id={chain.chain_id}", chain_probe.latency_ms))
        evidence.append(_evidence(chain_probe, source_type="direct_state", normalized_value={"chain_id": chain.chain_id}, chain_id=chain.chain_id, block_number=None, confidence=99, endpoint_method="eth_chainId"))
        block_call = rpc.call("eth_blockNumber")
        block_number = _safe_quantity(block_call.result)
        if block_number is None:
            raise ProviderError("RPC returned a malformed block number", provider_id=rpc_provider_id, code="MALFORMED_RESPONSE")
        evidence.append(_evidence(block_call, source_type="direct_state", normalized_value={"block_number": block_number}, chain_id=chain.chain_id, block_number=block_number, confidence=99, endpoint_method="eth_blockNumber"))
    except ProviderError as exc:
        return EngineResult(
            engine_id=EngineId.B1,
            engine_version="1.3.0",
            status=AnalysisStatus.PROVIDER_UNAVAILABLE,
            risk_score=0,
            data_confidence=0,
            engine_confidence=0,
            severity=Severity.UNKNOWN,
            summary=f"B1 cannot run because no healthy RPC provider is available for {chain.name}.",
            warnings=["No fabricated blockchain state or simulation result was produced."],
            missing_data=["healthy EVM RPC provider"],
            provider_consensus="UNAVAILABLE",
            provider_status=[_provider_status(exc.provider_id, "UNAVAILABLE", f"{exc.code}: {exc}")],
        )

    if tx_hash:
        try:
            tx_call = rpc.call("eth_getTransactionByHash", [tx_hash])
            if tx_call.result is None:
                return EngineResult(
                    engine_id=EngineId.B1,
                    engine_version="1.3.0",
                    status=AnalysisStatus.INSUFFICIENT_DATA,
                    risk_score=0,
                    data_confidence=40,
                    engine_confidence=0,
                    severity=Severity.UNKNOWN,
                    summary="Transaction hash was not found by the selected RPC provider.",
                    warnings=["No transaction was simulated."],
                    missing_data=["transaction body"],
                    evidence=evidence,
                    provider_consensus="SINGLE SOURCE",
                    provider_status=provider_status,
                )
            if not isinstance(tx_call.result, dict):
                raise ProviderError("RPC returned a malformed transaction body", provider_id=rpc_provider_id, code="MALFORMED_RESPONSE")
            transaction = dict(tx_call.result)
            if not _valid_address(transaction.get("from")) or not _valid_address(transaction.get("to")):
                raise ProviderError("RPC transaction body contains malformed addresses", provider_id=rpc_provider_id, code="MALFORMED_RESPONSE")
            historical_block = _safe_quantity(transaction.get("blockNumber"))
            evidence.append(_evidence(tx_call, source_type="direct_state", normalized_value={k: transaction.get(k) for k in ("hash", "from", "to", "value", "input", "blockNumber")}, chain_id=chain.chain_id, block_number=historical_block, confidence=99, endpoint_method="eth_getTransactionByHash", freshness=FreshnessStatus.UNKNOWN if historical_block is not None else FreshnessStatus.LIVE))
            if historical_block is not None:
                block_number = historical_block
                assumptions.append("Historical replay targets the state immediately before the transaction block when supported by the provider.")

            receipt_call = rpc.call("eth_getTransactionReceipt", [tx_hash])
            if receipt_call.result is None:
                missing.append("mined transaction receipt/event logs")
            elif not isinstance(receipt_call.result, dict):
                warnings.append("Transaction receipt response was malformed; mined event effects were not inferred.")
                missing.append("mined transaction receipt/event logs")
            else:
                receipt = receipt_call.result
                logs = receipt.get("logs")
                if isinstance(logs, list):
                    receipt_event_effects = normalize_standard_event_logs(logs, source="mined_transaction_receipt", outcome="observed")
                    receipt_block = _safe_quantity(receipt.get("blockNumber")) or historical_block
                    receipt_status = _safe_quantity(receipt.get("status"))
                    evidence.append(_evidence(
                        receipt_call,
                        source_type="observed_transaction_receipt_events",
                        normalized_value={
                            "transaction_hash": tx_hash,
                            "receipt_status": receipt_status,
                            "event_effects": receipt_event_effects,
                        },
                        chain_id=chain.chain_id,
                        block_number=receipt_block,
                        confidence=99,
                        endpoint_method="eth_getTransactionReceipt",
                        freshness=FreshnessStatus.UNKNOWN,
                    ))
                    assumptions.append("For a mined transaction hash, canonical event effects prefer observed receipt logs over replay/simulation event logs.")
                    _append_event_warnings(warnings, receipt_event_effects)
                else:
                    warnings.append("Transaction receipt did not contain a usable log list; mined event effects were not inferred.")
                    missing.append("mined transaction receipt/event logs")
        except ProviderError as exc:
            warnings.append(f"Transaction lookup/receipt evidence failed: {exc.code}")
            missing.append("transaction lookup or receipt evidence")

    rpc_tx = _tx_for_rpc(transaction)
    calldata_decode = decode_common_calldata(rpc_tx.get("data"))
    verified_abi_decode: dict[str, Any] | None = None
    if calldata_decode.get("unlimited_approval_candidate"):
        warnings.append("Calldata is consistent with approve(address,uint256) using uint256 max; treat this as a potential unlimited approval until the target contract interface is verified.")
    if not rpc_tx.get("to"):
        return _invalid("Resolved transaction has no destination; contract-creation simulation is not enabled in this MVP path")

    etherscan = EtherscanClient()
    if etherscan.configured and rpc_tx.get("data") not in (None, "", "0x"):
        try:
            abi_call = etherscan.get_abi(chain, rpc_tx["to"])
            body = abi_call.result if isinstance(abi_call.result, dict) else {}
            abi_payload = body.get("result")
            verified_abi_decode = decode_verified_abi_calldata(rpc_tx.get("data"), abi_payload)
            provider_status.append(_provider_status("etherscan", "HEALTHY", "Verified ABI lookup completed", abi_call.latency_ms))
            evidence.append(_evidence(abi_call, source_type="verified_contract_abi", normalized_value={"decode": verified_abi_decode}, chain_id=chain.chain_id, block_number=block_number, confidence=96 if verified_abi_decode.get("status") == "DECODED_VERIFIED_ABI" else 82, endpoint_method="Etherscan getabi"))
            if verified_abi_decode.get("status") == "DECODED_VERIFIED_ABI":
                if calldata_decode.get("status") == "UNKNOWN_SELECTOR":
                    calldata_decode = verified_abi_decode
                else:
                    calldata_decode = {**calldata_decode, "verified_abi": verified_abi_decode}
        except ProviderError as exc:
            provider_status.append(_provider_status("etherscan", "FAILED_OR_UNAVAILABLE", f"{exc.code}: {exc}"))
            missing.append("verified contract ABI")
    elif rpc_tx.get("data") not in (None, "", "0x"):
        missing.append("verified contract ABI")

    # Prefer Tenderly for decoded/full simulation when configured. We do not use the Alchemy
    # legacy simulation endpoint because the provider announced deprecation effective 2026-09-30.
    sim_resolution = resolve_provider("simulation", chain=chain.key)
    tenderly_used = sim_resolution.provider_id == "tenderly"
    if tenderly_used:
        try:
            tenderly = TenderlyClient()
            historical_target = block_number - 1 if tx_hash and block_number and block_number > 0 else None
            sim_call = tenderly.simulate(chain, rpc_tx, block_number=historical_target)
            success, revert_reason, gas_used, normalized = _tenderly_success(sim_call.result)
            tenderly_logs, tenderly_log_path = _tenderly_event_logs(sim_call.result)
            tenderly_event_effects = (
                normalize_standard_event_logs(tenderly_logs, source="tenderly_simulation", outcome="predicted")
                if tenderly_logs is not None
                else None
            )
            canonical_event_effects = receipt_event_effects or tenderly_event_effects
            _append_event_warnings(warnings, tenderly_event_effects)
            provider_status.append(_provider_status("tenderly", "HEALTHY", "Simulation response received and core execution status normalized", sim_call.latency_ms))
            evidence.append(_evidence(sim_call, source_type="simulation", normalized_value=normalized, chain_id=chain.chain_id, block_number=normalized.get("block_number") or historical_target or block_number, confidence=94, endpoint_method="Tenderly Simulation API"))
            if tenderly_event_effects is not None:
                evidence.append(_evidence(
                    sim_call,
                    source_type="simulation_event_logs",
                    normalized_value={"event_log_path": tenderly_log_path, "event_effects": tenderly_event_effects},
                    chain_id=chain.chain_id,
                    block_number=normalized.get("block_number") or historical_target or block_number,
                    confidence=94,
                    endpoint_method="Tenderly Simulation API event logs",
                ))
            score = 90 if not success else 10
            blockers = [f"Simulation reverted: {revert_reason or 'revert detected'}"] if not success else []
            tenderly_missing = sorted(set(missing + [
                "decoded internal call tree normalization",
                "before/after contract-state diff normalization",
                *_event_effect_gaps(canonical_event_effects),
            ]))
            return EngineResult(
                engine_id=EngineId.B1,
                engine_version="1.3.0",
                block_reference=normalized.get("block_number") or historical_target or block_number,
                status=AnalysisStatus.PARTIAL,
                risk_score=score,
                data_confidence=94,
                engine_confidence=91,
                severity=Severity.CRITICAL if not success else Severity.LOW,
                summary=(
                    "Tenderly simulation predicts a revert; standard event effects were normalized when raw logs were available, while richer internal/state effects remain partial."
                    if not success
                    else "Tenderly simulation completed without an execution revert; standard ERC event effects were normalized when raw logs were available, while internal/state effects remain partial."
                ),
                metrics={
                    "chain": chain.key,
                    "chain_id": chain.chain_id,
                    "from": rpc_tx.get("from"),
                    "to": rpc_tx.get("to"),
                    "execution_success": success,
                    "revert_reason": revert_reason,
                    "gas_used": gas_used,
                    "simulation_mode": "tenderly",
                    "simulation": normalized,
                    "calldata_decode": calldata_decode,
                    "verified_abi_decode": verified_abi_decode,
                    "event_effects": canonical_event_effects,
                    "simulated_event_effects": tenderly_event_effects if receipt_event_effects is not None else None,
                    "event_effects_precedence": "mined_transaction_receipt" if receipt_event_effects is not None else ("tenderly_simulation" if tenderly_event_effects is not None else None),
                },
                warnings=warnings,
                hard_blockers=blockers,
                mitigations=(["Do not sign the transaction until the revert cause is corrected."] if not success else []),
                safer_alternatives=(["Correct transaction parameters and re-simulate against fresh state."] if not success else []),
                evidence=evidence,
                provider_consensus="MULTI_SOURCE" if rpc_provider_id else "SINGLE_SOURCE",
                data_freshness={"status": "LIVE", "block_number": normalized.get("block_number") or block_number, "chain": chain.key},
                missing_data=tenderly_missing,
                provider_status=provider_status,
                assumptions=assumptions + ["Raw event amounts/token IDs are preserved without inferring token decimals, symbols, prices or ownership beyond the emitted standard event."],
            )
        except ProviderError as exc:
            provider_status.append(_provider_status("tenderly", "FAILED", f"{exc.code}: {exc}"))
            warnings.append("Tenderly simulation failed; Rivexis degraded to standards-based RPC dry-run.")

    # Standards-based fallback: eth_call executes the message without broadcasting and
    # eth_estimateGas performs an execution dry-run. This proves basic execution/revert status,
    # but it does not emit transaction logs or provide a canonical asset/state change set.
    block_tag: str = str(input_data.get("block_tag") or "latest")
    if tx_hash and block_number and block_number > 0:
        block_tag = hex(block_number - 1)
    call_success = True
    revert_reason: str | None = None
    call_result: str | None = None
    gas_estimate: int | None = None
    try:
        call = rpc.call("eth_call", [rpc_tx, block_tag])
        call_result = call.result
        evidence.append(_evidence(call, source_type="direct_state_simulation", normalized_value={"execution_success": True, "return_data": call_result, "block_tag": block_tag}, chain_id=chain.chain_id, block_number=block_number, confidence=88, endpoint_method="eth_call"))
    except ProviderError as exc:
        call_success = False
        revert_reason = str(exc)
        warnings.append(f"eth_call failed/reverted: {exc}")
    try:
        gas_call = rpc.call("eth_estimateGas", [rpc_tx, block_tag])
        gas_estimate = _safe_quantity(gas_call.result)
        if gas_estimate is None:
            raise ProviderError("RPC returned a malformed gas estimate", provider_id=rpc_provider_id or "rpc", code="MALFORMED_RESPONSE")
        evidence.append(_evidence(gas_call, source_type="direct_state_simulation", normalized_value={"gas_estimate": gas_estimate, "block_tag": block_tag}, chain_id=chain.chain_id, block_number=block_number, confidence=88, endpoint_method="eth_estimateGas"))
    except ProviderError as exc:
        if call_success:
            warnings.append(f"Gas estimation unavailable: {exc.code}: {exc}")
        missing.append("gas estimate")

    call_trace = None
    state_diff = None
    trace_requested = bool(input_data.get("trace")) or os.getenv("RIVEXIS_B1_DEBUG_TRACE", "false").lower() == "true"
    state_diff_requested = bool(input_data.get("state_diff")) or os.getenv("RIVEXIS_B1_STATE_DIFF", "false").lower() == "true"
    if trace_requested:
        try:
            trace_call = rpc.call("debug_traceCall", [rpc_tx, block_tag, {"tracer": "callTracer", "timeout": "5s"}])
            call_trace = normalize_call_trace(trace_call.result)
            trace_status = call_trace.get("status")
            trace_confidence = 92 if trace_status == "NORMALIZED_CALL_TRACE" else 55 if call_trace.get("call_count") else 0
            evidence.append(_evidence(trace_call, source_type="execution_trace", normalized_value=call_trace, chain_id=chain.chain_id, block_number=block_number, confidence=trace_confidence, endpoint_method="debug_traceCall/callTracer"))
            if trace_status == "PARTIAL_CALL_TRACE":
                warnings.append("Internal call trace was only partially normalized; malformed or bounded nodes were excluded from promoted effects.")
                missing.append("complete canonical internal call trace")
            elif trace_status == "UNAVAILABLE_CALL_TRACE":
                warnings.append("RPC returned no valid internal call-trace nodes.")
                missing.append("decoded internal call trace")
        except ProviderError as exc:
            warnings.append(f"Internal call trace unavailable from selected RPC: {exc.code}")
            missing.append("decoded internal call trace")
    else:
        missing.append("decoded internal call trace")
    if state_diff_requested:
        try:
            diff_call = rpc.call("debug_traceCall", [rpc_tx, block_tag, {"tracer": "prestateTracer", "tracerConfig": {"diffMode": True}, "timeout": "5s"}])
            state_diff = summarize_prestate_diff(diff_call.result)
            state_diff_status = state_diff.get("status")
            state_diff_confidence = 90 if state_diff_status == "NORMALIZED_PRESTATE_DIFF" else 55 if state_diff_status == "PARTIAL_PRESTATE_DIFF" else 0
            evidence.append(_evidence(diff_call, source_type="state_diff", normalized_value=state_diff, chain_id=chain.chain_id, block_number=block_number, confidence=state_diff_confidence, endpoint_method="debug_traceCall/prestateTracer"))
            if state_diff_status == "PARTIAL_PRESTATE_DIFF":
                warnings.append("State diff was only partially normalized; malformed or bounded state was excluded from the change summary.")
                missing.append("complete canonical before/after contract state diff")
            elif state_diff_status == "UNAVAILABLE_PRESTATE_DIFF":
                warnings.append("RPC returned no usable before/after contract state diff.")
                missing.append("before/after contract state diff")
        except ProviderError as exc:
            warnings.append(f"State-diff tracer unavailable from selected RPC: {exc.code}")
            missing.append("before/after contract state diff")
    else:
        missing.append("before/after contract state diff")

    missing.extend(_event_effect_gaps(receipt_event_effects))
    score = 90 if not call_success else 15
    if call_success and receipt_event_effects is not None:
        summary = "RPC dry-run completed without an execution revert; for this mined transaction hash, standard ERC event effects were normalized from the observed transaction receipt."
    elif call_success:
        summary = "RPC dry-run completed without an execution revert; canonical event/state effects remain unavailable from the dry-run path."
    else:
        summary = "RPC dry-run indicates the transaction reverts or cannot execute."
    return EngineResult(
        engine_id=EngineId.B1,
        engine_version="1.3.0",
        block_reference=block_number,
        status=AnalysisStatus.PARTIAL,
        risk_score=score,
        data_confidence=82 if call_success else 88,
        engine_confidence=72,
        severity=Severity.CRITICAL if not call_success else Severity.LOW,
        summary=summary,
        metrics={
            "chain": chain.key,
            "chain_id": chain.chain_id,
            "from": rpc_tx.get("from"),
            "to": rpc_tx.get("to"),
            "execution_success": call_success,
            "return_data": call_result,
            "revert_reason": revert_reason,
            "gas_estimate": gas_estimate,
            "block_tag": block_tag,
            "simulation_mode": "standards-based-rpc-dry-run",
            "calldata_decode": calldata_decode,
            "verified_abi_decode": verified_abi_decode,
            "call_trace": call_trace,
            "state_diff": state_diff,
            "event_effects": receipt_event_effects,
            "event_effects_precedence": "mined_transaction_receipt" if receipt_event_effects is not None else None,
        },
        warnings=warnings + (["This fallback dry-run is execution-only; receipt event effects, when present, describe the already-mined transaction rather than newly simulated logs."] if call_success else []),
        hard_blockers=([f"Execution revert/failure: {revert_reason}"] if not call_success else []),
        mitigations=(["Correct transaction parameters and re-simulate before signing."] if not call_success else []),
        safer_alternatives=(["Configure Tenderly for predicted standard event effects on prospective transactions."] if call_success else ["Do not sign until the revert cause is corrected."]),
        evidence=evidence,
        provider_consensus="SINGLE SOURCE",
        data_freshness={"status": "LIVE", "block_number": block_number, "chain": chain.key},
        missing_data=sorted(set(missing)),
        provider_status=provider_status,
        assumptions=assumptions + [
            "RPC eth_call/eth_estimateGas simulate against the selected block state but do not guarantee the future mined outcome.",
            "Raw event amounts/token IDs are preserved without inferring token decimals, symbols, prices or ownership beyond the emitted standard event.",
        ],
    )


def _invalid(message: str) -> EngineResult:
    return EngineResult(
        engine_id=EngineId.B1,
        engine_version="1.3.0",
        status=AnalysisStatus.INSUFFICIENT_DATA,
        risk_score=0,
        data_confidence=0,
        engine_confidence=0,
        severity=Severity.UNKNOWN,
        summary=message,
        warnings=["No live simulation was executed."],
        missing_data=["valid B1 transaction input"],
        provider_consensus="UNAVAILABLE",
    )
