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


def _evidence(call: ProviderCall, *, source_type: str, normalized_value: Any, chain_id: int, block_number: int | None, confidence: float, endpoint_method: str) -> EvidenceRecord:
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
        calculation_version="b1-live-1.2.0",
        engine_version="1.2.0",
        confidence=confidence,
        freshness=FreshnessStatus.LIVE,
        license_classification="external-provider-evidence",
    )


def _provider_status(provider_id: str, status: str, detail: str | None = None, latency_ms: float | None = None) -> dict[str, Any]:
    out: dict[str, Any] = {"provider_id": provider_id, "status": status}
    if detail:
        out["detail"] = detail
    if latency_ms is not None:
        out["latency_ms"] = round(latency_ms, 2)
    return out


def _tenderly_success(body: dict[str, Any]) -> tuple[bool, str | None, int | None, dict[str, Any]]:
    transaction = body.get("transaction") if isinstance(body.get("transaction"), dict) else {}
    simulation = body.get("simulation") if isinstance(body.get("simulation"), dict) else {}
    error_info = transaction.get("error_info") if isinstance(transaction.get("error_info"), dict) else None
    success = not bool(error_info) and transaction.get("status", True) not in {False, 0, "0", "failed", "reverted"}
    revert_reason = None
    if error_info:
        revert_reason = str(error_info.get("error_message") or error_info.get("error_reason") or "Simulation reverted")
    gas_used = hex_to_int(transaction.get("gas_used") or transaction.get("gasUsed") or simulation.get("gas_used"))
    summary = {
        "simulation_id": simulation.get("id"),
        "network_id": simulation.get("network_id") or body.get("network_id"),
        "block_number": simulation.get("block_number") or transaction.get("block_number"),
        "gas_used": gas_used,
        "status": "success" if success else "reverted",
        "revert_reason": revert_reason,
        "logs_count": len(transaction.get("logs") or []) if isinstance(transaction.get("logs"), list) else None,
    }
    return success, revert_reason, gas_used, summary


