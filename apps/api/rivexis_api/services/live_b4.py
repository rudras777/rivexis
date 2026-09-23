from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from uuid import uuid4

from rivexis_api.chains import normalize_chain
from rivexis_api.models.engine import EngineResult
from rivexis_api.models.enums import AnalysisStatus, EngineId, FreshnessStatus, Severity
from rivexis_api.models.evidence import EvidenceRecord, SourceConflict
from rivexis_api.provider_clients import (
    ArkhamClient,
    EtherscanClient,
    NansenClient,
    ProviderError,
    hex_to_int,
)
from rivexis_api.providers import select_rpc_client

UINT256_MAX = 2**256 - 1


def _address(value: object) -> str | None:
    s = str(value or "").strip().lower()
    if len(s) != 42 or not s.startswith("0x"):
        return None
    try:
        int(s[2:], 16)
    except ValueError:
        return None
    return s


def _uint_decimal(value: object, *, maximum: int = UINT256_MAX) -> int | None:
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


def _rpc_uint(value: object) -> int | None:
    try:
        parsed = hex_to_int(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return parsed if parsed is not None and 0 <= parsed <= UINT256_MAX else None


def _parse_limit(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    if parsed < 1:
        return None
    return min(parsed, 250)


def _result_list(call) -> list[dict]:
    if not isinstance(call.result, dict):
        raise ProviderError(
            "Etherscan history response must be an object",
            provider_id="etherscan",
            code="MALFORMED_RESPONSE",
        )
    rows = call.result.get("result")
    if not isinstance(rows, list):
        raise ProviderError(
            "Etherscan history result must be a list",
            provider_id="etherscan",
            code="MALFORMED_RESPONSE",
        )
    return [row for row in rows if isinstance(row, dict)]


def _provider_evidence(
    call,
    *,
    provider: str,
    normalized_value: dict,
    chain_id: int,
    block_number: int | None,
    wallet: str,
    confidence: float,
) -> EvidenceRecord:
    retrieved = datetime.now(timezone.utc)
    return EvidenceRecord(
        evidence_id=str(uuid4()),
        provider=provider,
        source_type="entity_label_intelligence",
        provider_endpoint=call.endpoint,
        provider_request_id=call.request_id,
        retrieved_at=retrieved,
        # No normalized provider observation timestamp is available for these label
        # responses. Keep the schema-required datetime as a retrieval fallback only;
        # freshness remains UNKNOWN so it is not presented as provider-observed now.
        observed_at=retrieved,
        block_number=block_number,
        chain_id=chain_id,
        raw_reference=f"provider:{provider};request:{call.request_id};address:{wallet}",
        normalized_value=normalized_value,
        confidence=confidence,
        freshness=FreshnessStatus.UNKNOWN,
        license_classification="external-provider-attributed",
    )


def _nansen_normalize(body: object) -> dict:
    if not isinstance(body, dict):
        return {"labels": [], "identity_candidates": []}
    rows = body.get("data")
    if isinstance(rows, dict):
        rows = rows.get("data") or rows.get("labels") or []
    if not isinstance(rows, list):
        rows = body.get("labels") if isinstance(body.get("labels"), list) else []
    labels: list[dict] = []
    identities: list[str] = []
    for row in rows[:100]:
        if isinstance(row, str):
            label = row.strip()
            if label:
                labels.append({"label": label})
                identities.append(label)
            continue
        if not isinstance(row, dict):
            continue
        label = row.get("label") or row.get("name")
        normalized = {
            key: row.get(key)
            for key in ("label", "name", "category", "confidence")
            if row.get(key) is not None
        }
        if normalized:
            labels.append(normalized)
        if isinstance(label, str) and label.strip():
            identities.append(label.strip())
    return {"labels": labels, "identity_candidates": list(dict.fromkeys(identities))}


def _arkham_normalize(body: object) -> dict:
    if not isinstance(body, dict):
        return {"entity": None, "label": None, "tags": [], "identity_candidates": []}
    entity_obj = body.get("entity") or body.get("arkhamEntity")
    entity_name = None
    entity_id = None
    if isinstance(entity_obj, dict):
        entity_name = entity_obj.get("name") or entity_obj.get("label")
        entity_id = entity_obj.get("id") or entity_obj.get("entityId")
    elif isinstance(entity_obj, str):
        entity_name = entity_obj
    if not isinstance(entity_name, str) or not entity_name.strip():
        external_name = body.get("entityName")
        entity_name = external_name.strip() if isinstance(external_name, str) and external_name.strip() else None
    else:
        entity_name = entity_name.strip()

    label_obj = body.get("label") or body.get("arkhamLabel")
    if isinstance(label_obj, dict):
        raw_label = label_obj.get("name") or label_obj.get("label")
        label = raw_label.strip() if isinstance(raw_label, str) and raw_label.strip() else None
    else:
        label = label_obj.strip() if isinstance(label_obj, str) and label_obj.strip() else None

    tags_raw = body.get("tags") or []
    tags: list[str] = []
    if isinstance(tags_raw, list):
        for row in tags_raw[:100]:
            if isinstance(row, str) and row.strip():
                tags.append(row.strip())
            elif isinstance(row, dict):
                value = row.get("name") or row.get("tag") or row.get("label")
                if isinstance(value, str) and value.strip():
                    tags.append(value.strip())
    identities = [item for item in (entity_name, label) if item]
    return {
        "entity": {"name": entity_name, "id": entity_id} if entity_name or entity_id else None,
        "label": label,
        "tags": list(dict.fromkeys(tags)),
        "identity_candidates": list(dict.fromkeys(identities)),
    }


def _canonical_identity(value: str) -> str:
    return " ".join(value.lower().replace(":", " ").replace("-", " ").split())


def _invalid_input(message: str, missing: str) -> EngineResult:
    return EngineResult(
        engine_id=EngineId.B4,
        engine_version="1.0.0",
        status=AnalysisStatus.INSUFFICIENT_DATA,
        risk_score=0,
        data_confidence=0,
        engine_confidence=0,
        severity=Severity.UNKNOWN,
        summary=message,
        warnings=["No entity or fund-flow conclusion was inferred from invalid input."],
        missing_data=[missing],
        provider_consensus="UNAVAILABLE",
        demo=False,
    )


def run_live_b4(data: dict) -> EngineResult:
    wallet = _address(data.get("wallet") or data.get("address"))
    if not wallet:
        return _invalid_input("B4 requires a valid wallet/address.", "valid wallet/address")

    limit = _parse_limit(data.get("limit", 100))
    if limit is None:
        return _invalid_input("B4 limit must be a positive integer.", "positive history limit")

    try:
        chain = normalize_chain(data.get("chain", "ethereum"))
    except ValueError as exc:
        return EngineResult(
            engine_id=EngineId.B4,
            engine_version="1.0.0",
            status=AnalysisStatus.UNSUPPORTED,
            risk_score=0,
            data_confidence=0,
            engine_confidence=0,
            severity=Severity.UNKNOWN,
            summary=str(exc),
            missing_data=["supported chain"],
            provider_consensus="UNAVAILABLE",
            demo=False,
        )

    evidence: list[EvidenceRecord] = []
    provider_status: list[dict] = []
    warnings: list[str] = []
    missing: list[str] = []
    now = datetime.now(timezone.utc)

    try:
        rpc_provider, rpc, _probe, attempts = select_rpc_client(chain.chain_id)
        block_call = rpc.call("eth_blockNumber")
        block_number = _rpc_uint(block_call.result)
        if block_number is None:
            raise ProviderError(
                "RPC returned malformed block state",
                provider_id=rpc_provider,
                code="MALFORMED_RESPONSE",
            )
        block_tag = hex(block_number)
        balance_call = rpc.call("eth_getBalance", [wallet, block_tag])
        balance_wei = _rpc_uint(balance_call.result)
        if balance_wei is None:
            raise ProviderError(
                "RPC returned malformed balance state",
                provider_id=rpc_provider,
                code="MALFORMED_RESPONSE",
            )
        native_balance = balance_wei / 10**18
        provider_status.extend(attempts)
        provider_status.append(
            {
                "provider_id": rpc_provider,
                "status": "HEALTHY",
                "block_number": block_number,
                "latency_ms": balance_call.latency_ms,
            }
        )
        evidence.append(
            EvidenceRecord(
                evidence_id=str(uuid4()),
                provider=rpc_provider,
                source_type="direct_state",
                provider_endpoint=balance_call.endpoint,
                provider_request_id=balance_call.request_id,
                retrieved_at=now,
                observed_at=now,
                block_number=block_number,
                chain_id=chain.chain_id,
                raw_reference=wallet,
                normalized_value={
                    "wallet": wallet,
                    "native_balance": native_balance,
                    "native_symbol": chain.native_symbol,
                    "block_tag": block_tag,
                },
                confidence=92,
                freshness=FreshnessStatus.LIVE,
                license_classification="direct-rpc",
            )
        )
    except ProviderError as exc:
        return EngineResult(
            engine_id=EngineId.B4,
            engine_version="1.0.0",
            status=AnalysisStatus.PROVIDER_UNAVAILABLE,
            risk_score=0,
            data_confidence=0,
            engine_confidence=0,
            severity=Severity.UNKNOWN,
            summary=f"Direct blockchain state is unavailable for {chain.name}; Rivexis did not fabricate wallet balances or activity.",
            warnings=[str(exc)],
            missing_data=["direct blockchain state"],
            provider_consensus="UNAVAILABLE",
            provider_status=[{"provider_id": exc.provider_id, "status": exc.code}],
            demo=False,
        )

    normal_txs: list[dict] = []
    token_txs: list[dict] = []
    es = EtherscanClient()
    if es.configured:
        try:
            normal_call = es.account_transactions(chain, wallet, offset=limit)
            token_call = es.token_transactions(chain, wallet, offset=limit)
            normal_txs = _result_list(normal_call)
            token_txs = _result_list(token_call)
            provider_status.append(
                {
                    "provider_id": "etherscan",
                    "status": "HEALTHY",
                    "latency_ms": round(normal_call.latency_ms + token_call.latency_ms, 2),
                }
            )
            retrieved = datetime.now(timezone.utc)
            evidence.append(
                EvidenceRecord(
                    evidence_id=str(uuid4()),
                    provider="etherscan",
                    source_type="indexed_account_history",
                    provider_endpoint=normal_call.endpoint,
                    provider_request_id=normal_call.request_id,
                    retrieved_at=retrieved,
                    observed_at=retrieved,
                    block_number=block_number,
                    chain_id=chain.chain_id,
                    raw_reference=wallet,
                    normalized_value={
                        "normal_transaction_count": len(normal_txs),
                        "erc20_transfer_count": len(token_txs),
                    },
                    confidence=72,
                    freshness=FreshnessStatus.UNKNOWN,
                    license_classification="external-provider-attributed",
                )
            )
        except ProviderError as exc:
            provider_status.append({"provider_id": "etherscan", "status": exc.code})
            warnings.append(f"Indexed history unavailable from Etherscan: {exc}")
            missing.append("indexed transaction/token-transfer history")
    else:
        provider_status.append({"provider_id": "etherscan", "status": "CREDENTIALS_REQUIRED"})
        missing.append("indexed transaction/token-transfer history (Etherscan key not configured)")

    counterparty_flows: dict[str, dict] = defaultdict(
        lambda: {
            "normal_in_count": 0,
            "normal_out_count": 0,
            "token_in_count": 0,
            "token_out_count": 0,
            "native_in": 0.0,
            "native_out": 0.0,
            "token_assets": {},
        }
    )
    native_in = native_out = 0.0
    malformed_history_rows = 0
    token_metadata_conflicts = 0
    normalized_normal_rows = 0
    normalized_token_rows = 0

    for tx in normal_txs:
        frm = _address(tx.get("from"))
        to = _address(tx.get("to"))
        raw_value = _uint_decimal(tx.get("value") or 0)
        if raw_value is None or (frm != wallet and to != wallet):
            malformed_history_rows += 1
            continue
        value = raw_value / 10**18
        normalized_normal_rows += 1
        if frm == wallet:
            native_out += value
            if to:
                row = counterparty_flows[to]
                row["normal_out_count"] += 1
                row["native_out"] += value
        elif to == wallet:
            native_in += value
            if frm:
                row = counterparty_flows[frm]
                row["normal_in_count"] += 1
                row["native_in"] += value

    tokens: dict[str, dict] = {}
    for tx in token_txs:
        contract = _address(tx.get("contractAddress"))
        raw_amount = _uint_decimal(tx.get("value") or 0)
        decimals = _uint_decimal(tx.get("tokenDecimal"), maximum=255)
        frm = _address(tx.get("from"))
        to = _address(tx.get("to"))
        if (
            contract is None
            or raw_amount is None
            or decimals is None
            or (frm != wallet and to != wallet)
        ):
            malformed_history_rows += 1
            continue

        symbol = str(tx.get("tokenSymbol") or "UNKNOWN").strip()[:64] or "UNKNOWN"
        existing = tokens.get(contract)
        if existing is not None and existing["decimals"] != decimals:
            malformed_history_rows += 1
            token_metadata_conflicts += 1
            continue

        amount = raw_amount / (10**decimals)
        if existing is None:
            existing = {
                "contract": contract,
                "symbols": set(),
                "decimals": decimals,
                "in": 0.0,
                "out": 0.0,
                "count": 0,
            }
            tokens[contract] = existing
        existing["symbols"].add(symbol)
        existing["count"] += 1
        normalized_token_rows += 1

        if frm == wallet:
            existing["out"] += amount
            counterparty = to
            direction = "out"
        else:
            existing["in"] += amount
            counterparty = frm
            direction = "in"

        if counterparty:
            counterparty_row = counterparty_flows[counterparty]
            counterparty_row[f"token_{direction}_count"] += 1
            asset_row = counterparty_row["token_assets"].setdefault(
                contract,
                {
                    "contract": contract,
                    "symbols": set(),
                    "decimals": decimals,
                    "in": 0.0,
                    "out": 0.0,
                    "count": 0,
                },
            )
            asset_row["symbols"].add(symbol)
            asset_row["count"] += 1
            asset_row[direction] += amount

    if malformed_history_rows:
        warnings.append(
            f"Skipped {malformed_history_rows} indexed history row(s) with malformed identity/value/decimal fields; no zero-value substitution was made."
        )
        missing.append("fully normalized indexed transaction/token-transfer values")
    if token_metadata_conflicts:
        warnings.append(
            f"Skipped {token_metadata_conflicts} ERC-20 transfer row(s) whose decimals conflicted with another row for the same token contract."
        )
        missing.append("consistent indexed ERC-20 metadata for every transfer")

    identity_sources: list[dict] = []
    conflicts: list[SourceConflict] = []

    nansen = NansenClient()
    if nansen.configured:
        try:
            call = nansen.address_labels(address=wallet, chain=chain.key)
            if not isinstance(call.result, dict):
                provider_status.append(
                    {"provider_id": "nansen", "status": "MALFORMED_RESPONSE"}
                )
                warnings.append("Nansen returned a non-object entity-label payload; it was not treated as no-attribution evidence.")
            else:
                normalized = _nansen_normalize(call.result)
                identity_sources.append({"provider": "nansen", **normalized})
                evidence.append(
                    _provider_evidence(
                        call,
                        provider="nansen",
                        normalized_value=normalized,
                        chain_id=chain.chain_id,
                        block_number=block_number,
                        wallet=wallet,
                        confidence=82,
                    )
                )
                provider_status.append(
                    {
                        "provider_id": "nansen",
                        "status": "HEALTHY",
                        "latency_ms": round(call.latency_ms, 2),
                    }
                )
        except ProviderError as exc:
            provider_status.append(
                {"provider_id": "nansen", "status": exc.code, "detail": str(exc)}
            )
            warnings.append(f"Nansen entity-label evidence was unavailable: {exc.code}.")
    else:
        provider_status.append({"provider_id": "nansen", "status": "CREDENTIALS_REQUIRED"})

    arkham = ArkhamClient()
    if arkham.credentialed and not arkham.license_approved:
        provider_status.append(
            {"provider_id": "arkham", "status": "LICENSE_APPROVAL_REQUIRED"}
        )
        warnings.append(
            "Arkham credentials are present but the adapter is disabled until this deployment explicitly approves the applicable API/commercial terms."
        )
    elif arkham.configured:
        try:
            call = arkham.address_intelligence(wallet)
            if not isinstance(call.result, dict):
                provider_status.append(
                    {"provider_id": "arkham", "status": "MALFORMED_RESPONSE"}
                )
                warnings.append("Arkham returned a non-object entity-intelligence payload; it was not treated as no-attribution evidence.")
            else:
                normalized = _arkham_normalize(call.result)
                identity_sources.append({"provider": "arkham", **normalized})
                evidence.append(
                    _provider_evidence(
                        call,
                        provider="arkham",
                        normalized_value=normalized,
                        chain_id=chain.chain_id,
                        block_number=block_number,
                        wallet=wallet,
                        confidence=78,
                    )
                )
                provider_status.append(
                    {
                        "provider_id": "arkham",
                        "status": "HEALTHY",
                        "latency_ms": round(call.latency_ms, 2),
                    }
                )
        except ProviderError as exc:
            provider_status.append(
                {"provider_id": "arkham", "status": exc.code, "detail": str(exc)}
            )
            warnings.append(f"Arkham entity intelligence was unavailable: {exc.code}.")
    else:
        provider_status.append({"provider_id": "arkham", "status": "CREDENTIALS_REQUIRED"})

    attributed = [
        (source["provider"], source["identity_candidates"][0])
        for source in identity_sources
        if source.get("identity_candidates")
    ]
    identity = "UNKNOWN ADDRESS"
    identity_provenance: list[dict] = []
    if attributed:
        unique: dict[str, list[tuple[str, str]]] = {}
        for provider, label in attributed:
            unique.setdefault(_canonical_identity(label), []).append((provider, label))
            identity_provenance.append({"provider": provider, "label": label})
        if len(unique) == 1:
            identity = attributed[0][1]
        else:
            identity = "CONFLICTING EXTERNAL LABELS"
            (provider_a, label_a), (provider_b, label_b) = attributed[0], attributed[1]
            conflicts.append(
                SourceConflict(
                    metric="entity_identity",
                    source_a=provider_a,
                    value_a=label_a,
                    source_b=provider_b,
                    value_b=label_b,
                    severity="high",
                    resolution_method="unresolved_external_attribution_conflict",
                    resolution_confidence=0,
                )
            )
            warnings.append(
                "External entity providers disagree on the address identity; Rivexis did not silently choose one label."
            )

    def asset_rows(asset_map: dict[str, dict]) -> list[dict]:
        rows = []
        for contract, row in sorted(asset_map.items()):
            symbols = sorted(row["symbols"])
            rows.append(
                {
                    "contract": contract,
                    "symbol": symbols[0] if len(symbols) == 1 else None,
                    "symbols": symbols,
                    "decimals": row["decimals"],
                    "in": row["in"],
                    "out": row["out"],
                    "net": row["in"] - row["out"],
                    "count": row["count"],
                }
            )
        return rows

    counterparty_counts = {
        address: (
            row["normal_in_count"]
            + row["normal_out_count"]
            + row["token_in_count"]
            + row["token_out_count"]
        )
        for address, row in counterparty_flows.items()
    }
    indexed_records_with_counterparty = sum(counterparty_counts.values())
    ordered_counterparties = sorted(
        counterparty_flows,
        key=lambda address: (-counterparty_counts[address], address),
    )
    top_counterparties = []
    for address in ordered_counterparties[:10]:
        row = counterparty_flows[address]
        count = counterparty_counts[address]
        top_counterparties.append(
            {
                "address": address,
                "identity": "UNKNOWN ADDRESS",
                "interaction_count": count,
                "interaction_share_pct": (
                    round((count / indexed_records_with_counterparty) * 100, 4)
                    if indexed_records_with_counterparty
                    else 0.0
                ),
                "inbound_record_count": row["normal_in_count"] + row["token_in_count"],
                "outbound_record_count": row["normal_out_count"] + row["token_out_count"],
                "normal_transaction_counts": {
                    "in": row["normal_in_count"],
                    "out": row["normal_out_count"],
                },
                "erc20_transfer_counts": {
                    "in": row["token_in_count"],
                    "out": row["token_out_count"],
                },
                "native_in": row["native_in"],
                "native_out": row["native_out"],
                "native_net": row["native_in"] - row["native_out"],
                "token_assets": asset_rows(row["token_assets"]),
            }
        )

    token_flows = asset_rows(tokens)
    shares = (
        [count / indexed_records_with_counterparty for count in counterparty_counts.values()]
        if indexed_records_with_counterparty
        else []
    )
    ordered_shares = sorted(shares, reverse=True)
    counterparty_concentration = {
        "unique_counterparties": len(counterparty_counts),
        "indexed_records_with_counterparty": indexed_records_with_counterparty,
        "top_counterparty_share_pct": round(ordered_shares[0] * 100, 4) if ordered_shares else 0.0,
        "top3_share_pct": round(sum(ordered_shares[:3]) * 100, 4) if ordered_shares else 0.0,
        "interaction_hhi": round(sum(share * share for share in shares) * 10000, 2),
        "basis": "validated indexed normal-transaction and ERC-20 transfer records with a normalized opposite address",
        "risk_interpretation": "descriptive_only_not_scored",
    }

    activity_count = normalized_normal_rows + normalized_token_rows
    data_conf = 82 if activity_count else 58
    if malformed_history_rows:
        data_conf = max(35, data_conf - 10)
    if attributed:
        data_conf = min(94, data_conf + 7)
    if conflicts:
        data_conf = max(35, data_conf - 20)
    consensus = (
        "CONFLICTING"
        if conflicts
        else "MULTI_SOURCE"
        if len({item.provider for item in evidence}) > 1
        else "SINGLE_SOURCE"
    )
    risk = 10.0 + (5 if activity_count >= 150 else 0) + (8 if conflicts else 0)

    if identity == "UNKNOWN ADDRESS":
        warnings.append(
            "No attributable external entity label was returned; this address remains UNKNOWN ADDRESS."
        )
        missing.append("attributed Nansen/Arkham or verified entity labels")
    elif identity == "CONFLICTING EXTERNAL LABELS":
        missing.append("resolved entity identity")
    missing.extend(
        [
            "cross-chain activity outside the selected chain",
            "full internal-call and protocol semantic classification",
            "realized/unrealized PnL and cost basis",
        ]
    )

    return EngineResult(
        engine_id=EngineId.B4,
        engine_version="1.0.0",
        status=AnalysisStatus.PARTIAL,
        risk_score=risk,
        data_confidence=data_conf,
        engine_confidence=62 if attributed else 55,
        severity=Severity.LOW,
        summary=f"Direct state and attributed entity intelligence were evaluated for {wallet} on {chain.name}. Identity state: {identity}.",
        metrics={
            "entity_profile": {
                "address": wallet,
                "identity": identity,
                "identity_provenance": identity_provenance,
                "chain": chain.name,
                "native_balance": native_balance,
                "native_symbol": chain.native_symbol,
            },
            "external_identity_evidence": identity_sources,
            "activity": {
                "indexed_normal_transactions": len(normal_txs),
                "indexed_erc20_transfers": len(token_txs),
                "normalized_normal_transactions": normalized_normal_rows,
                "normalized_erc20_transfers": normalized_token_rows,
                "normalized_activity_records": activity_count,
                "malformed_indexed_rows_skipped": malformed_history_rows,
                "token_metadata_conflicts_skipped": token_metadata_conflicts,
                "native_in": native_in,
                "native_out": native_out,
                "native_net": native_in - native_out,
            },
            "top_counterparties": top_counterparties,
            "counterparty_concentration": counterparty_concentration,
            "token_flows": token_flows,
        },
        warnings=warnings,
        evidence=evidence,
        provider_consensus=consensus,
        provider_conflicts=conflicts,
        data_freshness={"status": "LIVE", "block_number": block_number},
        missing_data=sorted(set(missing)),
        provider_status=provider_status,
        assumptions=[
            f"Direct native-balance state was pinned to captured RPC block {block_tag} ({block_number}) before evidence was stamped with that block reference.",
            "Provider-attributed labels are evidence, not absolute truth. Absence of a label is not evidence of benign or malicious ownership.",
            "External indexer/entity-label responses without a normalized provider observation timestamp are recorded with UNKNOWN evidence freshness rather than CURRENT.",
            "Counterparty concentration is descriptive concentration of validated indexed records, not economic exposure, ownership or maliciousness, and is not used in the B4 risk score.",
        ],
        demo=False,
    )