from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from rivexis_api.chains import normalize_chain
from rivexis_api.models.engine import EngineResult
from rivexis_api.models.enums import AnalysisStatus, EngineId, FreshnessStatus, Severity
from rivexis_api.models.evidence import EvidenceRecord
from rivexis_api.provider_clients import BlockaidClient, EtherscanClient, ProviderCall, ProviderError, hex_to_int
from rivexis_api.providers import resolve_provider, select_rpc_client
from rivexis_api.services.evm_decode import decode_common_calldata
from rivexis_api.services.security_intel import blockaid_risk, normalize_blockaid

MAX_UINT256 = 2**256 - 1


def _evidence(call: ProviderCall, source_type: str, normalized: Any, chain_id: int, block_number: int | None, confidence: float, endpoint: str) -> EvidenceRecord:
    return EvidenceRecord(
        evidence_id=str(uuid4()),
        provider=call.provider_id,
        source_type=source_type,
        provider_endpoint=endpoint,
        provider_request_id=call.request_id,
        retrieved_at=datetime.now(timezone.utc),
        observed_at=datetime.now(timezone.utc),
        block_number=block_number,
        chain_id=chain_id,
        raw_reference=f"provider:{call.provider_id};request:{call.request_id}",
        normalized_value=normalized,
        calculation_version="b2-live-1.2.0",
        engine_version="1.1.0",
        confidence=confidence,
        freshness=FreshnessStatus.LIVE,
        license_classification="external-provider-evidence",
    )


def _evm_address(value: object) -> str | None:
    raw = str(value or "").strip().lower()
    if len(raw) != 42 or not raw.startswith("0x"):
        return None
    try:
        int(raw[2:], 16)
    except ValueError:
        return None
    return raw


def _transaction_hash(value: object) -> str | None:
    raw = str(value or "").strip().lower()
    if len(raw) != 66 or not raw.startswith("0x"):
        return None
    try:
        int(raw[2:], 16)
    except ValueError:
        return None
    return raw


def _rpc_quantity(value: object) -> int | None:
    try:
        parsed = hex_to_int(value)
    except (TypeError, ValueError, OverflowError):
        return None
    if isinstance(parsed, bool) or parsed is None or parsed < 0:
        return None
    return parsed


def _bytecode(value: object) -> tuple[str, bytes] | None:
    if not isinstance(value, str) or not value.startswith("0x"):
        return None
    raw = value[2:]
    if len(raw) % 2:
        return None
    try:
        decoded = bytes.fromhex(raw)
    except ValueError:
        return None
    return "0x" + raw.lower(), decoded


def _decode_approval(data: str | None) -> dict[str, Any] | None:
    decoded = decode_common_calldata(data)
    selector = decoded.get("selector")
    signature = decoded.get("signature")
    params = decoded.get("parameters") if isinstance(decoded.get("parameters"), dict) else {}

    if signature == "approve(address,uint256)":
        spender = params.get("spender_or_approved")
        amount = params.get("amount_or_token_id")
        if _evm_address(spender) is None or not isinstance(amount, int) or isinstance(amount, bool):
            return {"type": "MALFORMED_APPROVAL", "selector": selector or "0x095ea7b3"}
        return {
            "type": "ERC20_APPROVE",
            "selector": selector,
            "spender": spender,
            "amount_raw": str(amount),
            "unlimited": amount >= MAX_UINT256 - 2**128,
        }

    if signature == "setApprovalForAll(address,bool)":
        operator = params.get("operator")
        enabled = params.get("approved")
        if _evm_address(operator) is None or not isinstance(enabled, bool):
            return {"type": "MALFORMED_APPROVAL", "selector": selector or "0xa22cb465"}
        return {
            "type": "SET_APPROVAL_FOR_ALL",
            "selector": selector,
            "operator": operator,
            "enabled": enabled,
        }

    if selector in {"0x095ea7b3", "0xa22cb465"}:
        return {"type": "MALFORMED_APPROVAL", "selector": selector}
    return None


def _severity(score: float) -> Severity:
    if score >= 80:
        return Severity.CRITICAL
    if score >= 60:
        return Severity.HIGH
    if score >= 35:
        return Severity.MODERATE
    return Severity.LOW


