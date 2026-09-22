from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from rivexis_api.chains import normalize_chain
from rivexis_api.provider_clients import ProviderError, hex_to_int
from rivexis_api.providers import select_rpc_client
from rivexis_api.services.deployment_registry import enrich_protocol_adapter_input, canonical_adapter
from rivexis_api.services.evm_decode import keccak256
from rivexis_api.services.protocol_adapters import collect_protocol_adapter


def event_topic(signature: str) -> str:
    return "0x" + keccak256(signature.encode()).hex()


def _uint(word: str) -> int:
    return int(word, 16)


def _address(word: str) -> str:
    return "0x" + word[-40:].lower()


def _bool(word: str) -> bool:
    return bool(_uint(word))


def _words(raw: str) -> list[str]:
    clean = (raw or "0x")[2:]
    if len(clean) % 64:
        return []
    return [clean[i:i + 64] for i in range(0, len(clean), 64)]


def _topic_word(topic: str) -> str:
    return topic[2:].rjust(64, "0")


@dataclass(frozen=True)
class EventSpec:
    name: str
    signature: str
    indexed: tuple[tuple[str, str], ...]
    data: tuple[tuple[str, str], ...]
    category: str = "configuration"

    @property
    def topic0(self) -> str:
        return event_topic(self.signature)


def _decode(kind: str, word: str) -> Any:
    if kind == "address": return _address(word)
    if kind == "bool": return _bool(word)
    if kind in {"uint", "uint8", "uint40", "uint64", "uint104", "uint128", "uint256"}: return _uint(word)
    if kind == "bytes32": return "0x" + word.lower()
    return "0x" + word.lower()


AAVE_EVENTS = (
    EventSpec("ReserveBorrowing", "ReserveBorrowing(address,bool)", (("asset","address"),), (("enabled","bool"),)),
    EventSpec("CollateralConfigurationChanged", "CollateralConfigurationChanged(address,uint256,uint256,uint256)", (("asset","address"),), (("ltv","uint256"),("liquidation_threshold","uint256"),("liquidation_bonus","uint256"))),
    EventSpec("ReserveActive", "ReserveActive(address,bool)", (("asset","address"),), (("active","bool"),)),
    EventSpec("ReserveFrozen", "ReserveFrozen(address,bool)", (("asset","address"),), (("frozen","bool"),)),
    EventSpec("ReservePaused", "ReservePaused(address,bool)", (("asset","address"),), (("paused","bool"),)),
    EventSpec("ReserveFactorChanged", "ReserveFactorChanged(address,uint256,uint256)", (("asset","address"),), (("old_reserve_factor","uint256"),("new_reserve_factor","uint256"))),
    EventSpec("BorrowCapChanged", "BorrowCapChanged(address,uint256,uint256)", (("asset","address"),), (("old_borrow_cap","uint256"),("new_borrow_cap","uint256"))),
    EventSpec("SupplyCapChanged", "SupplyCapChanged(address,uint256,uint256)", (("asset","address"),), (("old_supply_cap","uint256"),("new_supply_cap","uint256"))),
    EventSpec("LiquidationProtocolFeeChanged", "LiquidationProtocolFeeChanged(address,uint256,uint256)", (("asset","address"),), (("old_fee_bps","uint256"),("new_fee_bps","uint256"))),
    EventSpec("LiquidationGracePeriodChanged", "LiquidationGracePeriodChanged(address,uint40)", (("asset","address"),), (("grace_period_until","uint40"),)),
    EventSpec("ReserveInterestRateStrategyChanged", "ReserveInterestRateStrategyChanged(address,address,address)", (("asset","address"),), (("old_strategy","address"),("new_strategy","address"))),
)

