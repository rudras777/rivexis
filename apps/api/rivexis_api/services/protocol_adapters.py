from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import math
import os
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from rivexis_api.models.enums import FreshnessStatus
from rivexis_api.models.evidence import EvidenceRecord
from rivexis_api.provider_clients import ProviderCall, ProviderError, hex_to_int
from rivexis_api.services.evm_decode import function_selector
from rivexis_api.services.deployment_registry import enrich_protocol_adapter_input

WAD = 10**18
MORPHO_ORACLE_SCALE = 10**36
MORPHO_BLUE_MAINNET = "0xbbbbbbbbbb9cc5e90e3b3af64bdaf62c37eeffcb"


def _valid_address(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 42 or not value.startswith("0x"):
        return False
    try:
        int(value[2:], 16)
        return True
    except ValueError:
        return False


def _valid_bytes32(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 66 or not value.startswith("0x"):
        return False
    try:
        int(value[2:], 16)
        return True
    except ValueError:
        return False


def _word_uint(word: str) -> int:
    return int(word, 16)


def _word_address(word: str) -> str:
    return "0x" + word[-40:].lower()


def _word_bool(word: str) -> bool:
    return bool(int(word, 16))

def _word_int256(word: str) -> int:
    value = int(word, 16)
    return value - 2**256 if value >= 2**255 else value


def _words(raw: Any, minimum: int = 1) -> list[str]:
    if not isinstance(raw, str) or not raw.startswith("0x"):
        raise ValueError("contract call returned non-hex data")
    clean = raw[2:]
    if len(clean) < minimum * 64 or len(clean) % 64 != 0:
        raise ValueError("contract call returned malformed ABI data")
    return [clean[i:i + 64] for i in range(0, len(clean), 64)]


def _encode_address(address: str) -> str:
    if not _valid_address(address):
        raise ValueError("invalid EVM address")
    return address[2:].lower().rjust(64, "0")


def _encode_bytes32(value: str) -> str:
    if not _valid_bytes32(value):
        raise ValueError("invalid bytes32 value")
    return value[2:].lower()


def _calldata(signature: str, *encoded_words: str) -> str:
    return function_selector(signature) + "".join(encoded_words)


def _eth_call(rpc, to: str, signature: str, *encoded_words: str, block_tag: str = "latest") -> ProviderCall:
    return rpc.call("eth_call", [{"to": to, "data": _calldata(signature, *encoded_words)}, block_tag])

def _runtime_code_fingerprint(rpc, address: str, block_tag: str) -> tuple[ProviderCall, dict[str, Any]]:
    call = rpc.call("eth_getCode", [address, block_tag])
    raw = call.result
    if not isinstance(raw, str) or not raw.startswith("0x"):
        raise ValueError("eth_getCode returned malformed runtime bytecode")
    clean = raw[2:]
    if len(clean) % 2:
        raise ValueError("eth_getCode returned malformed runtime bytecode")
    code = bytes.fromhex(clean) if clean else b""
    return call, {
        "address": address.lower(),
        "runtime_code_bytes": len(code),
        "runtime_code_sha256": hashlib.sha256(code).hexdigest() if code else None,
        "code_present": bool(code),
    }


def _encode_uint(value: int) -> str:
    return hex(int(value))[2:].rjust(64, "0")


def _resolved_block(data: dict[str, Any], current_block: int | None) -> tuple[int | None, str]:
    raw = data.get("at_block")
    if raw in (None, "", "latest"):
        return current_block, "latest"
    try:
        value = int(raw, 16) if isinstance(raw, str) and raw.lower().startswith("0x") else int(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError("at_block must be a non-negative integer or hex block number") from exc
    if value < 0:
        raise ValueError("at_block must be non-negative")
    if current_block is not None and value > current_block:
        raise ValueError("at_block cannot be greater than the current chain head")
    return value, hex(value)


def _registry_evidence(identity: dict[str, Any], *, chain_id: int, block: int | None) -> EvidenceRecord:
    now = datetime.now(timezone.utc)
    return EvidenceRecord(
        evidence_id=str(uuid4()), provider="rivexis_registry", source_type="official_deployment_registry",
        provider_endpoint=identity.get("source_ref"), retrieved_at=now, observed_at=now,
        block_number=block, chain_id=chain_id, raw_reference=identity.get("source_ref"),
        normalized_value=identity, calculation_version="deployment-registry-1.0.0",
        engine_version="shared-1.4.0", confidence=100 if identity.get("status") == "VERIFIED" else 70,
        freshness=FreshnessStatus.CURRENT, license_classification="official-public-registry",
    )


def _evidence(call: ProviderCall, *, protocol: str, source_type: str, normalized: Any, chain_id: int, block: int | None, confidence: float = 99) -> EvidenceRecord:
    return EvidenceRecord(
        evidence_id=str(uuid4()), provider=call.provider_id, source_type=source_type,
        provider_endpoint=call.endpoint, provider_request_id=call.request_id,
        retrieved_at=datetime.now(timezone.utc), observed_at=datetime.now(timezone.utc),
        block_number=block, chain_id=chain_id,
        raw_reference=f"provider:{call.provider_id};request:{call.request_id};protocol:{protocol}",
        normalized_value=normalized, calculation_version="protocol-adapters-1.0.0",
        engine_version="shared-1.3.0", confidence=confidence,
        freshness=FreshnessStatus.LIVE, license_classification="direct-rpc",
    )


@dataclass
class ProtocolAdapterResult:
    adapter: str
    metrics: dict[str, Any] = field(default_factory=dict)
    evidence: list[EvidenceRecord] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    missing_data: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    risk_delta: float = 0.0
    confidence: float = 0.0


def supports_protocol_adapter(data: dict[str, Any]) -> bool:
    return str(data.get("protocol_adapter") or data.get("protocol_type") or "").strip().lower() in {
        "aave_v3", "aave-v3", "aave",
        "compound_v3", "compound-iii", "compound_iii", "comet",
        "morpho_blue", "morpho-blue", "morpho",
    }


def collect_protocol_adapter(data: dict[str, Any], *, rpc, chain_id: int, block_number: int | None) -> ProtocolAdapterResult:
    enriched, identity = enrich_protocol_adapter_input(data, chain_id)
    resolved_block, block_tag = _resolved_block(enriched, block_number)
    enriched["_rivexis_block_tag"] = block_tag
    enriched["_rivexis_deployment_identity"] = identity
    adapter = str(enriched.get("protocol_adapter") or enriched.get("protocol_type") or "").strip().lower()
    if adapter in {"aave_v3", "aave-v3", "aave"}:
        out = _collect_aave_v3(enriched, rpc=rpc, chain_id=chain_id, block_number=resolved_block)
    elif adapter in {"compound_v3", "compound-iii", "compound_iii", "comet"}:
        out = _collect_compound_v3(enriched, rpc=rpc, chain_id=chain_id, block_number=resolved_block)
    elif adapter in {"morpho_blue", "morpho-blue", "morpho"}:
        out = _collect_morpho_blue(enriched, rpc=rpc, chain_id=chain_id, block_number=resolved_block)
    else:
        raise ValueError(f"Unsupported protocol_adapter: {adapter or '<empty>'}")

    out.metrics["deployment_identity"] = identity
    out.metrics["read_block_number"] = resolved_block
    out.metrics["block_tag"] = block_tag
    out.evidence.append(_registry_evidence(identity, chain_id=chain_id, block=resolved_block))
    marker = "official deployment identity allowlist verification"
    if identity.get("status") == "VERIFIED":
        out.missing_data = [x for x in out.missing_data if x != marker]
        out.assumptions.append("Core deployment identity matched the versioned Rivexis snapshot of an official protocol-owned deployment source.")
        out.confidence = min(100.0, out.confidence + 3)
    elif identity.get("status") == "MISMATCH":
        out.risk_delta = min(100.0, out.risk_delta + 25)
        out.warnings.append("Supplied core protocol address does not match the selected official deployment registry record.")
    else:
        if marker not in out.missing_data:
            out.missing_data.append(marker)
    if block_tag != "latest":
        out.assumptions.append("Historical protocol state was queried at the caller-requested block; the deployment registry snapshot itself is a current identity snapshot, not proof of historical registry membership.")
    return out


def _collect_aave_v3(data: dict[str, Any], *, rpc, chain_id: int, block_number: int | None) -> ProtocolAdapterResult:
    out = ProtocolAdapterResult(adapter="aave_v3")
    block_tag = str(data.get("_rivexis_block_tag") or "latest")
    rpc_call = lambda to, signature, *words: _eth_call(rpc, to, signature, *words, block_tag=block_tag)
    provider = str(data.get("aave_data_provider") or data.get("pool_data_provider") or "")
    asset = str(data.get("asset_address") or data.get("underlying_asset") or "")
    if not (_valid_address(provider) and _valid_address(asset)):
        raise ValueError("Aave V3 adapter requires valid aave_data_provider/pool_data_provider and asset_address")
    encoded_asset = _encode_address(asset)

    cfg_call = rpc_call(provider, "getReserveConfigurationData(address)", encoded_asset)
    w = _words(cfg_call.result, 10)
    cfg = {
        "asset": asset.lower(), "decimals": _word_uint(w[0]),
        "ltv_bps": _word_uint(w[1]), "liquidation_threshold_bps": _word_uint(w[2]),
        "liquidation_bonus_bps": _word_uint(w[3]), "reserve_factor_bps": _word_uint(w[4]),
        "usage_as_collateral_enabled": _word_bool(w[5]), "borrowing_enabled": _word_bool(w[6]),
        "stable_borrow_rate_enabled": _word_bool(w[7]), "is_active": _word_bool(w[8]), "is_frozen": _word_bool(w[9]),
    }
    out.evidence.append(_evidence(cfg_call, protocol="aave_v3", source_type="protocol_native_reserve_configuration", normalized=cfg, chain_id=chain_id, block=block_number))

    def scalar(signature: str, name: str, decoder=_word_uint):
        try:
            call = rpc_call(provider, signature, encoded_asset)
            value = decoder(_words(call.result, 1)[0])
            out.evidence.append(_evidence(call, protocol="aave_v3", source_type="protocol_native_risk_parameter", normalized={"asset": asset.lower(), name: value}, chain_id=chain_id, block=block_number))
            return value
        except (ProviderError, ValueError) as exc:
            out.missing_data.append(f"Aave {name}")
            out.warnings.append(f"Aave {name} could not be read: {exc}")
            return None

    try:
        caps_call = rpc_call(provider, "getReserveCaps(address)", encoded_asset)
        cw = _words(caps_call.result, 2)
        caps = {"borrow_cap": _word_uint(cw[0]), "supply_cap": _word_uint(cw[1])}
        out.evidence.append(_evidence(caps_call, protocol="aave_v3", source_type="protocol_native_caps", normalized={"asset": asset.lower(), **caps}, chain_id=chain_id, block=block_number))
    except (ProviderError, ValueError) as exc:
        caps = {"borrow_cap": None, "supply_cap": None}
        out.missing_data.append("Aave reserve caps")
        out.warnings.append(f"Aave reserve caps could not be read: {exc}")

    debt_ceiling = scalar("getDebtCeiling(address)", "debt_ceiling")
    paused = scalar("getPaused(address)", "paused", _word_bool)
    siloed = scalar("getSiloedBorrowing(address)", "siloed_borrowing", _word_bool)
    liquidation_fee = scalar("getLiquidationProtocolFee(address)", "liquidation_protocol_fee_bps")
    emode = scalar("getReserveEModeCategory(address)", "emode_category")

    interest_rate_strategy = None
    oracle_source = None
    emode_config = None
    identity = data.get("_rivexis_deployment_identity") or {}
    if identity.get("status") == "VERIFIED":
        try:
            icall = rpc_call(provider, "getInterestRateStrategyAddress(address)", encoded_asset)
            interest_rate_strategy = _word_address(_words(icall.result, 1)[0])
            out.evidence.append(_evidence(icall, protocol="aave_v3", source_type="protocol_native_interest_rate_strategy", normalized={"asset": asset.lower(), "interest_rate_strategy": interest_rate_strategy}, chain_id=chain_id, block=block_number))
        except (ProviderError, ValueError) as exc:
            out.missing_data.append("Aave interest rate strategy")
            out.warnings.append(f"Aave interest rate strategy could not be read: {exc}")

        oracle_address = str(data.get("aave_oracle") or "")
        if _valid_address(oracle_address):
            try:
                ocall = rpc_call(oracle_address, "getSourceOfAsset(address)", encoded_asset)
                oracle_source = _word_address(_words(ocall.result, 1)[0])
                out.evidence.append(_evidence(ocall, protocol="aave_v3", source_type="protocol_native_oracle_source", normalized={"asset": asset.lower(), "aave_oracle": oracle_address.lower(), "source": oracle_source}, chain_id=chain_id, block=block_number))
            except (ProviderError, ValueError) as exc:
                out.missing_data.append("Aave asset oracle source")
                out.warnings.append(f"Aave asset oracle source could not be read: {exc}")

        pool_for_emode = str(data.get("aave_pool") or "")
        if emode and _valid_address(pool_for_emode):
            try:
                ecall = rpc_call(pool_for_emode, "getEModeCategoryData(uint8)", _encode_uint(int(emode)))
                ew = _words(ecall.result, 4)
                emode_config = {
                    "category": int(emode), "ltv_bps": _word_uint(ew[0]),
                    "liquidation_threshold_bps": _word_uint(ew[1]), "liquidation_bonus_bps": _word_uint(ew[2]),
                    "deprecated_price_source": _word_address(ew[3]),
                }
                out.evidence.append(_evidence(ecall, protocol="aave_v3", source_type="protocol_native_emode_configuration", normalized=emode_config, chain_id=chain_id, block=block_number))
                out.assumptions.append("Aave getEModeCategoryData is retained for compatibility; its legacy priceSource field is deprecated and is not treated as authoritative oracle evidence.")
            except (ProviderError, ValueError) as exc:
                out.missing_data.append("Aave eMode category configuration")
                out.warnings.append(f"Aave eMode category configuration could not be read: {exc}")

    ltv = cfg["ltv_bps"] / 10000
    threshold = cfg["liquidation_threshold_bps"] / 10000
    buffer = threshold - ltv
    if not cfg["is_active"]:
        out.risk_delta += 35; out.warnings.append("Aave reserve is inactive.")
    if cfg["is_frozen"]:
        out.risk_delta += 15; out.warnings.append("Aave reserve is frozen.")
    if paused:
        out.risk_delta += 25; out.warnings.append("Aave reserve is paused.")
    if cfg["liquidation_threshold_bps"] and cfg["liquidation_threshold_bps"] <= cfg["ltv_bps"]:
        out.risk_delta += 25; out.warnings.append("Aave liquidation threshold is not above LTV.")
    elif 0 < buffer < 0.03:
        out.risk_delta += 8; out.warnings.append("Aave LTV-to-liquidation-threshold buffer is below 3 percentage points.")

    position = None
    pool = data.get("aave_pool") or data.get("pool_address")
    user = data.get("user_address") or data.get("wallet")
    if _valid_address(pool) and _valid_address(user):
        try:
            call = rpc_call(str(pool), "getUserAccountData(address)", _encode_address(str(user)))
            pw = _words(call.result, 6)
            hf_raw = _word_uint(pw[5])
            position = {
                "user": str(user).lower(), "total_collateral_base": _word_uint(pw[0]), "total_debt_base": _word_uint(pw[1]),
                "available_borrows_base": _word_uint(pw[2]), "current_liquidation_threshold_bps": _word_uint(pw[3]),
                "ltv_bps": _word_uint(pw[4]), "health_factor": hf_raw / WAD if hf_raw else None,
            }
            out.evidence.append(_evidence(call, protocol="aave_v3", source_type="protocol_native_position", normalized=position, chain_id=chain_id, block=block_number))
            if position["health_factor"] is not None:
                hf = position["health_factor"]
                if hf < 1: out.risk_delta += 45; out.warnings.append("Aave account is at/below liquidation health factor 1.0.")
                elif hf < 1.05: out.risk_delta += 28
                elif hf < 1.2: out.risk_delta += 15
        except (ProviderError, ValueError) as exc:
            out.missing_data.append("Aave user account data")
            out.warnings.append(f"Aave user account data could not be read: {exc}")

    out.metrics = {
        "adapter": "aave_v3", "data_provider": provider.lower(), "reserve_configuration": cfg,
        "reserve_caps": caps, "debt_ceiling": debt_ceiling, "paused": paused,
        "siloed_borrowing": siloed, "liquidation_protocol_fee_bps": liquidation_fee,
        "emode_category": emode, "emode_configuration": emode_config,
        "interest_rate_strategy": interest_rate_strategy, "asset_oracle_source": oracle_source,
        "ltv_liquidation_buffer_pct_points": round(buffer * 100, 4), "position": position,
    }
    out.assumptions.append("Aave parameters are read from the caller-supplied Aave Protocol Data Provider; deployment identity must still be validated by allowlist or governance metadata in production.")
    out.missing_data.append("official deployment identity allowlist verification")
    out.confidence = 97 if not out.missing_data else 90
    out.risk_delta = min(65.0, out.risk_delta)
    return out


def _collect_compound_v3(data: dict[str, Any], *, rpc, chain_id: int, block_number: int | None) -> ProtocolAdapterResult:
    out = ProtocolAdapterResult(adapter="compound_v3")
    block_tag = str(data.get("_rivexis_block_tag") or "latest")
    rpc_call = lambda to, signature, *words: _eth_call(rpc, to, signature, *words, block_tag=block_tag)
    comet = str(data.get("comet_address") or data.get("market_address") or "")
    asset = str(data.get("collateral_asset") or data.get("asset_address") or "")
    if not (_valid_address(comet) and _valid_address(asset)):
        raise ValueError("Compound III adapter requires valid comet_address/market_address and collateral_asset")
    call = rpc_call(comet, "getAssetInfoByAddress(address)", _encode_address(asset))
    w = _words(call.result, 8)
    info = {
        "offset": _word_uint(w[0]), "asset": _word_address(w[1]), "price_feed": _word_address(w[2]),
        "scale": _word_uint(w[3]), "borrow_collateral_factor": _word_uint(w[4]) / WAD,
        "liquidate_collateral_factor": _word_uint(w[5]) / WAD,
        "liquidation_factor": _word_uint(w[6]) / WAD, "supply_cap_raw": _word_uint(w[7]),
    }
    out.evidence.append(_evidence(call, protocol="compound_v3", source_type="protocol_native_asset_configuration", normalized=info, chain_id=chain_id, block=block_number))
    if info["asset"].lower() != asset.lower():
        out.risk_delta += 35; out.warnings.append("Compound returned asset metadata for a different collateral address.")
    if info["liquidate_collateral_factor"] <= info["borrow_collateral_factor"]:
        out.risk_delta += 25; out.warnings.append("Compound liquidation collateral factor is not above borrow collateral factor.")
    elif info["liquidate_collateral_factor"] - info["borrow_collateral_factor"] < 0.03:
        out.risk_delta += 8; out.warnings.append("Compound borrow-to-liquidation collateral-factor buffer is below 3 percentage points.")

    price = None
    try:
        pcall = rpc_call(comet, "getPrice(address)", _encode_address(info["price_feed"]))
        price_raw = _word_uint(_words(pcall.result, 1)[0])
        price = {"price_feed": info["price_feed"], "price_usd": price_raw / 1e8, "price_raw": price_raw, "scale": 10**8}
        out.evidence.append(_evidence(pcall, protocol="compound_v3", source_type="protocol_native_oracle_price", normalized=price, chain_id=chain_id, block=block_number))
        if price_raw <= 0:
            out.risk_delta += 35; out.warnings.append("Compound protocol price feed returned a non-positive price.")
    except (ProviderError, ValueError) as exc:
        out.missing_data.append("Compound collateral price")
        out.warnings.append(f"Compound collateral price could not be read: {exc}")

    position = None
    user = data.get("user_address") or data.get("wallet")
    if _valid_address(user):
        try:
            liq_call = rpc_call(comet, "isLiquidatable(address)", _encode_address(str(user)))
            collat_call = rpc_call(comet, "isBorrowCollateralized(address)", _encode_address(str(user)))
            borrow_call = rpc_call(comet, "borrowBalanceOf(address)", _encode_address(str(user)))
            cb_call = rpc_call(comet, "collateralBalanceOf(address,address)", _encode_address(str(user)), _encode_address(asset))
            position = {
                "user": str(user).lower(), "is_liquidatable": _word_bool(_words(liq_call.result, 1)[0]),
                "is_borrow_collateralized": _word_bool(_words(collat_call.result, 1)[0]),
                "borrow_balance_raw": _word_uint(_words(borrow_call.result, 1)[0]),
                "collateral_balance_raw": _word_uint(_words(cb_call.result, 1)[0]),
            }
            for c, label, norm in (
                (liq_call, "protocol_native_liquidation_state", {"user": position["user"], "is_liquidatable": position["is_liquidatable"]}),
                (collat_call, "protocol_native_borrow_collateralization", {"user": position["user"], "is_borrow_collateralized": position["is_borrow_collateralized"]}),
                (borrow_call, "protocol_native_position_balance", {"user": position["user"], "borrow_balance_raw": position["borrow_balance_raw"]}),
                (cb_call, "protocol_native_position_balance", {"user": position["user"], "asset": asset.lower(), "collateral_balance_raw": position["collateral_balance_raw"]}),
            ):
                out.evidence.append(_evidence(c, protocol="compound_v3", source_type=label, normalized=norm, chain_id=chain_id, block=block_number))
            if position["is_liquidatable"]:
                out.risk_delta += 50; out.warnings.append("Compound reports the supplied account as presently liquidatable.")
            elif not position["is_borrow_collateralized"]:
                out.risk_delta += 18; out.warnings.append("Compound reports the account is not sufficiently collateralized for additional borrowing.")
        except (ProviderError, ValueError) as exc:
            out.missing_data.append("Compound user position state")
            out.warnings.append(f"Compound user position state could not be read: {exc}")

    core_configuration = None
    identity = data.get("_rivexis_deployment_identity") or {}
    if identity.get("status") == "VERIFIED":
        core_configuration = {}
        address_getters = {
            "governor": "governor()", "pause_guardian": "pauseGuardian()", "base_token": "baseToken()",
            "base_token_price_feed": "baseTokenPriceFeed()", "extension_delegate": "extensionDelegate()",
        }
        uint_getters = {"num_assets": "numAssets()", "utilization": "getUtilization()", "target_reserves": "targetReserves()"}
        bool_getters = {
            "supply_paused": "isSupplyPaused()", "transfer_paused": "isTransferPaused()",
            "withdraw_paused": "isWithdrawPaused()", "absorb_paused": "isAbsorbPaused()", "buy_paused": "isBuyPaused()",
        }
        for key, signature in address_getters.items():
            try:
                c = rpc_call(comet, signature); core_configuration[key] = _word_address(_words(c.result, 1)[0])
                out.evidence.append(_evidence(c, protocol="compound_v3", source_type="protocol_native_core_configuration", normalized={key: core_configuration[key]}, chain_id=chain_id, block=block_number))
            except (ProviderError, ValueError) as exc:
                out.missing_data.append(f"Compound {key}"); out.warnings.append(f"Compound {key} could not be read: {exc}")
        for key, signature in uint_getters.items():
            try:
                c = rpc_call(comet, signature); core_configuration[key] = _word_uint(_words(c.result, 1)[0])
                out.evidence.append(_evidence(c, protocol="compound_v3", source_type="protocol_native_core_configuration", normalized={key: core_configuration[key]}, chain_id=chain_id, block=block_number))
            except (ProviderError, ValueError) as exc:
                out.missing_data.append(f"Compound {key}")
        for key, signature in bool_getters.items():
            try:
                c = rpc_call(comet, signature); core_configuration[key] = _word_bool(_words(c.result, 1)[0])
                out.evidence.append(_evidence(c, protocol="compound_v3", source_type="protocol_native_pause_state", normalized={key: core_configuration[key]}, chain_id=chain_id, block=block_number))
            except (ProviderError, ValueError):
                out.missing_data.append(f"Compound {key}")
        expected_governor = data.get("compound_governor_expected")
        expected_guardian = data.get("compound_pause_guardian_expected")
        if expected_governor and core_configuration.get("governor") and core_configuration["governor"].lower() != str(expected_governor).lower():
            out.risk_delta += 8; out.warnings.append("Compound on-chain governor differs from the current Rivexis official deployment snapshot; review governance/upgrade history.")
        if expected_guardian and core_configuration.get("pause_guardian") and core_configuration["pause_guardian"].lower() != str(expected_guardian).lower():
            out.risk_delta += 5; out.warnings.append("Compound on-chain pause guardian differs from the current Rivexis official deployment snapshot; review governance/upgrade history.")

    out.metrics = {"adapter": "compound_v3", "comet": comet.lower(), "asset_info": info, "protocol_price": price, "position": position, "core_configuration": core_configuration}
    out.assumptions.append("Compound III risk parameters and liquidatability are read from the caller-supplied Comet deployment; deployment identity must be allowlisted independently in production.")
    out.missing_data.append("official deployment identity allowlist verification")
    out.confidence = 98 if price is not None else 91
    out.risk_delta = min(70.0, out.risk_delta)
    return out


def _collect_morpho_blue(data: dict[str, Any], *, rpc, chain_id: int, block_number: int | None) -> ProtocolAdapterResult:
    out = ProtocolAdapterResult(adapter="morpho_blue")
    block_tag = str(data.get("_rivexis_block_tag") or "latest")
    rpc_call = lambda to, signature, *words: _eth_call(rpc, to, signature, *words, block_tag=block_tag)
    market_id = str(data.get("morpho_market_id") or data.get("market_id") or "")
    contract = str(data.get("morpho_contract") or (MORPHO_BLUE_MAINNET if chain_id == 1 else ""))
    if not _valid_bytes32(market_id):
        raise ValueError("Morpho Blue adapter requires morpho_market_id/market_id bytes32")
    if not _valid_address(contract):
        raise ValueError("Morpho Blue adapter requires morpho_contract outside Ethereum mainnet")
    encoded_id = _encode_bytes32(market_id)
    pcall = rpc_call(contract, "idToMarketParams(bytes32)", encoded_id)
    pw = _words(pcall.result, 5)
    params = {
        "market_id": market_id.lower(), "loan_token": _word_address(pw[0]), "collateral_token": _word_address(pw[1]),
        "oracle": _word_address(pw[2]), "irm": _word_address(pw[3]), "lltv": _word_uint(pw[4]) / WAD,
        "lltv_wad": _word_uint(pw[4]),
    }
    out.evidence.append(_evidence(pcall, protocol="morpho_blue", source_type="protocol_native_market_parameters", normalized=params, chain_id=chain_id, block=block_number))

    mcall = rpc_call(contract, "market(bytes32)", encoded_id)
    mw = _words(mcall.result, 6)
    state = {
        "total_supply_assets_raw": _word_uint(mw[0]), "total_supply_shares_raw": _word_uint(mw[1]),
        "total_borrow_assets_raw": _word_uint(mw[2]), "total_borrow_shares_raw": _word_uint(mw[3]),
        "last_update": _word_uint(mw[4]), "fee_wad": _word_uint(mw[5]), "fee": _word_uint(mw[5]) / WAD,
    }
    supply = state["total_supply_assets_raw"]
    borrow = state["total_borrow_assets_raw"]
    state["utilization"] = borrow / supply if supply else None
    out.evidence.append(_evidence(mcall, protocol="morpho_blue", source_type="protocol_native_market_state", normalized=state, chain_id=chain_id, block=block_number))

    price = None
    if int(params["oracle"], 16) != 0:
        try:
            ocall = rpc_call(params["oracle"], "price()")
            price_raw = _word_uint(_words(ocall.result, 1)[0])
            price = {"oracle": params["oracle"], "price_raw": price_raw, "price_collateral_in_loan": price_raw / MORPHO_ORACLE_SCALE, "scale": MORPHO_ORACLE_SCALE}
            out.evidence.append(_evidence(ocall, protocol="morpho_blue", source_type="protocol_native_oracle_price", normalized=price, chain_id=chain_id, block=block_number))
            if price_raw <= 0:
                out.risk_delta += 40; out.warnings.append("Morpho market oracle returned a non-positive price.")
        except (ProviderError, ValueError) as exc:
            out.missing_data.append("Morpho market oracle price")
            out.warnings.append(f"Morpho market oracle price could not be read: {exc}")
    else:
        out.missing_data.append("Morpho market oracle (zero-address oracle market)")

    position = None
    user = data.get("user_address") or data.get("wallet")
    if _valid_address(user):
        try:
            ucall = rpc_call(contract, "position(bytes32,address)", encoded_id, _encode_address(str(user)))
            uw = _words(ucall.result, 3)
            position = {"user": str(user).lower(), "supply_shares": _word_uint(uw[0]), "borrow_shares": _word_uint(uw[1]), "collateral_raw": _word_uint(uw[2])}
            if state["total_borrow_shares_raw"]:
                position["borrow_assets_estimated_raw"] = position["borrow_shares"] * state["total_borrow_assets_raw"] / state["total_borrow_shares_raw"]
            else:
                position["borrow_assets_estimated_raw"] = 0.0
            if price and position["borrow_assets_estimated_raw"]:
                collateral_value = position["collateral_raw"] * price["price_raw"] / MORPHO_ORACLE_SCALE
                borrowed = float(position["borrow_assets_estimated_raw"])
                position["ltv"] = borrowed / collateral_value if collateral_value else None
                position["health_factor"] = (collateral_value * params["lltv"] / borrowed) if borrowed else None
                if position["health_factor"] is not None:
                    if position["health_factor"] <= 1:
                        out.risk_delta += 50; out.warnings.append("Morpho position is at/beyond the market LLTV liquidation boundary.")
                    elif position["health_factor"] < 1.05:
                        out.risk_delta += 28
                    elif position["health_factor"] < 1.2:
                        out.risk_delta += 15
            out.evidence.append(_evidence(ucall, protocol="morpho_blue", source_type="protocol_native_position", normalized=position, chain_id=chain_id, block=block_number))
        except (ProviderError, ValueError) as exc:
            out.missing_data.append("Morpho user position state")
            out.warnings.append(f"Morpho user position state could not be read: {exc}")

    oracle_composition = None
    identity = data.get("_rivexis_deployment_identity") or {}
    if price and identity.get("status") == "VERIFIED":
        composition_specs = {
            "base_vault": ("BASE_VAULT()", "address"),
            "base_vault_conversion_sample": ("BASE_VAULT_CONVERSION_SAMPLE()", "uint"),
            "base_feed_1": ("BASE_FEED_1()", "address"), "base_feed_2": ("BASE_FEED_2()", "address"),
            "quote_vault": ("QUOTE_VAULT()", "address"),
            "quote_vault_conversion_sample": ("QUOTE_VAULT_CONVERSION_SAMPLE()", "uint"),
            "quote_feed_1": ("QUOTE_FEED_1()", "address"), "quote_feed_2": ("QUOTE_FEED_2()", "address"),
            "scale_factor": ("SCALE_FACTOR()", "uint"),
        }
        observed: dict[str, Any] = {}
        successful = 0
        for key, (signature, kind) in composition_specs.items():
            try:
                c = rpc_call(params["oracle"], signature)
                word = _words(c.result, 1)[0]
                value = _word_address(word) if kind == "address" else _word_uint(word)
                observed[key] = value; successful += 1
                out.evidence.append(_evidence(c, protocol="morpho_blue", source_type="protocol_native_oracle_composition", normalized={key: value}, chain_id=chain_id, block=block_number))
            except (ProviderError, ValueError):
                observed[key] = None
        if successful:
            oracle_composition = observed
            oracle_composition["recognized_morpho_chainlink_oracle_v2_surface"] = successful >= 5
        else:
            out.warnings.append("Morpho oracle does not expose the inspected Morpho ChainlinkOracleV2 composition surface; it may use a different/custom oracle implementation.")

        if oracle_composition and oracle_composition.get("recognized_morpho_chainlink_oracle_v2_surface"):
            feed_health: dict[str, Any] = {}
            block_timestamp = None
            try:
                tag = block_tag if block_tag != "latest" else (hex(block_number) if block_number is not None else "latest")
                bcall = rpc.call("eth_getBlockByNumber", [tag, False])
                if isinstance(bcall.result, dict):
                    block_timestamp = hex_to_int(bcall.result.get("timestamp"))
            except (ProviderError, ValueError):
                block_timestamp = None
            stale_seconds = max(60, int(os.getenv("RIVEXIS_MORPHO_FEED_STALE_SECONDS", "3600")))
            for key in ("base_feed_1", "base_feed_2", "quote_feed_1", "quote_feed_2"):
                feed = oracle_composition.get(key)
                if not _valid_address(feed) or int(feed, 16) == 0:
                    continue
                info: dict[str, Any] = {"address": feed}
                try:
                    dcall = rpc_call(feed, "decimals()")
                    info["decimals"] = _word_uint(_words(dcall.result, 1)[0])
                    out.evidence.append(_evidence(dcall, protocol="morpho_blue", source_type="protocol_native_oracle_feed_metadata", normalized={key: info.copy()}, chain_id=chain_id, block=block_number))
                    rcall = rpc_call(feed, "latestRoundData()")
                    rw = _words(rcall.result, 5)
                    answer = _word_int256(rw[1]); updated_at = _word_uint(rw[3])
                    info.update({"answer_raw": answer, "updated_at": updated_at, "answered_in_round": _word_uint(rw[4])})
                    if block_timestamp is not None and updated_at:
                        info["age_seconds_at_block"] = max(0, block_timestamp - updated_at)
                        info["stale"] = info["age_seconds_at_block"] > stale_seconds
                    if answer <= 0:
                        out.risk_delta += 20; out.warnings.append(f"Morpho oracle dependency {key} returned a non-positive answer.")
                    if info.get("stale"):
                        out.risk_delta += 12; out.warnings.append(f"Morpho oracle dependency {key} is stale at the inspected block under the configured threshold.")
                    out.evidence.append(_evidence(rcall, protocol="morpho_blue", source_type="protocol_native_oracle_feed_state", normalized={key: info.copy()}, chain_id=chain_id, block=block_number))
                except (ProviderError, ValueError) as exc:
                    info["error"] = str(exc)
                    out.missing_data.append(f"Morpho oracle dependency {key} live round state")
                feed_health[key] = info
            oracle_composition["feed_health"] = feed_health

    identity = data.get("_rivexis_deployment_identity") or {}
    expected_irm = str(data.get("morpho_adaptive_curve_irm") or "").lower()
    irm_classification = "official_adaptive_curve" if expected_irm and params["irm"].lower() == expected_irm else ("zero_oracleless" if int(params["irm"], 16) == 0 else "custom_or_other")

    dependency_provenance: dict[str, Any] = {"irm_enabled_by_morpho": None, "oracle_created_by_official_factory": None, "adaptive_curve_rate_at_target_raw": None, "oracle_runtime_code": None, "irm_runtime_code": None, "irm_morpho_binding": None, "borrow_rate_per_second_wad": None, "borrow_rate_apr_percent": None}
    # Runtime code fingerprints make dependency changes externally comparable without
    # claiming that a SHA-256 fingerprint is an Ethereum identity primitive.
    for dependency_name, dependency_address in (("oracle_runtime_code", params["oracle"]), ("irm_runtime_code", params["irm"])):
        if int(dependency_address, 16) == 0:
            continue
        try:
            code_call, code_meta = _runtime_code_fingerprint(rpc, dependency_address, block_tag)
            dependency_provenance[dependency_name] = code_meta
            out.evidence.append(_evidence(code_call, protocol="morpho_blue", source_type="protocol_native_runtime_code_fingerprint", normalized={dependency_name: code_meta}, chain_id=chain_id, block=block_number))
            if not code_meta["code_present"]:
                out.risk_delta += 35
                out.warnings.append(f"Morpho dependency {dependency_address} has no runtime bytecode at the inspected block.")
        except (ProviderError, ValueError) as exc:
            out.missing_data.append(f"Morpho {dependency_name.replace('_', ' ')}")
            out.warnings.append(f"Morpho dependency runtime code could not be fingerprinted: {exc}")

    if int(params["irm"], 16) != 0:
        try:
            c = rpc_call(contract, "isIrmEnabled(address)", _encode_address(params["irm"]))
            dependency_provenance["irm_enabled_by_morpho"] = _word_bool(_words(c.result, 1)[0])
            out.evidence.append(_evidence(c, protocol="morpho_blue", source_type="protocol_native_irm_provenance", normalized={"irm": params["irm"], "enabled_by_morpho": dependency_provenance["irm_enabled_by_morpho"]}, chain_id=chain_id, block=block_number))
            if dependency_provenance["irm_enabled_by_morpho"] is False:
                out.risk_delta += 30; out.warnings.append("Morpho core reports the market IRM is not enabled.")
        except (ProviderError, ValueError) as exc:
            out.missing_data.append("Morpho IRM enablement provenance")
            out.warnings.append(f"Morpho IRM enablement could not be verified: {exc}")

    factory = str(data.get("morpho_oracle_factory") or "")
    if price and _valid_address(factory):
        try:
            c = rpc_call(factory, "isMorphoChainlinkOracleV2(address)", _encode_address(params["oracle"]))
            dependency_provenance["oracle_created_by_official_factory"] = _word_bool(_words(c.result, 1)[0])
            out.evidence.append(_evidence(c, protocol="morpho_blue", source_type="protocol_native_oracle_factory_provenance", normalized={"oracle": params["oracle"], "factory": factory.lower(), "created_by_factory": dependency_provenance["oracle_created_by_official_factory"]}, chain_id=chain_id, block=block_number))
            if oracle_composition and oracle_composition.get("recognized_morpho_chainlink_oracle_v2_surface") and dependency_provenance["oracle_created_by_official_factory"] is False:
                out.risk_delta += 8; out.warnings.append("Oracle exposes the inspected ChainlinkOracleV2 surface but the official factory does not recognize it as factory-created.")
        except (ProviderError, ValueError) as exc:
            out.missing_data.append("Morpho oracle factory provenance")
            out.warnings.append(f"Morpho oracle factory provenance could not be verified: {exc}")

    if irm_classification == "official_adaptive_curve":
        try:
            c = rpc_call(params["irm"], "rateAtTarget(bytes32)", encoded_id)
            raw = _word_uint(_words(c.result, 1)[0])
            if raw >= 2**255: raw -= 2**256
            dependency_provenance["adaptive_curve_rate_at_target_raw"] = raw
            out.evidence.append(_evidence(c, protocol="morpho_blue", source_type="protocol_native_irm_state", normalized={"market_id": market_id.lower(), "irm": params["irm"], "rate_at_target_raw_signed": raw}, chain_id=chain_id, block=block_number))
        except (ProviderError, ValueError) as exc:
            out.missing_data.append("Morpho Adaptive Curve rateAtTarget state")
            out.warnings.append(f"Morpho Adaptive Curve rateAtTarget could not be read: {exc}")

        try:
            c = rpc_call(params["irm"], "MORPHO()")
            bound = _word_address(_words(c.result, 1)[0])
            dependency_provenance["irm_morpho_binding"] = {"reported_morpho": bound, "expected_morpho": contract.lower(), "matches": bound == contract.lower()}
            out.evidence.append(_evidence(c, protocol="morpho_blue", source_type="protocol_native_irm_binding", normalized=dependency_provenance["irm_morpho_binding"], chain_id=chain_id, block=block_number))
            if bound != contract.lower():
                out.risk_delta += 25
                out.warnings.append("Official Adaptive Curve IRM candidate reports a MORPHO binding different from the inspected Morpho core.")
        except (ProviderError, ValueError) as exc:
            out.missing_data.append("Morpho Adaptive Curve MORPHO binding")
            out.warnings.append(f"Morpho Adaptive Curve MORPHO binding could not be read: {exc}")

        try:
            signature = "borrowRateView((address,address,address,address,uint256),(uint128,uint128,uint128,uint128,uint128,uint128))"
            c = rpc_call(
                params["irm"], signature,
                _encode_address(params["loan_token"]), _encode_address(params["collateral_token"]),
                _encode_address(params["oracle"]), _encode_address(params["irm"]), _encode_uint(int(params["lltv_wad"])),
                _encode_uint(int(state["total_supply_assets_raw"])), _encode_uint(int(state["total_supply_shares_raw"])),
                _encode_uint(int(state["total_borrow_assets_raw"])), _encode_uint(int(state["total_borrow_shares_raw"])),
                _encode_uint(int(state["last_update"])), _encode_uint(int(state["fee_wad"])),
            )
            borrow_rate = _word_uint(_words(c.result, 1)[0])
            apr = (borrow_rate * 365 * 24 * 60 * 60 / WAD) * 100
            dependency_provenance["borrow_rate_per_second_wad"] = borrow_rate
            dependency_provenance["borrow_rate_apr_percent"] = apr
            dependency_provenance["target_utilization"] = 0.9
            dependency_provenance["utilization_error_vs_target"] = (state.get("utilization") - 0.9) if state.get("utilization") is not None else None
            rate_target = dependency_provenance.get("adaptive_curve_rate_at_target_raw")
            if isinstance(rate_target, int):
                dependency_provenance["rate_at_target_apr_percent"] = (rate_target * 365 * 24 * 60 * 60 / WAD) * 100
            out.evidence.append(_evidence(c, protocol="morpho_blue", source_type="protocol_native_irm_economics", normalized={
                "market_id": market_id.lower(), "borrow_rate_per_second_wad": borrow_rate, "simple_annualized_borrow_rate_percent": apr,
                "utilization": state.get("utilization"), "documented_target_utilization": 0.9,
            }, chain_id=chain_id, block=block_number))
            if apr > 200:
                out.risk_delta += 12
                out.warnings.append("Morpho Adaptive Curve simple annualized borrow rate exceeds 200% at the inspected state.")
        except (ProviderError, ValueError) as exc:
            out.missing_data.append("Morpho Adaptive Curve borrowRateView economics")
            out.warnings.append(f"Morpho Adaptive Curve borrowRateView could not be read: {exc}")

    util = state.get("utilization")
    if util is not None and util > 0.98:
        out.risk_delta += 12; out.warnings.append("Morpho market utilization exceeds 98%, indicating a thin immediate liquidity buffer.")
    if params["lltv"] >= 0.965:
        out.risk_delta += 8; out.warnings.append("Morpho market LLTV is at or above 96.5%; liquidation buffer is structurally narrow.")

    out.metrics = {"adapter": "morpho_blue", "morpho_contract": contract.lower(), "market_params": params, "market_state": state, "oracle": price, "oracle_composition": oracle_composition, "irm_classification": irm_classification, "dependency_provenance": dependency_provenance, "position": position}
    out.assumptions.append("Morpho market parameters are immutable market identity inputs; oracle and IRM security still require implementation-level dependency review.")
    out.missing_data.append("official deployment identity allowlist verification")
    out.confidence = 99 if price is not None else 92
    out.risk_delta = min(70.0, out.risk_delta)
    return out


def protocol_adapter_capabilities() -> list[dict[str, Any]]:
    return [
        {
            "adapter": "aave_v3",
            "required": ["chain", "asset_address"],
            "conditional": ["aave_data_provider required when no unique official deployment registry record exists"],
            "registry_autofill": ["aave_data_provider", "aave_pool", "aave_oracle", "aave_addresses_provider"],
            "optional_position": ["aave_pool", "user_address"],
            "reads": ["reserve_configuration", "borrow_supply_caps", "debt_ceiling", "paused", "siloed_borrowing", "liquidation_protocol_fee", "emode_category", "interest_rate_strategy", "asset_oracle_source", "user_account_data"],
            "authority": "direct_onchain_state",
            "historical_read": {"input": "at_block", "requires": "archive-capable RPC for historical blocks"},
        },
        {
            "adapter": "compound_v3",
            "required": ["chain", "collateral_asset"],
            "conditional": ["comet_address or compound_market required when no unique official deployment registry record exists"],
            "registry_autofill": ["comet_address", "compound_configurator"],
            "optional_position": ["user_address"],
            "reads": ["asset_info", "protocol_price", "governor", "pause_guardian", "base_token", "base_token_price_feed", "pause_state", "utilization", "is_liquidatable", "is_borrow_collateralized", "borrow_balance", "collateral_balance"],
            "authority": "direct_onchain_state",
            "historical_read": {"input": "at_block", "requires": "archive-capable RPC for historical blocks"},
        },
        {
            "adapter": "morpho_blue",
            "required": ["chain", "morpho_market_id"],
            "conditional": ["morpho_contract required when the selected chain has no official registry record"],
            "registry_autofill": ["morpho_contract", "morpho_adaptive_curve_irm", "morpho_oracle_factory"],
            "optional_position": ["user_address"],
            "reads": ["immutable_market_params", "market_state", "oracle_price", "oracle_composition_if_supported", "official_oracle_factory_provenance", "irm_enablement", "adaptive_curve_rate_at_target_if_official", "user_position", "derived_health_factor"],
            "authority": "direct_onchain_state",
            "historical_read": {"input": "at_block", "requires": "archive-capable RPC for historical blocks"},
        },
    ]
