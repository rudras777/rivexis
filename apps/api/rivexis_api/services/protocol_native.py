from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from rivexis_api.chains import ChainConfig, normalize_chain
from rivexis_api.models.enums import FreshnessStatus
from rivexis_api.models.evidence import EvidenceRecord
from rivexis_api.provider_clients import EtherscanClient, ProviderCall, ProviderError
from rivexis_api.providers import select_rpc_client
from rivexis_api.services.protocol_adapters import collect_protocol_adapter, supports_protocol_adapter

DECIMALS_SELECTOR = "0x313ce567"
LATEST_ROUND_DATA_SELECTOR = "0xfeaf968c"
EIP1967_IMPLEMENTATION_SLOT = "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"
EIP1967_ADMIN_SLOT = "0xb53127684a568b3173ae13b9f8a6016e243e63b6e8ee1178d6a717850b5d6103"
EIP1967_BEACON_SLOT = "0xa3f0ad74e5423aebfd80d3ef4346578335a9a72aeaee59ff6cb3582b35133d50"
UINT256_MAX = 2**256 - 1
MAX_RUNTIME_CODE_BYTES = 128 * 1024


def _rpc_quantity(value: Any) -> int | None:
    if not isinstance(value, str) or not value.startswith("0x"):
        return None
    digits = value[2:]
    if not digits or (len(digits) > 1 and digits.startswith("0")):
        return None
    try:
        parsed = int(digits, 16)
    except ValueError:
        return None
    return parsed if parsed <= UINT256_MAX else None


def _abi_words(value: Any, *, count: int) -> list[str] | None:
    if not isinstance(value, str) or not value.startswith("0x"):
        return None
    clean = value[2:]
    if len(clean) != 64 * count:
        return None
    try:
        int(clean, 16)
    except ValueError:
        return None
    return [clean[index : index + 64] for index in range(0, len(clean), 64)]


def _runtime_code(value: Any) -> bytes | None:
    if not isinstance(value, str) or not value.startswith("0x"):
        return None
    clean = value[2:]
    if len(clean) % 2 or len(clean) // 2 > MAX_RUNTIME_CODE_BYTES:
        return None
    try:
        return bytes.fromhex(clean)
    except ValueError:
        return None


