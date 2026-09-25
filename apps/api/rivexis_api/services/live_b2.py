from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from rivexis_api.chains import normalize_chain
from rivexis_api.models.engine import EngineResult
from rivexis_api.models.enums import AnalysisStatus, EngineId, FreshnessStatus, Severity
from rivexis_api.models.evidence import EvidenceRecord, SourceConflict
from rivexis_api.provider_clients import BlockaidClient, EtherscanClient, ProviderCall, ProviderError, hex_to_int
from rivexis_api.providers import resolve_provider, select_rpc_client
from rivexis_api.services.evm_decode import decode_common_calldata, keccak256
from rivexis_api.services.security_intel import blockaid_risk, normalize_blockaid

MAX_UINT256 = 2**256 - 1
MAX_RUNTIME_BYTECODE_BYTES = 131072
EIP1167_PREFIX = bytes.fromhex("363d3d373d3d3d363d73")
EIP1167_SUFFIX = bytes.fromhex("5af43d82803e903d91602b57fd5bf3")
STRUCTURAL_OPCODES = {
    0xF0: "CREATE",
    0xF2: "CALLCODE",
    0xF4: "DELEGATECALL",
    0xF5: "CREATE2",
    0xFF: "SELFDESTRUCT",
}


def _evidence(call: ProviderCall, source_type: str, normalized: Any, chain_id: int, block_number: int | None, confidence: float, endpoint: str, freshness: FreshnessStatus = FreshnessStatus.LIVE) -> EvidenceRecord:
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
        calculation_version="b2-live-1.3.0",
        engine_version="1.1.0",
        confidence=confidence,
        freshness=freshness,
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
    if not isinstance(value, str) or not value.startswith("0x"):
        return None
    digits = value[2:]
    if not digits or (len(digits) > 1 and digits[0] == "0"):
        return None
    try:
        parsed = hex_to_int(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return parsed if parsed is not None and 0 <= parsed <= MAX_UINT256 else None


def _bytecode(value: object) -> tuple[str, bytes] | None:
    if not isinstance(value, str) or not value.startswith("0x"):
        return None
    raw = value[2:]
    if len(raw) % 2 or len(raw) // 2 > MAX_RUNTIME_BYTECODE_BYTES:
        return None
    try:
        decoded = bytes.fromhex(raw)
    except ValueError:
        return None
    return "0x" + raw.lower(), decoded


def _runtime_bytecode_observations(code: bytes) -> dict[str, Any]:
    opcode_counts = {name: 0 for name in STRUCTURAL_OPCODES.values()}
    instruction_count = 0
    offset = 0
    while offset < len(code):
        opcode = code[offset]
        instruction_count += 1
        name = STRUCTURAL_OPCODES.get(opcode)
        if name:
            opcode_counts[name] += 1
        offset += 1
        if 0x60 <= opcode <= 0x7F:
            offset += opcode - 0x5F

    minimal_proxy = (
        len(code) == len(EIP1167_PREFIX) + 20 + len(EIP1167_SUFFIX)
        and code.startswith(EIP1167_PREFIX)
        and code.endswith(EIP1167_SUFFIX)
    )
    implementation = (
        "0x" + code[len(EIP1167_PREFIX) : len(EIP1167_PREFIX) + 20].hex()
        if minimal_proxy
        else None
    )
    return {
        "status": "OBSERVED_RUNTIME_BYTECODE" if code else "NO_RUNTIME_CODE",
        "bytecode_bytes": len(code),
        "bytecode_keccak256": "0x" + keccak256(code).hex(),
        "instruction_count": instruction_count,
        "opcode_presence": {
            name: count for name, count in opcode_counts.items() if count
        },
        "exact_eip1167_minimal_proxy": minimal_proxy,
        "embedded_implementation": implementation,
        "is_security_verdict": False,
        "note": "Opcode presence and exact proxy shape are structural observations, not reachability, exploitability, or safety conclusions.",
    }


def _normalize_etherscan_source(body: object) -> dict[str, Any] | None:
    if not isinstance(body, dict):
        return None
    result = body.get("result")
    if not isinstance(result, list) or len(result) != 1 or not isinstance(result[0], dict):
        return None
    item = result[0]
    source_code = item.get("SourceCode")
    abi = item.get("ABI")
    contract_name = item.get("ContractName")
    compiler_version = item.get("CompilerVersion")
    proxy_value = item.get("Proxy", "0")
    implementation_value = item.get("Implementation", "")
    if (
        not isinstance(source_code, str)
        or not isinstance(abi, str)
        or len(source_code) > 10_000_000
        or len(abi) > 5_000_000
        or not isinstance(contract_name, str)
        or len(contract_name) > 256
        or not isinstance(compiler_version, str)
        or len(compiler_version) > 256
        or proxy_value not in {"0", "1"}
        or not isinstance(implementation_value, str)
    ):
        return None
    implementation = (
        _evm_address(implementation_value) if implementation_value else None
    )
    if implementation_value and implementation is None:
        return None
    if implementation == "0x" + "0" * 40:
        implementation = None
    proxy = proxy_value == "1"
    if not proxy and implementation is not None:
        return None
    return {
        "verified_source": bool(source_code) and "not verified" not in abi.lower(),
        "contract_name": contract_name or None,
        "compiler_version": compiler_version or None,
        "proxy": proxy,
        "implementation": implementation,
    }


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
    conflicts: list[SourceConflict] = []
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
    runtime_bytecode: dict[str, Any] | None = None
    direct_proxy = False
    direct_implementation: str | None = None
    try:
        code_call = rpc.call("eth_getCode", [target, block_tag])
        normalized_code = _bytecode(code_call.result)
        if normalized_code is None:
            raise ProviderError(
                "RPC returned malformed contract bytecode",
                provider_id=rpc_provider_id,
                code="MALFORMED_RESPONSE",
            )
        _code, code_bytes = normalized_code
        code_present = bool(code_bytes)
        runtime_bytecode = _runtime_bytecode_observations(code_bytes)
        direct_proxy = bool(runtime_bytecode.get("exact_eip1167_minimal_proxy"))
        direct_implementation = runtime_bytecode.get("embedded_implementation")
        if direct_implementation == "0x" + "0" * 40:
            direct_implementation = None
        evidence.append(_evidence(
            code_call,
            "direct_state",
            {
                "address": target,
                "has_contract_code": code_present,
                "bytecode_bytes": len(code_bytes),
                "bytecode_keccak256": runtime_bytecode["bytecode_keccak256"],
                "structural_observations": runtime_bytecode,
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

    if runtime_bytecode and runtime_bytecode.get("opcode_presence"):
        signals.append(
            {
                "type": "runtime_bytecode_opcode_presence",
                "observed_opcodes": runtime_bytecode["opcode_presence"],
                "source": "block-pinned eth_getCode structural parse",
                "is_security_verdict": False,
            }
        )
    if direct_proxy:
        signals.append(
            {
                "type": "exact_eip1167_minimal_proxy",
                "implementation": direct_implementation,
                "source": "block-pinned exact runtime-bytecode pattern",
                "is_security_verdict": False,
            }
        )

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
    explorer_proxy = False
    explorer_implementation: str | None = None
    explorer_evidence_consumed = False
    if code_present:
        etherscan = EtherscanClient()
        if etherscan.configured:
            try:
                source_call = etherscan.get_source_code(chain, target)
                normalized_source = _normalize_etherscan_source(source_call.result)
                if normalized_source is None:
                    raise ProviderError(
                        "Etherscan returned malformed source metadata",
                        provider_id="etherscan",
                        code="MALFORMED_RESPONSE",
                    )
                verified = normalized_source["verified_source"]
                explorer_proxy = normalized_source["proxy"]
                explorer_implementation = normalized_source["implementation"]
                normalized = {
                    "address": target,
                    **normalized_source,
                }
                evidence.append(_evidence(source_call, "verified_indexed_state", normalized, chain.chain_id, None, 96, "Etherscan V2 getsourcecode", FreshnessStatus.UNKNOWN))
                explorer_evidence_consumed = True
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

    proxy = bool(direct_proxy or explorer_proxy)
    implementation_conflict = bool(
        direct_implementation
        and explorer_implementation
        and direct_implementation != explorer_implementation
    )
    implementation = (
        None
        if implementation_conflict
        else direct_implementation or explorer_implementation
    )
    if implementation_conflict:
        score += 15
        warnings.append("Direct minimal-proxy bytecode and explorer metadata disagree on the implementation address.")
        missing.append("resolved proxy implementation identity")
        signals.append(
            {
                "type": "proxy_implementation_conflict",
                "direct_implementation": direct_implementation,
                "explorer_implementation": explorer_implementation,
                "source": "direct bytecode vs Etherscan",
                "is_security_verdict": False,
            }
        )
        conflicts.append(
            SourceConflict(
                metric="proxy_implementation",
                source_a="direct_eip1167_runtime",
                value_a=direct_implementation,
                source_b="etherscan",
                value_b=explorer_implementation,
                severity="high",
                resolution_method="unresolved",
            )
        )
    if proxy:
        score += 10
        warnings.append("Target has proxy structure evidence; implementation code and upgrade authority require separate review.")
        signals.append(
            {
                "type": "proxy_structure",
                "implementation": implementation,
                "sources": [
                    source
                    for source, present in (
                        ("exact_eip1167_runtime", direct_proxy),
                        ("etherscan", explorer_proxy),
                    )
                    if present
                ],
                "is_security_verdict": False,
            }
        )
        if implementation is None and not implementation_conflict:
            missing.append("proxy implementation address")

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
        metrics={"chain": chain.key, "chain_id": chain.chain_id, "target": target, "contract_code_present": code_present, "runtime_bytecode": runtime_bytecode, "verified_source": verified, "proxy": proxy, "proxy_sources": [source for source, present in (("exact_eip1167_runtime", direct_proxy), ("etherscan", explorer_proxy)) if present], "implementation": implementation, "implementation_conflict": implementation_conflict, "approval": approval},
        signals=signals,
        warnings=warnings,
        hard_blockers=hard_blockers,
        mitigations=mitigations,
        safer_alternatives=mitigations[:],
        evidence=evidence,
        provider_conflicts=conflicts,
        provider_consensus="MULTI_SOURCE" if len({e.provider for e in evidence}) > 1 else "SINGLE_SOURCE",
        data_freshness={"status": "UNKNOWN" if explorer_evidence_consumed else "LIVE", "chain": chain.key, "block_number": block_number, "direct_state": "LIVE", "external_verification": "UNKNOWN" if explorer_evidence_consumed else "NOT_CONSUMED"},
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