def run_live_b1(input_data: dict[str, Any]) -> EngineResult:
    try:
        chain = normalize_chain(input_data.get("chain") or input_data.get("network"))
    except ValueError as exc:
        return EngineResult(
            engine_id=EngineId.B1,
            engine_version="1.2.0",
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

    try:
        rpc_provider_id, rpc, chain_probe, fallback_errors = select_rpc_client(chain.key)
        provider_status.extend(_provider_status(x["provider_id"], "FAILED_OR_UNAVAILABLE", x["error"]) for x in fallback_errors)
        provider_status.append(_provider_status(rpc_provider_id, "HEALTHY", f"chain_id={chain.chain_id}", chain_probe.latency_ms))
        evidence.append(_evidence(chain_probe, source_type="direct_state", normalized_value={"chain_id": chain.chain_id}, chain_id=chain.chain_id, block_number=None, confidence=99, endpoint_method="eth_chainId"))
        block_call = rpc.call("eth_blockNumber")
        block_number = hex_to_int(block_call.result)
        evidence.append(_evidence(block_call, source_type="direct_state", normalized_value={"block_number": block_number}, chain_id=chain.chain_id, block_number=block_number, confidence=99, endpoint_method="eth_blockNumber"))
    except ProviderError as exc:
        return EngineResult(
            engine_id=EngineId.B1,
            engine_version="1.2.0",
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
                    engine_version="1.2.0",
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
            transaction = dict(tx_call.result)
            historical_block = hex_to_int(transaction.get("blockNumber"))
            evidence.append(_evidence(tx_call, source_type="direct_state", normalized_value={k: transaction.get(k) for k in ("hash", "from", "to", "value", "input", "blockNumber")}, chain_id=chain.chain_id, block_number=historical_block, confidence=99, endpoint_method="eth_getTransactionByHash"))
            if historical_block is not None:
                block_number = historical_block
                assumptions.append("Historical replay targets the state immediately before the transaction block when supported by the provider.")
        except ProviderError as exc:
            warnings.append(f"Transaction lookup failed: {exc.code}")
            missing.append("transaction lookup")

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
            evidence.append(_evidence(abi_call, source_type="verified_contract_abi", normalized_value={"decode": verified_abi_decode}, chain_id=chain.chain_id, block_number=block_number, confidence=96 if verified_abi_decode.get("status")=="DECODED_VERIFIED_ABI" else 82, endpoint_method="Etherscan getabi"))
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
            provider_status.append(_provider_status("tenderly", "HEALTHY", "Simulation response received and core execution status normalized", sim_call.latency_ms))
            evidence.append(_evidence(sim_call, source_type="simulation", normalized_value=normalized, chain_id=chain.chain_id, block_number=normalized.get("block_number") or historical_target or block_number, confidence=94, endpoint_method="Tenderly Simulation API"))
            score = 90 if not success else 10
            blockers = [f"Simulation reverted: {revert_reason or 'revert detected'}"] if not success else []
            tenderly_missing = sorted(set(missing + [
                "decoded internal call tree normalization",
                "decoded token/NFT asset-change normalization",
                "approval/allowance-change normalization",
                "before/after contract-state diff normalization",
            ]))
            return EngineResult(
                engine_id=EngineId.B1,
                engine_version="1.2.0",
                block_reference=normalized.get("block_number") or historical_target or block_number,
                status=AnalysisStatus.PARTIAL,
                risk_score=score,
                data_confidence=94,
                engine_confidence=91,
                severity=Severity.CRITICAL if not success else Severity.LOW,
                summary=("Tenderly simulation predicts a revert; richer decoded effects are not yet normalized." if not success else "Tenderly simulation completed without an execution revert; richer decoded state/asset effects are not yet normalized into the Rivexis canonical model."),
                metrics={"chain": chain.key, "chain_id": chain.chain_id, "execution_success": success, "revert_reason": revert_reason, "gas_used": gas_used, "simulation": normalized, "calldata_decode": calldata_decode},
                warnings=warnings,
                hard_blockers=blockers,
                mitigations=(["Do not sign the transaction until the revert cause is corrected."] if not success else []),
                safer_alternatives=(["Correct transaction parameters and re-simulate against fresh state."] if not success else []),
                evidence=evidence,
                provider_consensus="MULTI_SOURCE" if rpc_provider_id else "SINGLE SOURCE",
                data_freshness={"status": "LIVE", "block_number": normalized.get("block_number") or block_number, "chain": chain.key},
                missing_data=tenderly_missing,
                provider_status=provider_status,
                assumptions=assumptions,
            )
        except ProviderError as exc:
            provider_status.append(_provider_status("tenderly", "FAILED", f"{exc.code}: {exc}"))
            warnings.append("Tenderly simulation failed; Rivexis degraded to standards-based RPC dry-run.")

    # Standards-based fallback: eth_call executes the message without broadcasting and
    # eth_estimateGas performs an execution dry-run. This proves basic execution/revert status,
    # but it does not provide decoded internal traces, asset changes, approvals, or state diffs.
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
        gas_estimate = hex_to_int(gas_call.result)
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
            trace_call = rpc.call("debug_traceCall", [rpc_tx, block_tag, {"tracer":"callTracer","timeout":"5s"}])
            call_trace = normalize_call_trace(trace_call.result)
            evidence.append(_evidence(trace_call, source_type="execution_trace", normalized_value=call_trace, chain_id=chain.chain_id, block_number=block_number, confidence=92, endpoint_method="debug_traceCall/callTracer"))
        except ProviderError as exc:
            warnings.append(f"Internal call trace unavailable from selected RPC: {exc.code}")
            missing.append("decoded internal call trace")
    else:
        missing.append("decoded internal call trace")
    if state_diff_requested:
        try:
            diff_call = rpc.call("debug_traceCall", [rpc_tx, block_tag, {"tracer":"prestateTracer","tracerConfig":{"diffMode":True},"timeout":"5s"}])
            state_diff = summarize_prestate_diff(diff_call.result)
            evidence.append(_evidence(diff_call, source_type="state_diff", normalized_value=state_diff, chain_id=chain.chain_id, block_number=block_number, confidence=90, endpoint_method="debug_traceCall/prestateTracer"))
        except ProviderError as exc:
            warnings.append(f"State-diff tracer unavailable from selected RPC: {exc.code}")
            missing.append("before/after contract state diff")
    else:
        missing.append("before/after contract state diff")

    if call_trace is None:
        missing.extend(["decoded token/NFT asset changes", "approval/allowance changes"])
    elif not call_trace.get("approval_candidates"):
        missing.append("canonical token/NFT transfer event normalization")
    score = 90 if not call_success else 15
    return EngineResult(
        engine_id=EngineId.B1,
        engine_version="1.2.0",
        block_reference=block_number,
        status=AnalysisStatus.PARTIAL,
        risk_score=score,
        data_confidence=82 if call_success else 88,
        engine_confidence=72,
        severity=Severity.CRITICAL if not call_success else Severity.LOW,
        summary=("RPC dry-run indicates the transaction reverts or cannot execute." if not call_success else "RPC dry-run completed without an execution revert; decoded state/asset effects remain unavailable."),
        metrics={"chain": chain.key, "chain_id": chain.chain_id, "execution_success": call_success, "return_data": call_result, "revert_reason": revert_reason, "gas_estimate": gas_estimate, "block_tag": block_tag, "simulation_mode": "standards-based-rpc-dry-run", "calldata_decode": calldata_decode, "verified_abi_decode": verified_abi_decode, "call_trace": call_trace, "state_diff": state_diff},
        warnings=warnings + (["This fallback is execution-only and is not equivalent to a decoded full-state simulation."] if call_success else []),
        hard_blockers=([f"Execution revert/failure: {revert_reason}"] if not call_success else []),
        mitigations=(["Correct transaction parameters and re-simulate before signing."] if not call_success else []),
        safer_alternatives=(["Configure Tenderly for decoded execution traces and richer state-change evidence."] if call_success else ["Do not sign until the revert cause is corrected."]),
        evidence=evidence,
        provider_consensus="SINGLE SOURCE",
        data_freshness={"status": "LIVE", "block_number": block_number, "chain": chain.key},
        missing_data=sorted(set(missing)),
        provider_status=provider_status,
        assumptions=assumptions + ["RPC eth_call/eth_estimateGas simulate against the selected block state but do not guarantee the future mined outcome."],
    )


def _invalid(message: str) -> EngineResult:
    return EngineResult(
        engine_id=EngineId.B1,
        engine_version="1.2.0",
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