def _valid_address(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 42 or not value.startswith("0x"):
        return False
    try:
        int(value[2:], 16)
        return True
    except ValueError:
        return False


def _signed_word(word: str) -> int:
    value = int(word, 16)
    return value - (1 << 256) if value >= (1 << 255) else value




def _storage_address(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    clean = value[2:] if value.startswith("0x") else value
    if len(clean) != 64:
        return None
    try:
        int(clean, 16)
    except ValueError:
        return None
    if clean[:24] != "0" * 24:
        return None
    tail = clean[-40:]
    if int(tail, 16) == 0:
        return None
    return "0x" + tail.lower()


def _governance_declaration(data: dict[str, Any]) -> dict[str, Any] | None:
    raw = data.get("governance_metadata") or data.get("governance")
    if not isinstance(raw, dict):
        return None
    out: dict[str, Any] = {}
    for key in ("timelock_seconds", "upgrade_delay_seconds", "multisig_threshold", "multisig_signers", "emergency_admin_count", "can_pause"):
        if key in raw:
            out[key] = raw[key]
    signers = out.get("multisig_signers")
    if isinstance(signers, list):
        out["multisig_signer_count"] = len(signers)
        out["multisig_signers"] = [str(x) for x in signers[:25]]
    elif isinstance(signers, (int, float)):
        out["multisig_signer_count"] = int(signers)
    return out or None


def _apply_governance_declaration(result: "ProtocolNativeResult", data: dict[str, Any]) -> dict[str, Any] | None:
    gov = _governance_declaration(data)
    if not gov:
        return None
    def num(name: str) -> float | None:
        value = gov.get(name)
        try:
            return float(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    timelock = num("timelock_seconds")
    upgrade_delay = num("upgrade_delay_seconds")
    threshold = num("multisig_threshold")
    signer_count = num("multisig_signer_count")
    emergency_admins = num("emergency_admin_count")
    if timelock is not None:
        if timelock <= 0:
            result.risk_delta += 15
            result.warnings.append("Caller-declared governance has no timelock delay.")
        elif timelock < 3600:
            result.risk_delta += 10
            result.warnings.append("Caller-declared governance timelock is under one hour.")
        elif timelock < 86400:
            result.risk_delta += 5
    if upgrade_delay is not None and upgrade_delay < 3600:
        result.risk_delta += 8
        result.warnings.append("Caller-declared upgrade delay is under one hour.")
    if signer_count is not None:
        if signer_count <= 1:
            result.risk_delta += 15
            result.warnings.append("Caller-declared governance/admin control has one or fewer multisig signers.")
        elif threshold is not None and threshold / signer_count < 0.5:
            result.risk_delta += 8
            result.warnings.append("Caller-declared multisig threshold is below 50% of signers.")
    if emergency_admins is not None and emergency_admins > 0:
        result.risk_delta += min(8.0, 3.0 + emergency_admins)
        result.warnings.append("Caller-declared emergency administrator authority exists and requires policy review.")
    if gov.get("can_pause") is True:
        result.risk_delta += 3
    now = datetime.now(timezone.utc)
    result.evidence.append(EvidenceRecord(
        evidence_id=str(uuid4()), provider="user_input", source_type="declared_governance_metadata",
        provider_endpoint="analysis request", retrieved_at=now, observed_at=now, normalized_value=gov,
        calculation_version="protocol-native-1.1.0", engine_version="shared-1.1.0", confidence=45,
        freshness=FreshnessStatus.CURRENT, license_classification="user-supplied-unverified",
    ))
    result.assumptions.append("Governance/timelock/multisig metadata is caller-declared unless independently corroborated by a protocol-specific adapter or direct contract-state rule.")
    return gov

def _freshness(updated_at: int) -> tuple[FreshnessStatus, float | None]:
    if not updated_at or updated_at > UINT256_MAX:
        return FreshnessStatus.UNKNOWN, None
    try:
        observed = datetime.fromtimestamp(updated_at, tz=timezone.utc)
    except (ValueError, OSError, OverflowError):
        return FreshnessStatus.UNKNOWN, None
    age = (datetime.now(timezone.utc) - observed).total_seconds()
    if age < -300:
        return FreshnessStatus.UNKNOWN, None
    age = max(0.0, age)
    status = (
        FreshnessStatus.LIVE if age <= 120 else
        FreshnessStatus.CURRENT if age <= 900 else
        FreshnessStatus.RECENT if age <= 3600 else
        FreshnessStatus.STALE if age <= 21600 else
        FreshnessStatus.EXPIRED
    )
    return status, age


def _evidence(
    call: ProviderCall,
    *,
    source_type: str,
    normalized: Any,
    chain_id: int,
    block: int | None,
    confidence: float,
    license_classification: str,
    freshness: FreshnessStatus | None = None,
    observed_at: datetime | None = None,
) -> EvidenceRecord:
    retrieved = datetime.now(timezone.utc)
    direct_state = source_type.startswith("direct")
    return EvidenceRecord(
        evidence_id=str(uuid4()),
        provider=call.provider_id,
        source_type=source_type,
        provider_endpoint=call.endpoint,
        provider_request_id=call.request_id,
        retrieved_at=retrieved,
        # External explorer metadata has no provider-normalized observation time.
        # Keep retrieval time only as the schema fallback and never inherit the RPC block.
        observed_at=observed_at or retrieved,
        block_number=block if direct_state else None,
        chain_id=chain_id,
        raw_reference=f"provider:{call.provider_id};request:{call.request_id}",
        normalized_value=normalized,
        calculation_version="protocol-native-1.2.0",
        engine_version="shared-1.1.0",
        confidence=confidence,
        freshness=freshness or (FreshnessStatus.LIVE if direct_state else FreshnessStatus.UNKNOWN),
        license_classification=license_classification,
    )


@dataclass
class ProtocolNativeResult:
    chain: ChainConfig
    block_number: int | None = None
    metrics: dict[str, Any] = field(default_factory=dict)
    evidence: list[EvidenceRecord] = field(default_factory=list)
    provider_status: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    missing_data: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    risk_delta: float = 0.0
    confidence: float = 0.0


def _declared_contracts(data: dict[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    raw = data.get("protocol_contracts")
    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, str):
                rows.append({"address": item, "role": "protocol_dependency"})
            elif isinstance(item, dict) and item.get("address"):
                rows.append({"address": str(item["address"]), "role": str(item.get("role") or "protocol_dependency")})
    singular = [
        ("contract_address", "core_protocol"),
        ("market_address", "market"),
        ("vault_address", "vault"),
        ("governance_contract", "governance"),
        ("admin_address", "admin"),
    ]
    for key, role in singular:
        if data.get(key):
            rows.append({"address": str(data[key]), "role": role})
    deps = data.get("dependency_contracts")
    if isinstance(deps, list):
        for item in deps:
            if isinstance(item, str):
                rows.append({"address": item, "role": "dependency"})
            elif isinstance(item, dict) and item.get("address"):
                rows.append({"address": str(item["address"]), "role": str(item.get("role") or "dependency")})
    # deterministic de-duplication by address+role
    seen = set()
    out = []
    for row in rows:
        row["address"] = row["address"].lower()
        key = (row["address"], row["role"])
        if key not in seen:
            seen.add(key)
            out.append(row)
    return out


def has_protocol_native_input(data: dict[str, Any]) -> bool:
    return bool(_declared_contracts(data) or data.get("protocol_oracle_feed") or _governance_declaration(data) or supports_protocol_adapter(data))


def collect_protocol_native(data: dict[str, Any]) -> ProtocolNativeResult:
    chain = normalize_chain(data.get("protocol_chain") or data.get("chain") or "ethereum")
    result = ProtocolNativeResult(chain=chain)
    declared = _declared_contracts(data)
    invalid = [row for row in declared if not _valid_address(row["address"])]
    if invalid:
        result.warnings.append(f"Ignored {len(invalid)} invalid declared protocol/dependency address(es).")
    declared = [row for row in declared if _valid_address(row["address"])]
    oracle_feed = data.get("protocol_oracle_feed")
    if oracle_feed and not _valid_address(oracle_feed):
        result.warnings.append("protocol_oracle_feed is not a valid EVM address and was not queried.")
        oracle_feed = None

    governance = _governance_declaration(data)
    protocol_adapter_requested = supports_protocol_adapter(data)
    if not declared and not oracle_feed and not protocol_adapter_requested:
        if governance:
            governance = _apply_governance_declaration(result, data)
            result.metrics = {"chain": chain.key, "block_number": None, "declared_contracts": [], "declared_oracle": None, "declared_governance": governance}
            result.confidence = 45.0
            result.missing_data.append("direct protocol-native contract/oracle evidence")
            result.assumptions.append("Rivexis never infers protocol contract roles from a protocol name alone in this generic adapter.")
            return result
        result.missing_data.append("declared protocol-native contract/oracle addresses")
        result.assumptions.append("Rivexis never infers protocol contract roles from a protocol name alone in this generic adapter.")
        return result

    try:
        rpc_provider, rpc, probe, fallback_errors = select_rpc_client(chain.key)
        result.provider_status.extend({"provider_id": x["provider_id"], "status": "FAILED_OR_UNAVAILABLE", "detail": x["error"]} for x in fallback_errors)
        result.provider_status.append({"provider_id": rpc_provider, "status": "HEALTHY", "latency_ms": round(probe.latency_ms, 2)})
        block_call = rpc.call("eth_blockNumber")
        chain_head = _rpc_quantity(block_call.result)
        if chain_head is None:
            raise ValueError("eth_blockNumber returned a non-canonical uint256 quantity")
        requested_block = data.get("at_block")
        if requested_block not in (None, "", "latest"):
            if isinstance(requested_block, bool):
                raise ValueError("at_block must be a non-negative integer or hex block number")
            try:
                historical_block = int(requested_block, 16) if isinstance(requested_block, str) and requested_block.lower().startswith("0x") else int(requested_block)
            except (TypeError, ValueError) as exc:
                raise ValueError("at_block must be a non-negative integer or hex block number") from exc
            if historical_block < 0 or historical_block > UINT256_MAX or historical_block > chain_head:
                raise ValueError("at_block must be non-negative and not greater than the current chain head")
            result.block_number = historical_block
            block_tag = hex(historical_block)
        else:
            result.block_number = chain_head
            block_tag = hex(chain_head)
        result.evidence.append(_evidence(block_call, source_type="direct_state", normalized={"chain_head_block": chain_head, "analysis_block": result.block_number, "block_tag": block_tag}, chain_id=chain.chain_id, block=chain_head, confidence=99, license_classification="direct-rpc"))
    except (ProviderError, ValueError) as exc:
        if isinstance(exc, ProviderError):
            result.provider_status.append({"provider_id": exc.provider_id, "status": exc.code, "detail": str(exc)})
        else:
            result.provider_status.append({"provider_id": "direct_rpc", "status": "MALFORMED_RPC_STATE", "detail": str(exc)})
        result.missing_data.append("protocol-native RPC state")
        result.warnings.append("Protocol-native RPC evidence was unavailable or malformed; no direct-state inference was made.")
        return result

    adapter_metrics = None
    if protocol_adapter_requested:
        try:
            adapter = collect_protocol_adapter(data, rpc=rpc, chain_id=chain.chain_id, block_number=result.block_number)
            adapter_metrics = adapter.metrics
            result.evidence.extend(adapter.evidence)
            result.warnings.extend(adapter.warnings)
            result.missing_data.extend(adapter.missing_data)
            result.assumptions.extend(adapter.assumptions)
            result.risk_delta += adapter.risk_delta
            result.confidence = max(result.confidence, adapter.confidence)
        except (ValueError, ProviderError) as exc:
            result.missing_data.append("protocol-specific adapter evidence")
            result.warnings.append(f"Protocol-specific adapter could not be completed: {exc}")

    explorer = EtherscanClient()
    contracts: list[dict[str, Any]] = []
    for row in declared[:25]:
        address = row["address"]
        role = row["role"]
        item: dict[str, Any] = {"address": address, "role": role, "verified_source": None, "proxy": None, "implementation": None}
        try:
            code_call = rpc.call("eth_getCode", [address, block_tag])
            code_bytes = _runtime_code(code_call.result)
            if code_bytes is None:
                raise ValueError("eth_getCode returned malformed or oversized runtime bytecode")
            has_code = bool(code_bytes)
            item.update({"has_code": has_code, "code_size_bytes": len(code_bytes) if has_code else 0, "code_sha256": hashlib.sha256(code_bytes).hexdigest() if has_code else None})
            result.evidence.append(_evidence(code_call, source_type="direct_contract_state", normalized=item.copy(), chain_id=chain.chain_id, block=result.block_number, confidence=99, license_classification="direct-rpc"))
            if not has_code and role in {"core_protocol", "market", "vault", "governance", "dependency", "protocol_dependency"}:
                result.risk_delta += 12
                result.warnings.append(f"Declared {role} address {address} has no runtime bytecode at the current block.")
            if not has_code and role == "admin":
                result.risk_delta += 10
                result.warnings.append("Declared admin address is an EOA at the current block; key-management/centralization controls require independent review.")
            if has_code and len(contracts) < 10:
                proxy_state: dict[str, Any] = {}
                for slot_name, slot in (("implementation", EIP1967_IMPLEMENTATION_SLOT), ("admin", EIP1967_ADMIN_SLOT), ("beacon", EIP1967_BEACON_SLOT)):
                    try:
                        slot_call = rpc.call("eth_getStorageAt", [address, slot, block_tag])
                        slot_words = _abi_words(slot_call.result, count=1)
                        if slot_words is None or slot_words[0][:24] != "0" * 24:
                            raise ValueError("malformed EIP-1967 storage word")
                        slot_address = _storage_address(slot_call.result)
                        proxy_state[slot_name] = slot_address
                        result.evidence.append(_evidence(
                            slot_call, source_type="direct_proxy_state",
                            normalized={"address": address, "role": role, "slot": slot_name, "value": slot_address},
                            chain_id=chain.chain_id, block=result.block_number, confidence=99, license_classification="direct-rpc",
                        ))
                    except (ProviderError, ValueError) as slot_exc:
                        proxy_state[slot_name] = None
                        provider_id = slot_exc.provider_id if isinstance(slot_exc, ProviderError) else "direct_rpc"
                        status_code = slot_exc.code if isinstance(slot_exc, ProviderError) else "MALFORMED_STORAGE_WORD"
                        result.provider_status.append({"provider_id": provider_id, "status": status_code, "detail": f"EIP-1967 {slot_name} slot: {slot_exc}"})
                        result.missing_data.append(f"canonical EIP-1967 {slot_name} state for {address}")
                item["eip1967"] = proxy_state
                if proxy_state.get("implementation") or proxy_state.get("beacon"):
                    result.risk_delta += 5
                    result.warnings.append(f"Direct EIP-1967 state indicates declared {role} contract {address} is upgradeable/proxied.")
                if proxy_state.get("admin"):
                    result.risk_delta += 5
                    result.warnings.append(f"Direct EIP-1967 admin slot is populated for declared {role} contract {address}; upgrade authority requires review.")
        except (ProviderError, ValueError) as exc:
            item["state_error"] = exc.code if isinstance(exc, ProviderError) else "MALFORMED_RUNTIME_CODE"
            result.missing_data.append(f"runtime code for {role}:{address}")
            result.warnings.append(f"Direct runtime code for declared {role} contract {address} was unusable; no deployed-code inference was made.")

        if explorer.configured and item.get("has_code"):
            try:
                source_call = explorer.get_source_code(chain, address)
                if not isinstance(source_call.result, dict):
                    raise ValueError("explorer source response is not an object")
                body = source_call.result
                rows = body.get("result")
                if not isinstance(rows, list) or len(rows) != 1 or not isinstance(rows[0], dict):
                    raise ValueError("explorer source response must contain one metadata row")
                first = rows[0]
                abi_raw = first.get("ABI")
                source_code_raw = first.get("SourceCode")
                proxy_raw = first.get("Proxy", "0")
                if not isinstance(abi_raw, str) or not isinstance(source_code_raw, str) or not isinstance(proxy_raw, str) or proxy_raw not in {"0", "1"}:
                    raise ValueError("explorer source metadata has malformed field types")
                abi = abi_raw
                source_code = source_code_raw
                verified = bool(source_code) and "not verified" not in abi.lower()
                proxy = proxy_raw == "1"
                implementation_raw = first.get("Implementation")
                if implementation_raw not in (None, "") and not _valid_address(implementation_raw):
                    raise ValueError("explorer implementation metadata is not a canonical EVM address")
                implementation = (
                    str(implementation_raw).lower()
                    if _valid_address(implementation_raw)
                    else None
                )
                item.update({"verified_source": verified, "proxy": proxy, "implementation": implementation, "contract_name": first.get("ContractName")})
                direct_impl = ((item.get("eip1967") or {}).get("implementation"))
                if direct_impl and implementation and direct_impl.lower() != implementation.lower():
                    result.risk_delta += 8
                    result.warnings.append(f"Direct EIP-1967 implementation for {address} conflicts with explorer implementation metadata.")
                    item["implementation_conflict"] = {"direct_eip1967": direct_impl, "explorer": implementation.lower()}
                result.evidence.append(_evidence(source_call, source_type="verified_contract_metadata", normalized={"address": address, "role": role, "verified_source": verified, "proxy": proxy, "implementation": implementation, "contract_name": first.get("ContractName")}, chain_id=chain.chain_id, block=None, confidence=95, license_classification="external-provider-attributed"))
                if not verified:
                    result.risk_delta += 10
                    result.warnings.append(f"Declared {role} contract {address} is not verified by the configured explorer evidence.")
                if proxy:
                    result.risk_delta += 6
                    result.warnings.append(f"Declared {role} contract {address} is a proxy; implementation and upgrade authority require review.")
            except (ProviderError, ValueError) as exc:
                status_code = exc.code if isinstance(exc, ProviderError) else "MALFORMED_EXPLORER_METADATA"
                result.provider_status.append({"provider_id": "etherscan", "status": status_code, "detail": str(exc)})
                result.missing_data.append(f"verified source/proxy metadata for {address}")
        elif item.get("has_code"):
            result.missing_data.append(f"verified source/proxy metadata for {address}")
        contracts.append(item)

    oracle: dict[str, Any] | None = None
    if oracle_feed:
        try:
            dec_call = rpc.call("eth_call", [{"to": oracle_feed, "data": DECIMALS_SELECTOR}, block_tag])
            decimal_words = _abi_words(dec_call.result, count=1)
            decimals = int(decimal_words[0], 16) if decimal_words else None
            round_call = rpc.call("eth_call", [{"to": oracle_feed, "data": LATEST_ROUND_DATA_SELECTOR}, block_tag])
            words = _abi_words(round_call.result, count=5)
            if decimals is None or not (0 <= decimals <= 36) or words is None:
                raise ValueError("malformed AggregatorV3 response")
            round_id = int(words[0], 16)
            answer_raw = _signed_word(words[1])
            updated_at = int(words[3], 16)
            answered_in_round = int(words[4], 16)
            status, age = _freshness(updated_at)
            observed_at = None
            if age is not None:
                observed_at = datetime.fromtimestamp(updated_at, tz=timezone.utc)
            oracle = {
                "feed_address": oracle_feed,
                "decimals": decimals,
                "answer": answer_raw / (10 ** decimals),
                "answer_raw": answer_raw,
                "round_id": round_id,
                "updated_at": updated_at,
                "answered_in_round": answered_in_round,
                "age_seconds": age,
                "freshness": status.value,
            }
            result.evidence.append(_evidence(round_call, source_type="direct_oracle_state", normalized=oracle, chain_id=chain.chain_id, block=result.block_number, confidence=97, license_classification="direct-rpc", freshness=status, observed_at=observed_at))
            if answer_raw <= 0:
                result.risk_delta += 35
                result.warnings.append("Declared protocol oracle returned a non-positive answer.")
            if status in {FreshnessStatus.STALE, FreshnessStatus.EXPIRED}:
                result.risk_delta += 22
                result.warnings.append("Declared protocol oracle is stale/expired under Rivexis generic freshness thresholds.")
            if status == FreshnessStatus.UNKNOWN:
                result.missing_data.append("credible protocol oracle observation timestamp")
                result.warnings.append("Declared protocol oracle observation time is missing, malformed, or materially future-dated; freshness remains UNKNOWN.")
            if answered_in_round < round_id:
                result.risk_delta += 22
                result.warnings.append("Declared protocol oracle answeredInRound is behind the reported round id.")
        except (ProviderError, ValueError, OverflowError) as exc:
            result.missing_data.append("normalized protocol oracle state")
            result.warnings.append(f"Declared protocol oracle could not be normalized: {exc}")

    governance = _apply_governance_declaration(result, data)
    result.metrics = {"chain": chain.key, "block_number": result.block_number, "declared_contracts": contracts, "declared_oracle": oracle, "declared_governance": governance, "protocol_adapter": adapter_metrics}
    result.risk_delta = min(55.0, result.risk_delta)
    contract_state_observed = any("has_code" in item for item in contracts)
    oracle_is_fresh = bool(oracle and oracle.get("freshness") != FreshnessStatus.UNKNOWN.value)
    result.confidence = max(result.confidence, min(92.0, 62.0 + (12 if contract_state_observed else 0) + (12 if oracle_is_fresh else 0)))
    result.assumptions.extend([
        "Contract roles and dependency relationships are caller-declared unless a protocol-specific adapter independently verifies them.",
        "A supplied AggregatorV3-compatible feed is treated as declared oracle evidence; Rivexis does not infer that it is the protocol's authoritative oracle from compatibility alone.",
    ])
    if not explorer.configured and contracts:
        result.provider_status.append({"provider_id": "etherscan", "status": "CREDENTIALS_REQUIRED"})
    return result