COMPOUND_CONFIG_EVENTS = (
    EventSpec("SetGovernor", "SetGovernor(address,address,address)", (("comet","address"),("old_governor","address"),("new_governor","address")), ()),
    EventSpec("SetPauseGuardian", "SetPauseGuardian(address,address,address)", (("comet","address"),("old_pause_guardian","address"),("new_pause_guardian","address")), ()),
    EventSpec("SetBaseTokenPriceFeed", "SetBaseTokenPriceFeed(address,address,address)", (("comet","address"),("old_feed","address"),("new_feed","address")), ()),
    EventSpec("SetSupplyKink", "SetSupplyKink(address,uint64,uint64)", (("comet","address"),), (("old_supply_kink","uint64"),("new_supply_kink","uint64"))),
    EventSpec("SetBorrowKink", "SetBorrowKink(address,uint64,uint64)", (("comet","address"),), (("old_borrow_kink","uint64"),("new_borrow_kink","uint64"))),
    EventSpec("SetTargetReserves", "SetTargetReserves(address,uint104,uint104)", (("comet","address"),), (("old_target_reserves","uint104"),("new_target_reserves","uint104"))),
    EventSpec("UpdateAssetPriceFeed", "UpdateAssetPriceFeed(address,address,address,address)", (("comet","address"),("asset","address")), (("old_price_feed","address"),("new_price_feed","address"))),
    EventSpec("UpdateAssetBorrowCollateralFactor", "UpdateAssetBorrowCollateralFactor(address,address,uint64,uint64)", (("comet","address"),("asset","address")), (("old_borrow_cf","uint64"),("new_borrow_cf","uint64"))),
    EventSpec("UpdateAssetLiquidateCollateralFactor", "UpdateAssetLiquidateCollateralFactor(address,address,uint64,uint64)", (("comet","address"),("asset","address")), (("old_liquidate_cf","uint64"),("new_liquidate_cf","uint64"))),
    EventSpec("UpdateAssetLiquidationFactor", "UpdateAssetLiquidationFactor(address,address,uint64,uint64)", (("comet","address"),("asset","address")), (("old_liquidation_factor","uint64"),("new_liquidation_factor","uint64"))),
    EventSpec("UpdateAssetSupplyCap", "UpdateAssetSupplyCap(address,address,uint128,uint128)", (("comet","address"),("asset","address")), (("old_supply_cap","uint128"),("new_supply_cap","uint128"))),
)
COMPOUND_COMET_EVENTS = (
    EventSpec("PauseAction", "PauseAction(bool,bool,bool,bool,bool)", (), (("supply_paused","bool"),("transfer_paused","bool"),("withdraw_paused","bool"),("absorb_paused","bool"),("buy_paused","bool")), "operations"),
)
MORPHO_CORE_EVENTS = (
    EventSpec("SetOwner", "SetOwner(address)", (("new_owner","address"),), (), "governance"),
    EventSpec("SetFee", "SetFee(bytes32,uint256)", (("market_id","bytes32"),), (("new_fee","uint256"),)),
    EventSpec("EnableIrm", "EnableIrm(address)", (("irm","address"),), (), "governance"),
    EventSpec("EnableLltv", "EnableLltv(uint256)", (), (("lltv","uint256"),), "governance"),
    EventSpec("CreateMarket", "CreateMarket(bytes32,(address,address,address,address,uint256))", (("market_id","bytes32"),), (("loan_token","address"),("collateral_token","address"),("oracle","address"),("irm","address"),("lltv","uint256")), "configuration"),
)
MORPHO_ORACLE_FACTORY_EVENTS = (
    EventSpec("CreateMorphoChainlinkOracleV2", "CreateMorphoChainlinkOracleV2(address,address)", (), (("caller","address"),("oracle","address")), "dependency"),
)


def _normalize_log(log: dict[str, Any], specs: dict[str, EventSpec], *, source_role: str) -> dict[str, Any] | None:
    topics = [str(t).lower() for t in (log.get("topics") or [])]
    if not topics: return None
    spec = specs.get(topics[0])
    if not spec: return None
    params: dict[str, Any] = {}
    for i, (name, kind) in enumerate(spec.indexed, 1):
        if len(topics) <= i: return None
        params[name] = _decode(kind, _topic_word(topics[i]))
    words = _words(str(log.get("data") or "0x"))
    if len(words) < len(spec.data): return None
    for i, (name, kind) in enumerate(spec.data):
        params[name] = _decode(kind, words[i])
    return {
        "event": spec.name, "category": spec.category, "source_role": source_role,
        "address": str(log.get("address") or "").lower(), "parameters": params,
        "block_number": hex_to_int(log.get("blockNumber")), "transaction_hash": log.get("transactionHash"),
        "log_index": hex_to_int(log.get("logIndex")), "topic0": topics[0], "removed": bool(log.get("removed", False)),
    }