def run_live_b2(input_data: dict[str, Any]) -> EngineResult:
    try:
        chain = normalize_chain(input_data.get("chain") or input_data.get("network"))
    except ValueError as exc:
        return _insufficient(str(exc), AnalysisStatus.UNSUPPORTED)

    tx = input_data.get("transaction") if isinstance(input_data.get("transaction"), dict) else dict(input_data)
    for key in ("chain", "network", "transaction", "transaction_hash", "tx_hash"):
        tx.pop(key, None)

    raw_tx_hash = input_data.get("transaction_hash") or input_data.get("tx_hash")
    tx_hash = None
    if raw_tx_hash not in (None, ""):
        tx_hash = _transaction_hash(raw_tx_hash)
        if tx_hash is None:
            return _insufficient(
                "Transaction hash must be a 32-byte 0x-prefixed hexadecimal value"
            )

    explicit_target = input_data.get("contract") or input_data.get("address") or tx.get("to")
    target = None
    if explicit_target not in (None, ""):
        target = _evm_address(explicit_target)
        if target is None:
            return _insufficient("Target address must be a valid 20-byte EVM address")

    sender = tx.get("from")
    if sender not in (None, "") and _evm_address(sender) is None:
        return _insufficient("Transaction from address must be a valid 20-byte EVM address")
    if sender not in (None, ""):
        tx["from"] = _evm_address(sender)
    if tx.get("to") not in (None, ""):
        tx["to"] = _evm_address(tx.get("to"))

    evidence: list[EvidenceRecord] = []
    statuses: list[dict[str, Any]] = []
    warnings: list[str] = []
    signals: list[dict[str, Any]] = []
    missing: list[str] = []
    mitigations: list[str] = []
    block_number: int | None = None

    try:
        rpc_provider_id, rpc, chain_probe, fallback_errors = select_rpc_client(chain.key)
        statuses.extend({"provider_id": e["provider_id"], "status": "FAILED_OR_UNAVAILABLE", "detail": e["error"]} for e in fallback_errors)
        statuses.append({"provider_id": rpc_provider_id, "status": "HEALTHY", "latency_ms": round(chain_probe.latency_ms, 2)})
        block_call = rpc.call("eth_blockNumber")
        block_number = _rpc_quantity(block_call.result)
        if block_number is None:
            raise ProviderError(
                "RPC returned a malformed block number",
                provider_id=rpc_provider_id,
                code="MALFORMED_RESPONSE",
            )
        evidence.append(_evidence(block_call, "direct_state", {"block_number": block_number}, chain.chain_id, block_number, 99, "eth_blockNumber"))
        if tx_hash:
            tx_call = rpc.call("eth_getTransactionByHash", [tx_hash])
            if tx_call.result:
                if not isinstance(tx_call.result, dict):
                    raise ProviderError(
                        "RPC returned a malformed transaction body",
                        provider_id=rpc_provider_id,
                        code="MALFORMED_RESPONSE",
                    )
                tx = dict(tx_call.result)
                resolved_target = tx.get("to") or target
                if resolved_target not in (None, ""):
                    target = _evm_address(resolved_target)
                    if target is None:
                        return _insufficient(
                            "Resolved transaction destination is not a valid 20-byte EVM address"
                        )
                resolved_sender = tx.get("from")
                if resolved_sender not in (None, "") and _evm_address(resolved_sender) is None:
                    return _insufficient(
                        "Resolved transaction sender is not a valid 20-byte EVM address"
                    )
                if resolved_sender not in (None, ""):
                    tx["from"] = _evm_address(resolved_sender)
                if target is not None:
                    tx["to"] = target
                historical_block = _rpc_quantity(tx.get("blockNumber"))
                evidence.append(_evidence(tx_call, "direct_state", {k: tx.get(k) for k in ("hash", "from", "to", "input", "value", "blockNumber")}, chain.chain_id, historical_block, 99, "eth_getTransactionByHash"))
            else:
                warnings.append("Transaction hash was not found by the selected RPC provider.")
                missing.append("transaction body")
    except ProviderError as exc:
        return EngineResult(
            engine_id=EngineId.B2,
            engine_version="1.1.0",
            status=AnalysisStatus.PROVIDER_UNAVAILABLE,
            risk_score=0,
            data_confidence=0,
            engine_confidence=0,
            severity=Severity.UNKNOWN,
            summary=f"B2 cannot acquire direct chain state for {chain.name}.",
            warnings=["No security classification was fabricated."],
            missing_data=["healthy EVM RPC provider"],
            provider_consensus="UNAVAILABLE",
            provider_status=[{"provider_id": exc.provider_id, "status": "UNAVAILABLE", "detail": f"{exc.code}: {exc}"}],
        )

    if not target:
        return _insufficient("Provide a contract/address, transaction destination, or transaction hash for live B2 analysis")

    block_tag = hex(block_number)
    code_present = False
    try:
        code_call = rpc.call("eth_getCode", [target, block_tag])
        normalized_code = _bytecode(code_call.result)
        if normalized_code is None:
            raise ProviderError(
                "RPC returned malformed contract bytecode",
                provider_id=rpc_provider_id,
                code="MALFORMED_RESPONSE",
            )
        code, code_bytes = normalized_code
        code_present = bool(code_bytes)
        evidence.append(_evidence(
            code_call,
            "direct_state",
            {
                "address": target,
                "has_contract_code": code_present,
                "bytecode_bytes": len(code_bytes),
                "block_tag": block_tag,
            },
            chain.chain_id,
            block_number,
            99,
            "eth_getCode",
        ))
    except ProviderError as exc:
        warnings.append(f"Contract-code lookup failed: {exc.code}")
        missing.append("contract bytecode state")

    approval = _decode_approval(tx.get("data") or tx.get("input"))
    score = 8.0
    if approval:
        signals.append({"type": "approval", **approval, "source": "Rivexis deterministic calldata rule"})
        if approval.get("type") == "ERC20_APPROVE" and approval.get("unlimited"):
            score += 52
            warnings.append("Transaction grants an effectively unlimited ERC-20 allowance.")
            mitigations.append("Reduce the allowance to the minimum amount required for this action.")
        elif approval.get("type") == "SET_APPROVAL_FOR_ALL" and approval.get("enabled"):
            score += 48
            warnings.append("Transaction enables blanket operator approval for all applicable NFTs/tokens.")
            mitigations.append("Use asset-specific approval when the protocol supports it, or revoke operator approval after use.")
        elif approval.get("type") == "MALFORMED_APPROVAL":
            score += 30
            warnings.append("Approval-like calldata could not be decoded safely.")

    verified: bool | None = None
    proxy = False
    implementation: str | None = None
    if code_present:
        etherscan = EtherscanClient()
        if etherscan.configured:
            try:
                source_call = etherscan.get_source_code(chain, target)
                body = source_call.result
                result = body.get("result") if isinstance(body, dict) else None
                first = result[0] if isinstance(result, list) and result and isinstance(result[0], dict) else {}
                source_code = str(first.get("SourceCode") or "")
                abi = str(first.get("ABI") or "")
                verified = bool(source_code) and "not verified" not in abi.lower()
                proxy = str(first.get("Proxy") or "0") == "1"
                implementation = str(first.get("Implementation") or "") or None
                normalized = {
                    "address": target,
                    "verified_source": verified,
                    "contract_name": first.get("ContractName"),
                    "compiler_version": first.get("CompilerVersion"),
                    "proxy": proxy,
                    "implementation": implementation,
                }
                evidence.append(_evidence(source_call, "verified_indexed_state", normalized, chain.chain_id, block_number, 96, "Etherscan V2 getsourcecode"))
                statuses.append({"provider_id": "etherscan", "status": "HEALTHY", "latency_ms": round(source_call.latency_ms, 2)})
            except ProviderError as exc:
                statuses.append({"provider_id": "etherscan", "status": "FAILED", "detail": f"{exc.code}: {exc}"})
                missing.append("contract verification state")
        else:
            statuses.append({"provider_id": "etherscan", "status": "CREDENTIALS_REQUIRED"})
            missing.append("contract verification state")
        if verified is False:
            score += 24
            warnings.append("Contract source code is not verified by the configured explorer evidence.")
        if proxy:
            score += 10
            warnings.append("Target is reported as a proxy contract; implementation and upgrade authority require separate review.")
            if implementation:
                signals.append({"type": "proxy", "implementation": implementation, "source": "Etherscan"})

    security_resolution = resolve_provider("security", chain=chain.key)
    external_security_consumed = False
    hard_blockers: list[str] = []
    if security_resolution.provider_id == "blockaid":
        blockaid = BlockaidClient()
        try:
            domain = input_data.get("dapp_domain") or input_data.get("domain")
            sender = tx.get("from")
            if sender:
                security_call = blockaid.scan_transaction(
                    chain=chain.key,
                    transaction=tx,
                    account_address=str(input_data.get("account_address") or sender),
                    domain=str(domain) if domain else None,
                    block=block_number,
                )
                endpoint_name = "Blockaid /v0/evm/transaction/scan"
            else:
                security_call = blockaid.scan_address(
                    chain=chain.key,
                    address=target,
                    domain=str(domain) if domain else None,
                )
                endpoint_name = "Blockaid /v0/evm/address/scan"
            normalized_security = normalize_blockaid(security_call.result)
            evidence.append(_evidence(security_call, "external_security_intelligence", normalized_security, chain.chain_id, block_number, 90, endpoint_name))
            statuses.append({"provider_id": "blockaid", "status": "HEALTHY", "latency_ms": round(security_call.latency_ms, 2)})
            signals.append({"type": "external_security", "provider": "blockaid", **normalized_security})
            score_add, malicious, external_messages = blockaid_risk(normalized_security)
            score += score_add
            warnings.extend(external_messages)
            if malicious:
                hard_blockers.append("External Blockaid evidence explicitly classifies the address/transaction as malicious.")
                mitigations.append("Do not execute this interaction unless the external classification is independently investigated and resolved.")
            external_security_consumed = True
        except ProviderError as exc:
            statuses.append({"provider_id": "blockaid", "status": exc.code, "detail": str(exc)})
            warnings.append(f"Blockaid security evidence was configured but unavailable: {exc.code}.")
            missing.append("Blockaid security verdict")
    elif security_resolution.provider_id == "hypernative":
        statuses.append({"provider_id": "hypernative", "status": "CUSTOMER_SCHEMA_REQUIRED"})
        missing.append("Hypernative customer API schema/endpoint configuration")
        warnings.append("Hypernative credentials are present, but Rivexis will not invent a customer-only screening request schema. Configure the certified adapter contract before consuming Hypernative evidence.")
    else:
        missing.append("external malicious-address / transaction threat intelligence")
        warnings.append("Blockaid/Hypernative threat intelligence is not connected; B2 cannot classify the target as known malicious or benign.")

    score = min(100.0, score)
    data_conf = 88 if evidence else 0
    if missing:
        data_conf = max(45, data_conf - min(25, len(set(missing)) * 5))
    return EngineResult(
        engine_id=EngineId.B2,
        engine_version="1.1.0",
        block_reference=block_number,
        status=AnalysisStatus.PARTIAL,
        risk_score=round(score, 2),
        data_confidence=data_conf,
        engine_confidence=82 if external_security_consumed else 75,
        severity=_severity(score),
        summary=("B2 combined deterministic on-chain checks with attributed external security evidence." if external_security_consumed else "B2 completed deterministic on-chain security checks; external threat-intelligence coverage is partial."),
        metrics={"chain": chain.key, "chain_id": chain.chain_id, "target": target, "contract_code_present": code_present, "verified_source": verified, "proxy": proxy, "implementation": implementation, "approval": approval},
        signals=signals,
        warnings=warnings,
        hard_blockers=hard_blockers,
        mitigations=mitigations,
        safer_alternatives=mitigations[:],
        evidence=evidence,
        provider_consensus="MULTI_SOURCE" if len({e.provider for e in evidence}) > 1 else "SINGLE_SOURCE",
        data_freshness={"status": "LIVE", "chain": chain.key, "block_number": block_number},
        missing_data=sorted(set(missing)),
        provider_status=statuses,
        assumptions=[
            "Absence of an external malicious verdict is not evidence that an address or transaction is safe.",
            f"Direct contract bytecode state is pinned to captured RPC block {block_tag}.",
        ],
    )


def _insufficient(message: str, status: AnalysisStatus = AnalysisStatus.INSUFFICIENT_DATA) -> EngineResult:
    return EngineResult(
        engine_id=EngineId.B2,
        engine_version="1.1.0",
        status=status,
        risk_score=0,
        data_confidence=0,
        engine_confidence=0,
        severity=Severity.UNKNOWN,
        summary=message,
        warnings=["No live security verdict was fabricated."],
        missing_data=["valid B2 target input"],
        provider_consensus="UNAVAILABLE",
    )
