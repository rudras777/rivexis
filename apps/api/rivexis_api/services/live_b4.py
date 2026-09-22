from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
from uuid import uuid4

from rivexis_api.chains import normalize_chain
from rivexis_api.models.engine import EngineResult
from rivexis_api.models.enums import AnalysisStatus, EngineId, FreshnessStatus, Severity
from rivexis_api.models.evidence import EvidenceRecord, SourceConflict
from rivexis_api.provider_clients import ArkhamClient, EtherscanClient, NansenClient, ProviderError, hex_to_int
from rivexis_api.providers import select_rpc_client


def _address(value: object) -> str | None:
    s = str(value or "").strip().lower()
    if len(s) != 42 or not s.startswith("0x"):
        return None
    try:
        int(s[2:], 16)
    except ValueError:
        return None
    return s


def _result_list(call) -> list[dict]:
    body = call.result if isinstance(call.result, dict) else {}
    rows = body.get("result")
    return [x for x in rows if isinstance(x, dict)] if isinstance(rows, list) else []


def _provider_evidence(call, *, provider: str, normalized_value: dict, chain_id: int, block_number: int | None, wallet: str, confidence: float) -> EvidenceRecord:
    return EvidenceRecord(
        evidence_id=str(uuid4()),
        provider=provider,
        source_type="entity_label_intelligence",
        provider_endpoint=call.endpoint,
        provider_request_id=call.request_id,
        retrieved_at=datetime.now(timezone.utc),
        observed_at=datetime.now(timezone.utc),
        block_number=block_number,
        chain_id=chain_id,
        raw_reference=f"provider:{provider};request:{call.request_id};address:{wallet}",
        normalized_value=normalized_value,
        confidence=confidence,
        freshness=FreshnessStatus.CURRENT,
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
        normalized = {k: row.get(k) for k in ("label", "name", "category", "confidence") if row.get(k) is not None}
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
    entity_name = entity_name or body.get("entityName")
    label_obj = body.get("label") or body.get("arkhamLabel")
    if isinstance(label_obj, dict):
        label = label_obj.get("name") or label_obj.get("label")
    else:
        label = label_obj if isinstance(label_obj, str) else None
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
    identities = [x.strip() for x in (entity_name, label) if isinstance(x, str) and x.strip()]
    return {
        "entity": {"name": entity_name, "id": entity_id} if entity_name or entity_id else None,
        "label": label,
        "tags": list(dict.fromkeys(tags)),
        "identity_candidates": list(dict.fromkeys(identities)),
    }


def _canonical_identity(value: str) -> str:
    return " ".join(value.lower().replace(":", " ").replace("-", " ").split())


def run_live_b4(data: dict) -> EngineResult:
    wallet = _address(data.get("wallet") or data.get("address"))
    if not wallet:
        return EngineResult(
            engine_id=EngineId.B4,
            status=AnalysisStatus.INSUFFICIENT_DATA,
            risk_score=0,
            data_confidence=0,
            engine_confidence=0,
            severity=Severity.UNKNOWN,
            summary="B4 requires a valid wallet/address.",
            warnings=["No entity identity was inferred from invalid or missing input."],
            missing_data=["valid wallet/address"],
            provider_consensus="UNAVAILABLE",
            demo=False,
        )
    try:
        chain = normalize_chain(data.get("chain", "ethereum"))
    except ValueError as exc:
        return EngineResult(engine_id=EngineId.B4,status=AnalysisStatus.UNSUPPORTED,risk_score=0,data_confidence=0,engine_confidence=0,severity=Severity.UNKNOWN,summary=str(exc),missing_data=["supported chain"],demo=False)

    evidence: list[EvidenceRecord] = []
    provider_status: list[dict] = []
    warnings: list[str] = []
    missing: list[str] = []
    now = datetime.now(timezone.utc)

    try:
        rpc_provider, rpc, probe, attempts = select_rpc_client(chain.chain_id)
        block_call = rpc.call("eth_blockNumber")
        balance_call = rpc.call("eth_getBalance", [wallet, "latest"])
        block_number = hex_to_int(block_call.result) or 0
        balance_wei = hex_to_int(balance_call.result) or 0
        native_balance = balance_wei / 10**18
        provider_status.extend(attempts)
        provider_status.append({"provider_id": rpc_provider, "status": "HEALTHY", "block_number": block_number, "latency_ms": balance_call.latency_ms})
        evidence.append(EvidenceRecord(
            evidence_id=str(uuid4()),provider=rpc_provider,source_type="direct_state",provider_endpoint=balance_call.endpoint,provider_request_id=balance_call.request_id,
            retrieved_at=now,observed_at=now,block_number=block_number,chain_id=chain.chain_id,raw_reference=wallet,
            normalized_value={"wallet":wallet,"native_balance":native_balance,"native_symbol":chain.native_symbol},confidence=92,freshness=FreshnessStatus.LIVE,license_classification="direct-rpc"
        ))
    except ProviderError as exc:
        return EngineResult(
            engine_id=EngineId.B4,status=AnalysisStatus.PROVIDER_UNAVAILABLE,risk_score=0,data_confidence=0,engine_confidence=0,severity=Severity.UNKNOWN,
            summary=f"Direct blockchain state is unavailable for {chain.name}; Rivexis did not fabricate wallet balances or activity.",warnings=[str(exc)],missing_data=["direct blockchain state"],provider_consensus="UNAVAILABLE",provider_status=[{"provider_id":exc.provider_id,"status":exc.code}],demo=False
        )

    normal_txs: list[dict] = []
    token_txs: list[dict] = []
    es = EtherscanClient()
    if es.configured:
        limit = min(max(int(data.get("limit", 100)), 1), 250)
        try:
            normal_call = es.account_transactions(chain, wallet, offset=limit)
            token_call = es.token_transactions(chain, wallet, offset=limit)
            normal_txs = _result_list(normal_call)
            token_txs = _result_list(token_call)
            provider_status.append({"provider_id":"etherscan","status":"HEALTHY","latency_ms":round(normal_call.latency_ms+token_call.latency_ms,2)})
            evidence.append(EvidenceRecord(
                evidence_id=str(uuid4()),provider="etherscan",source_type="indexed_account_history",provider_endpoint=normal_call.endpoint,provider_request_id=normal_call.request_id,
                retrieved_at=now,observed_at=now,block_number=block_number,chain_id=chain.chain_id,raw_reference=wallet,
                normalized_value={"normal_transaction_count":len(normal_txs),"erc20_transfer_count":len(token_txs)},confidence=78,freshness=FreshnessStatus.CURRENT,license_classification="external-provider-attributed"
            ))
        except ProviderError as exc:
            provider_status.append({"provider_id":"etherscan","status":exc.code})
            warnings.append(f"Indexed history unavailable from Etherscan: {exc}")
            missing.append("indexed transaction/token-transfer history")
    else:
        provider_status.append({"provider_id":"etherscan","status":"CREDENTIALS_REQUIRED"})
        missing.append("indexed transaction/token-transfer history (Etherscan key not configured)")

    counterparties = Counter()
    native_in = native_out = 0.0
    for tx in normal_txs:
        frm = _address(tx.get("from")); to = _address(tx.get("to"))
        value = float(tx.get("value") or 0) / 10**18
        if frm == wallet:
            native_out += value
            if to: counterparties[to] += 1
        elif to == wallet:
            native_in += value
            if frm: counterparties[frm] += 1

    tokens = defaultdict(lambda: {"in":0.0,"out":0.0,"count":0,"contract":None})
    for tx in token_txs:
        decimals = int(tx.get("tokenDecimal") or 0) if str(tx.get("tokenDecimal") or "0").isdigit() else 0
        amount = float(tx.get("value") or 0) / (10**decimals if decimals >= 0 else 1)
        symbol = str(tx.get("tokenSymbol") or "UNKNOWN")
        row = tokens[symbol]; row["contract"] = tx.get("contractAddress"); row["count"] += 1
        frm = _address(tx.get("from")); to = _address(tx.get("to"))
        if frm == wallet:
            row["out"] += amount
            if to: counterparties[to] += 1
        elif to == wallet:
            row["in"] += amount
            if frm: counterparties[frm] += 1

    identity_sources: list[dict] = []
    conflicts: list[SourceConflict] = []

    nansen = NansenClient()
    if nansen.configured:
        try:
            call = nansen.address_labels(address=wallet, chain=chain.key)
            normalized = _nansen_normalize(call.result)
            identity_sources.append({"provider": "nansen", **normalized})
            evidence.append(_provider_evidence(call, provider="nansen", normalized_value=normalized, chain_id=chain.chain_id, block_number=block_number, wallet=wallet, confidence=82))
            provider_status.append({"provider_id": "nansen", "status": "HEALTHY", "latency_ms": round(call.latency_ms, 2)})
        except ProviderError as exc:
            provider_status.append({"provider_id": "nansen", "status": exc.code, "detail": str(exc)})
            warnings.append(f"Nansen entity-label evidence was unavailable: {exc.code}.")
    else:
        provider_status.append({"provider_id": "nansen", "status": "CREDENTIALS_REQUIRED"})

    arkham = ArkhamClient()
    if arkham.credentialed and not arkham.license_approved:
        provider_status.append({"provider_id": "arkham", "status": "LICENSE_APPROVAL_REQUIRED"})
        warnings.append("Arkham credentials are present but the adapter is disabled until this deployment explicitly approves the applicable API/commercial terms.")
    elif arkham.configured:
        try:
            call = arkham.address_intelligence(wallet)
            normalized = _arkham_normalize(call.result)
            identity_sources.append({"provider": "arkham", **normalized})
            evidence.append(_provider_evidence(call, provider="arkham", normalized_value=normalized, chain_id=chain.chain_id, block_number=block_number, wallet=wallet, confidence=78))
            provider_status.append({"provider_id": "arkham", "status": "HEALTHY", "latency_ms": round(call.latency_ms, 2)})
        except ProviderError as exc:
            provider_status.append({"provider_id": "arkham", "status": exc.code, "detail": str(exc)})
            warnings.append(f"Arkham entity intelligence was unavailable: {exc.code}.")
    else:
        provider_status.append({"provider_id": "arkham", "status": "CREDENTIALS_REQUIRED"})

    attributed = [(src["provider"], src["identity_candidates"][0]) for src in identity_sources if src.get("identity_candidates")]
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
            (pa, la), (pb, lb) = attributed[0], attributed[1]
            conflicts.append(SourceConflict(
                metric="entity_identity", source_a=pa, value_a=la, source_b=pb, value_b=lb,
                severity="high", resolution_method="unresolved_external_attribution_conflict", resolution_confidence=0,
            ))
            warnings.append("External entity providers disagree on the address identity; Rivexis did not silently choose one label.")

    top_counterparties = [{"address":a,"interaction_count":c,"identity":"UNKNOWN ADDRESS"} for a,c in counterparties.most_common(10)]
    token_flows = [{"symbol":k,**v,"net":v["in"]-v["out"]} for k,v in sorted(tokens.items())]
    activity_count = len(normal_txs) + len(token_txs)
    data_conf = 82 if normal_txs or token_txs else 58
    if identity_sources:
        data_conf = min(94, data_conf + 7)
    if conflicts:
        data_conf = max(35, data_conf - 20)
    consensus = "CONFLICTING" if conflicts else "MULTI_SOURCE" if len({e.provider for e in evidence}) > 1 else "SINGLE_SOURCE"
    risk = 10.0 + (5 if activity_count >= 150 else 0) + (8 if conflicts else 0)

    if identity == "UNKNOWN ADDRESS":
        warnings.append("No attributable external entity label was returned; this address remains UNKNOWN ADDRESS.")
        missing.append("attributed Nansen/Arkham or verified entity labels")
    elif identity == "CONFLICTING EXTERNAL LABELS":
        missing.append("resolved entity identity")
    missing.extend([
        "cross-chain activity outside the selected chain",
        "full internal-call and protocol semantic classification",
        "realized/unrealized PnL and cost basis",
    ])

    return EngineResult(
        engine_id=EngineId.B4,status=AnalysisStatus.PARTIAL,risk_score=risk,data_confidence=data_conf,engine_confidence=62 if identity_sources else 55,severity=Severity.LOW,
        summary=f"Direct state and attributed entity intelligence were evaluated for {wallet} on {chain.name}. Identity state: {identity}.",
        metrics={
            "entity_profile":{"address":wallet,"identity":identity,"identity_provenance":identity_provenance,"chain":chain.name,"native_balance":native_balance,"native_symbol":chain.native_symbol},
            "external_identity_evidence":identity_sources,
            "activity":{"indexed_normal_transactions":len(normal_txs),"indexed_erc20_transfers":len(token_txs),"native_in":native_in,"native_out":native_out,"native_net":native_in-native_out},
            "top_counterparties":top_counterparties,"token_flows":token_flows,
        },
        warnings=warnings,evidence=evidence,provider_consensus=consensus,provider_conflicts=conflicts,data_freshness={"status":"LIVE","block_number":block_number},missing_data=sorted(set(missing)),provider_status=provider_status,
        assumptions=["Provider-attributed labels are evidence, not absolute truth. Absence of a label is not evidence of benign or malicious ownership."],demo=False
    )