def _chunk_size(data: dict[str, Any]) -> int:
    configured = int(data.get("log_chunk_blocks") or os.getenv("RIVEXIS_PROTOCOL_HISTORY_CHUNK_BLOCKS", "5000"))
    return max(1, min(configured, 50000))


def _get_logs(
    rpc, address: str, specs: tuple[EventSpec, ...], from_block: int, to_block: int,
    source_role: str, *, chunk_blocks: int = 5000, include_removed: bool = False,
) -> tuple[list[dict[str, Any]], list[str], dict[str, Any]]:
    """Fetch logs in bounded chunks, shrinking a failing retryable chunk instead of
    converting provider range limits into an empty history result."""
    topic_map = {spec.topic0.lower(): spec for spec in specs}
    request_ids: list[str] = []
    out: list[dict[str, Any]] = []
    removed_count = 0
    chunk_count = 0
    adaptive_reductions = 0
    minimum = max(1, min(int(chunk_blocks), int(os.getenv("RIVEXIS_PROTOCOL_HISTORY_MIN_CHUNK_BLOCKS", "25"))))
    cursor = from_block
    current_chunk = max(minimum, int(chunk_blocks))
    while cursor <= to_block:
        end = min(to_block, cursor + current_chunk - 1)
        filt = {
            "address": address, "fromBlock": hex(cursor), "toBlock": hex(end),
            "topics": [[spec.topic0 for spec in specs]],
        }
        try:
            call = rpc.call("eth_getLogs", [filt])
        except ProviderError as exc:
            if exc.retryable and current_chunk > minimum:
                current_chunk = max(minimum, current_chunk // 2)
                adaptive_reductions += 1
                continue
            raise
        request_ids.append(call.request_id)
        chunk_count += 1
        rows = call.result if isinstance(call.result, list) else []
        for row in rows:
            if not isinstance(row, dict):
                continue
            normalized = _normalize_log(row, topic_map, source_role=source_role)
            if not normalized:
                continue
            if normalized.get("removed"):
                removed_count += 1
                if not include_removed:
                    continue
            out.append(normalized)
        cursor = end + 1
        # After an adaptive reduction, grow conservatively once the smaller range works.
        if current_chunk < chunk_blocks:
            current_chunk = min(chunk_blocks, max(current_chunk + 1, current_chunk * 2))
    # Protect against provider overlap/replay at chunk boundaries.
    unique: dict[tuple[Any, ...], dict[str, Any]] = {}
    for row in out:
        key = (row.get("transaction_hash"), row.get("log_index"), row.get("address"), row.get("topic0"))
        unique[key] = row
    return list(unique.values()), request_ids, {
        "chunk_count": chunk_count, "adaptive_reductions": adaptive_reductions,
        "removed_log_count": removed_count, "requested_chunk_blocks": chunk_blocks,
    }


def _hydrate_timestamps(rpc, events: list[dict[str, Any]], *, max_blocks: int) -> tuple[list[str], int]:
    blocks = sorted({int(event["block_number"]) for event in events if event.get("block_number") is not None})
    if len(blocks) > max_blocks:
        return [], len(blocks) - max_blocks
    request_ids: list[str] = []
    timestamps: dict[int, tuple[int, str]] = {}
    for block_number in blocks:
        call = rpc.call("eth_getBlockByNumber", [hex(block_number), False])
        request_ids.append(call.request_id)
        block = call.result if isinstance(call.result, dict) else {}
        raw = block.get("timestamp")
        if raw is None:
            continue
        ts = int(raw, 16) if isinstance(raw, str) and raw.startswith("0x") else int(raw)
        timestamps[block_number] = (ts, datetime.fromtimestamp(ts, tz=timezone.utc).isoformat())
    for event in events:
        block_number = event.get("block_number")
        if block_number in timestamps:
            event["block_timestamp"] = timestamps[block_number][0]
            event["block_datetime"] = timestamps[block_number][1]
    return request_ids, 0


def _bounds(data: dict[str, Any], chain_head: int) -> tuple[int, int]:
    if data.get("from_block") is None or data.get("to_block") is None:
        raise ValueError("from_block and to_block are required")
    def parse(v: Any) -> int:
        return int(v, 16) if isinstance(v, str) and v.lower().startswith("0x") else int(v)
    start, end = parse(data["from_block"]), parse(data["to_block"])
    if start < 0 or end < start or end > chain_head:
        raise ValueError("Invalid protocol history block range")
    max_range = int(os.getenv("RIVEXIS_PROTOCOL_HISTORY_MAX_BLOCKS", "50000"))
    if end - start > max_range:
        raise ValueError(f"Protocol history range exceeds configured maximum of {max_range} blocks")
    return start, end


def protocol_event_timeline(data: dict[str, Any]) -> dict[str, Any]:
    chain = normalize_chain(data.get("chain") or data.get("chain_id"))
    provider_id, rpc, probe, failures = select_rpc_client(chain.key)
    head_call = rpc.call("eth_blockNumber")
    head = int(head_call.result, 16)
    start, end = _bounds(data, head)
    enriched, identity = enrich_protocol_adapter_input(data, chain.chain_id)
    adapter = canonical_adapter(enriched.get("protocol_adapter") or enriched.get("protocol_type"))
    events: list[dict[str, Any]] = []
    request_ids: list[str] = []
    targets: list[tuple[str, tuple[EventSpec, ...], str]] = []
    verified = identity.get("status") == "VERIFIED"
    c = identity.get("contracts") or {}
    if adapter == "aave_v3":
        target = data.get("aave_pool_configurator") or (c.get("pool_configurator") if verified else None)
        if not target: raise ValueError("Aave history requires verified registry configurator or explicit aave_pool_configurator")
        targets.append((str(target), AAVE_EVENTS, "pool_configurator"))
    elif adapter == "compound_v3":
        configurator = data.get("compound_configurator") or (c.get("configurator") if verified else None)
        comet = data.get("comet_address") or data.get("market_address") or (c.get("comet") if verified else None)
        if not configurator or not comet: raise ValueError("Compound history requires configurator and comet (verified registry or explicit addresses)")
        targets.extend([(str(configurator), COMPOUND_CONFIG_EVENTS, "configurator"), (str(comet), COMPOUND_COMET_EVENTS, "comet")])
    elif adapter == "morpho_blue":
        morpho = data.get("morpho_contract") or (c.get("morpho") if verified else None)
        factory = data.get("morpho_oracle_factory") or (c.get("chainlink_oracle_v2_factory") if verified else None)
        if not morpho: raise ValueError("Morpho history requires verified registry core or explicit morpho_contract")
        targets.append((str(morpho), MORPHO_CORE_EVENTS, "morpho_core"))
        if factory: targets.append((str(factory), MORPHO_ORACLE_FACTORY_EVENTS, "oracle_factory"))
    else:
        raise ValueError("Unsupported protocol adapter for history")
    chunk_meta: list[dict[str, Any]] = []
    include_removed = bool(data.get("include_removed", False))
    chunk_blocks = _chunk_size(data)
    for address, specs, role in targets:
        rows, ids, meta = _get_logs(
            rpc, address, specs, start, end, role,
            chunk_blocks=chunk_blocks, include_removed=include_removed,
        )
        events.extend(rows); request_ids.extend(ids)
        chunk_meta.append({"address": address.lower(), "source_role": role, **meta})
    asset_filter = str(data.get("asset_address") or data.get("collateral_asset") or "").lower()
    market_filter = str(data.get("morpho_market_id") or data.get("market_id") or "").lower()
    if asset_filter:
        events = [e for e in events if not e["parameters"].get("asset") or str(e["parameters"].get("asset")).lower() == asset_filter]
    if market_filter and adapter == "morpho_blue":
        events = [e for e in events if not e["parameters"].get("market_id") or str(e["parameters"].get("market_id")).lower() == market_filter]
    timestamp_request_ids: list[str] = []
    timestamp_skipped_blocks = 0
    if bool(data.get("hydrate_timestamps", False)) and events:
        max_blocks = max(1, int(data.get("timestamp_hydration_max_blocks") or os.getenv("RIVEXIS_PROTOCOL_HISTORY_TIMESTAMP_MAX_BLOCKS", "250")))
        timestamp_request_ids, timestamp_skipped_blocks = _hydrate_timestamps(rpc, events, max_blocks=max_blocks)
        request_ids.extend(timestamp_request_ids)
    events.sort(key=lambda e: (e.get("block_number") or 0, e.get("log_index") or 0))
    return {
        "adapter": adapter, "chain": chain.key, "chain_id": chain.chain_id, "provider": provider_id,
        "from_block": start, "to_block": end, "chain_head": head, "deployment_identity": identity,
        "events": events, "event_count": len(events), "provider_request_ids": request_ids,
        "log_fetch": {
            "chunk_blocks": chunk_blocks, "targets": chunk_meta,
            "include_removed": include_removed,
            "timestamp_hydration": bool(data.get("hydrate_timestamps", False)),
            "timestamp_request_count": len(timestamp_request_ids),
            "timestamp_skipped_blocks": timestamp_skipped_blocks,
        },
        "provider_failures_before_selection": failures,
        "limitations": [
            "Timeline contains only Rivexis-normalized protocol events in the supported event catalog; absence of an event is not proof that no governance/configuration action occurred.",
            "Removed logs are excluded by default; set include_removed=true only for reorg investigation workflows.",
        ],
    }


def _flatten(value: Any, prefix: str = "") -> dict[str, Any]:
    out: dict[str, Any] = {}
    if isinstance(value, dict):
        for key, item in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            out.update(_flatten(item, path))
    elif isinstance(value, list):
        out[prefix] = value
    else:
        out[prefix] = value
    return out


def _materiality(path: str) -> str:
    p = path.lower()
    high = ("liquidat", "oracle", "price_feed", "governor", "pause_guardian", "paused", "lltv", "borrow_collateral_factor", "liquidate_collateral_factor", "implementation")
    medium = ("ltv", "cap", "reserve_factor", "interest_rate", "irm", "kink", "fee", "target_reserves", "supply_factor")
    if any(x in p for x in high): return "HIGH"
    if any(x in p for x in medium): return "MEDIUM"
    return "LOW"


def compare_protocol_configuration(data: dict[str, Any]) -> dict[str, Any]:
    chain = normalize_chain(data.get("chain") or data.get("chain_id"))
    provider_id, rpc, probe, failures = select_rpc_client(chain.key)
    head_call = rpc.call("eth_blockNumber"); head = int(head_call.result, 16)
    start, end = _bounds(data, head)
    if start == end: raise ValueError("Configuration comparison requires two different blocks")
    base = dict(data); base["at_block"] = start
    target = dict(data); target["at_block"] = end
    before = collect_protocol_adapter(base, rpc=rpc, chain_id=chain.chain_id, block_number=head)
    after = collect_protocol_adapter(target, rpc=rpc, chain_id=chain.chain_id, block_number=head)
    a = _flatten(before.metrics); b = _flatten(after.metrics)
    ignored_suffixes = {"read_block_number", "block_tag", "deployment_identity.verified_on"}
    changes = []
    for path in sorted(set(a) | set(b)):
        if path in ignored_suffixes: continue
        if a.get(path) != b.get(path):
            changes.append({"path": path, "from": a.get(path), "to": b.get(path), "materiality": _materiality(path)})
    counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for row in changes: counts[row["materiality"]] += 1
    return {
        "adapter": canonical_adapter(data.get("protocol_adapter") or data.get("protocol_type")),
        "chain": chain.key, "chain_id": chain.chain_id, "provider": provider_id,
        "from_block": start, "to_block": end, "chain_head": head,
        "before": before.metrics, "after": after.metrics, "changes": changes,
        "change_count": len(changes), "materiality_counts": counts,
        "warnings": sorted(set(before.warnings + after.warnings)),
        "missing_data": sorted(set(before.missing_data + after.missing_data)),
        "provider_failures_before_selection": failures,
        "limitations": ["Materiality is a Rivexis deterministic review priority, not a claim that a parameter change was malicious or unsafe.", "Historical reads require archive-capable RPC state."],
    }
