from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from rivexis_api.chains import normalize_chain
from rivexis_api.models.engine import EngineResult
from rivexis_api.models.enums import AnalysisStatus, EngineId, FreshnessStatus, Severity
from rivexis_api.models.evidence import EvidenceRecord
from rivexis_api.provider_clients import CoinGeckoClient, ProviderCall, ProviderError, hex_to_int
from rivexis_api.providers import select_rpc_client

NATIVE_GECKO = {
    "ethereum": "ethereum",
    "base": "ethereum",
    "arbitrum": "ethereum",
    "optimism": "ethereum",
    "polygon": "polygon-ecosystem-token",
}
BALANCE_OF_SELECTOR = "0x70a08231"


def ev(
    call: ProviderCall,
    provider: str,
    source_type: str,
    value: Any,
    chain_id: int | None = None,
    block: int | None = None,
    confidence: float = 90,
    endpoint: str | None = None,
    freshness: FreshnessStatus = FreshnessStatus.LIVE,
    observed_at: datetime | None = None,
) -> EvidenceRecord:
    now = datetime.now(timezone.utc)
    return EvidenceRecord(
        evidence_id=str(uuid4()),
        provider=provider,
        source_type=source_type,
        provider_endpoint=endpoint,
        provider_request_id=call.request_id,
        retrieved_at=now,
        observed_at=observed_at or now,
        chain_id=chain_id,
        block_number=block,
        raw_reference=f"provider:{provider};request:{call.request_id}",
        normalized_value=value,
        calculation_version="f1-live-1.2.0",
        engine_version="1.2.0",
        confidence=confidence,
        freshness=freshness,
        license_classification="external-provider-evidence",
    )


def _market_freshness(prices: dict[str, Any], ids: list[str]):
    now = datetime.now(timezone.utc)
    stamps = []
    for cid in ids:
        row = prices.get(cid)
        raw = row.get("last_updated_at") if isinstance(row, dict) else None
        try:
            if raw not in (None, ""):
                stamps.append(float(raw))
        except (TypeError, ValueError):
            pass
    if not stamps:
        return FreshnessStatus.UNKNOWN, None, now
    observed = datetime.fromtimestamp(min(stamps), tz=timezone.utc)
    age = max(0.0, (now - observed).total_seconds())
    status = (
        FreshnessStatus.LIVE
        if age <= 120
        else FreshnessStatus.CURRENT
        if age <= 900
        else FreshnessStatus.RECENT
        if age <= 3600
        else FreshnessStatus.STALE
        if age <= 21600
        else FreshnessStatus.EXPIRED
    )
    return status, age, observed


def _sev(score: float) -> Severity:
    if score >= 80:
        return Severity.CRITICAL
    if score >= 60:
        return Severity.HIGH
    if score >= 35:
        return Severity.MODERATE
    return Severity.LOW


def _address(value: object) -> str | None:
    raw = str(value or "").strip().lower()
    if len(raw) != 42 or not raw.startswith("0x"):
        return None
    try:
        int(raw[2:], 16)
    except ValueError:
        return None
    return raw


def _balance_of_calldata(wallet: str) -> str:
    return BALANCE_OF_SELECTOR + ("0" * 24) + wallet[2:]


def _aggregate_positions(positions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Aggregate one economic exposure before concentration scoring.

    Multiple wallets, or a manual position plus an observed wallet balance, must not
    appear as independent diversification merely because they were collected as
    separate rows.
    """

    grouped: dict[str, dict[str, Any]] = {}
    for position in positions:
        asset_id = str(position["id"])
        row = grouped.setdefault(
            asset_id,
            {
                "id": asset_id,
                "label": str(position.get("label") or asset_id),
                "quantity": 0.0,
                "sources": [],
            },
        )
        row["quantity"] += float(position.get("quantity") or 0)
        source = str(position.get("source") or "unknown")
        if source not in row["sources"]:
            row["sources"].append(source)
    return list(grouped.values())


def _erc20_specs(input_data: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    raw = input_data.get("erc20_tokens") or input_data.get("token_contracts") or []
    if raw and not isinstance(raw, list):
        return [], ["erc20_tokens must be a list"]
    specs = []
    missing = []
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            missing.append(f"valid ERC-20 token descriptor at index {index}")
            continue
        contract = _address(item.get("contract_address") or item.get("contract"))
        asset_id = item.get("coingecko_id") or item.get("asset_id")
        decimals = item.get("decimals")
        if contract is None or asset_id is None or decimals is None:
            missing.append(
                f"ERC-20 descriptor {index} requires contract_address, coingecko_id, and decimals"
            )
            continue
        try:
            decimals = int(decimals)
        except (TypeError, ValueError):
            missing.append(f"numeric ERC-20 decimals for {asset_id}")
            continue
        if decimals < 0 or decimals > 36:
            missing.append(f"ERC-20 decimals between 0 and 36 for {asset_id}")
            continue
        specs.append(
            {
                "contract": contract,
                "id": str(asset_id),
                "label": str(item.get("symbol") or asset_id),
                "decimals": decimals,
            }
        )
    return specs, missing


def run_live_f1(input_data: dict[str, Any]) -> EngineResult:
    positions: list[dict[str, Any]] = []
    evidence: list[EvidenceRecord] = []
    statuses: list[dict[str, Any]] = []
    warnings: list[str] = []
    missing: list[str] = []
    assumptions: list[str] = []

    manual = input_data.get("manual_positions") or input_data.get("positions") or []
    if manual and not isinstance(manual, list):
        return _fail("manual_positions must be a list")
    manual_used = False
    for pos in manual:
        if not isinstance(pos, dict):
            continue
        gid = pos.get("coingecko_id") or pos.get("asset_id")
        qty = pos.get("quantity")
        if gid is None or qty is None:
            missing.append("manual position coingecko_id/quantity")
            continue
        try:
            qty = float(qty)
        except (TypeError, ValueError):
            missing.append(f"numeric quantity for {gid}")
            continue
        positions.append(
            {
                "id": str(gid),
                "label": str(pos.get("symbol") or gid),
                "quantity": qty,
                "source": "manual",
            }
        )
        manual_used = True

    token_specs, token_spec_errors = _erc20_specs(input_data)
    missing.extend(token_spec_errors)
    wallets = input_data.get("wallets") or (
        [] if not input_data.get("wallet") else [input_data.get("wallet")]
    )
    chain = None
    block_number = None
    if wallets:
        if not isinstance(wallets, list):
            return _fail("wallets must be a list")
        try:
            chain = normalize_chain(input_data.get("chain") or "ethereum")
        except ValueError as exc:
            return _fail(str(exc), AnalysisStatus.UNSUPPORTED)
        try:
            pid, rpc, probe, fallbacks = select_rpc_client(chain.key)
            statuses.extend(
                {
                    "provider_id": x["provider_id"],
                    "status": "FAILED_OR_UNAVAILABLE",
                    "detail": x["error"],
                }
                for x in fallbacks
            )
            block = rpc.call("eth_blockNumber")
            block_number = hex_to_int(block.result)
            evidence.append(
                ev(
                    block,
                    pid,
                    "direct_state",
                    {"block_number": block_number},
                    chain.chain_id,
                    block_number,
                    99,
                    "eth_blockNumber",
                )
            )
            total_native = 0.0
            valid_wallets = []
            for wallet in wallets:
                w = _address(wallet)
                if w is None:
                    missing.append(f"valid wallet address: {wallet}")
                    continue
                valid_wallets.append(w)
                bal = rpc.call("eth_getBalance", [w, "latest"])
                wei = hex_to_int(bal.result) or 0
                native = wei / 1e18
                total_native += native
                evidence.append(
                    ev(
                        bal,
                        pid,
                        "direct_state",
                        {
                            "wallet": w,
                            "native_balance": native,
                            "native_symbol": chain.native_symbol,
                        },
                        chain.chain_id,
                        block_number,
                        99,
                        "eth_getBalance",
                    )
                )
            if total_native > 0:
                positions.append(
                    {
                        "id": NATIVE_GECKO[chain.key],
                        "label": chain.native_symbol,
                        "quantity": total_native,
                        "source": "wallet-native-balance",
                    }
                )

            for spec in token_specs:
                for wallet in valid_wallets:
                    try:
                        token_call = rpc.call(
                            "eth_call",
                            [
                                {
                                    "to": spec["contract"],
                                    "data": _balance_of_calldata(wallet),
                                },
                                "latest",
                            ],
                        )
                        raw_balance = hex_to_int(token_call.result)
                        if raw_balance is None:
                            raise ProviderError(
                                "ERC-20 balanceOf returned a non-quantity result",
                                provider_id=pid,
                                code="INVALID_TOKEN_BALANCE",
                            )
                        quantity = raw_balance / (10 ** spec["decimals"])
                        evidence.append(
                            ev(
                                token_call,
                                pid,
                                "direct_token_balance",
                                {
                                    "wallet": wallet,
                                    "token_contract": spec["contract"],
                                    "coingecko_id": spec["id"],
                                    "symbol": spec["label"],
                                    "decimals": spec["decimals"],
                                    "raw_balance": raw_balance,
                                    "quantity": quantity,
                                },
                                chain.chain_id,
                                block_number,
                                96,
                                "eth_call balanceOf(address)",
                            )
                        )
                        if quantity > 0:
                            positions.append(
                                {
                                    "id": spec["id"],
                                    "label": spec["label"],
                                    "quantity": quantity,
                                    "source": "wallet-erc20-balance",
                                }
                            )
                    except ProviderError as exc:
                        warnings.append(
                            f"ERC-20 balance read failed for {spec['label']} at {spec['contract']}: {exc.code}."
                        )
                        missing.append(
                            f"ERC-20 balance for {spec['label']} at {spec['contract']}"
                        )

            statuses.append(
                {
                    "provider_id": pid,
                    "status": "HEALTHY",
                    "latency_ms": round(probe.latency_ms, 2),
                }
            )
            missing.extend(
                [
                    "automatic ERC-20 token discovery outside explicitly supplied contracts",
                    "NFT positions for wallet ingestion",
                    "DeFi protocol positions for wallet ingestion",
                ]
            )
        except ProviderError as exc:
            statuses.append(
                {
                    "provider_id": exc.provider_id,
                    "status": "UNAVAILABLE",
                    "detail": f"{exc.code}: {exc}",
                }
            )
            missing.append("live wallet balances")
    elif token_specs:
        missing.append("wallet address required for ERC-20 balance reads")

    if not positions:
        return EngineResult(
            engine_id=EngineId.F1,
            engine_version="1.2.0",
            status=AnalysisStatus.INSUFFICIENT_DATA,
            risk_score=0,
            data_confidence=0,
            engine_confidence=0,
            severity=Severity.UNKNOWN,
            summary="No usable portfolio positions were available.",
            warnings=["No portfolio value was fabricated."],
            missing_data=sorted(set(missing + ["manual positions or wallet balances"])),
            provider_consensus="UNAVAILABLE",
            provider_status=statuses,
        )

    positions = _aggregate_positions(positions)
    ids = sorted({p["id"] for p in positions})
    try:
        price_call = CoinGeckoClient().simple_price(ids, "usd")
    except ProviderError as exc:
        return EngineResult(
            engine_id=EngineId.F1,
            engine_version="1.2.0",
            status=AnalysisStatus.PROVIDER_UNAVAILABLE,
            risk_score=0,
            data_confidence=35,
            engine_confidence=0,
            severity=Severity.UNKNOWN,
            summary="Portfolio holdings were available but current market valuation could not be obtained.",
            warnings=[f"{exc.code}: {exc}"],
            evidence=evidence,
            missing_data=sorted(set(missing + ["current market prices"])),
            provider_consensus="UNAVAILABLE",
            provider_status=statuses
            + [
                {
                    "provider_id": "coingecko",
                    "status": "UNAVAILABLE",
                    "detail": f"{exc.code}: {exc}",
                }
            ],
        )
    prices = price_call.result if isinstance(price_call.result, dict) else {}
    normalized_prices = {
        k: {
            "usd": v.get("usd"),
            "last_updated_at": v.get("last_updated_at"),
            "usd_24h_change": v.get("usd_24h_change"),
        }
        for k, v in prices.items()
        if isinstance(v, dict)
    }
    market_freshness, market_age, market_observed = _market_freshness(prices, ids)
    evidence.append(
        ev(
            price_call,
            "coingecko",
            "professional_market_reference",
            normalized_prices,
            confidence=90,
            endpoint="GET /api/v3/simple/price",
            freshness=market_freshness,
            observed_at=market_observed,
        )
    )
    statuses.append(
        {
            "provider_id": "coingecko",
            "status": "HEALTHY",
            "latency_ms": round(price_call.latency_ms, 2),
        }
    )
    valued = []
    total = 0.0
    for position in positions:
        row = prices.get(position["id"])
        px = row.get("usd") if isinstance(row, dict) else None
        if px is None:
            missing.append(f"price for {position['id']}")
            continue
        value = float(px) * position["quantity"]
        total += value
        valued.append(
            {
                **position,
                "price_usd": float(px),
                "value_usd": round(value, 6),
            }
        )
    if total <= 0:
        return _fail("Positions were found, but no positive USD portfolio value could be calculated")
    for position in valued:
        position["weight_pct"] = round(100 * position["value_usd"] / total, 4)
    largest = max((p["weight_pct"] for p in valued), default=0.0)
    hhi = sum((p["weight_pct"] / 100) ** 2 for p in valued)
    score = min(100, max(10, largest) + (10 if hhi > 0.5 else 0))
    if largest > 50:
        warnings.append(
            f"Largest valued exposure is {largest:.1f}% of the observed portfolio."
        )
    if manual_used:
        assumptions.append(
            "Manual position quantities are user-supplied and are not independently verified on-chain."
        )
    if token_specs:
        assumptions.append(
            "ERC-20 contract addresses, decimals, symbols and CoinGecko IDs are caller-supplied metadata; balances are read directly on-chain but token identity metadata is not independently discovered."
        )
    if market_freshness in {FreshnessStatus.STALE, FreshnessStatus.EXPIRED}:
        warnings.append(
            "Market reference timestamps are stale; valuation confidence is reduced."
        )
    data_conf = (
        82
        if market_freshness in {FreshnessStatus.LIVE, FreshnessStatus.CURRENT}
        else 72
        if market_freshness == FreshnessStatus.RECENT
        else 60
    )
    return EngineResult(
        engine_id=EngineId.F1,
        engine_version="1.2.0",
        block_reference=block_number,
        status=(
            AnalysisStatus.PARTIAL
            if market_freshness not in {FreshnessStatus.STALE, FreshnessStatus.EXPIRED}
            else AnalysisStatus.STALE_DATA
        ),
        risk_score=round(score, 2),
        data_confidence=data_conf,
        engine_confidence=78 if token_specs else 76,
        severity=_sev(score),
        summary=(
            "F1 valued aggregated manual and directly observed native/ERC-20 wallet holdings with provider market references where available; automatic token discovery, NFT and DeFi positions remain partial."
        ),
        metrics={
            "portfolio_value_usd": round(total, 2),
            "positions": valued,
            "largest_exposure_pct": largest,
            "concentration_hhi": round(hhi, 4),
        },
        warnings=warnings,
        mitigations=(
            [
                "Review concentration and diversify material single-asset exposure where consistent with policy."
            ]
            if largest > 50
            else []
        ),
        evidence=evidence,
        provider_consensus=(
            "MULTI_SOURCE" if len({e.provider for e in evidence}) > 1 else "SINGLE_SOURCE"
        ),
        data_freshness={
            "status": market_freshness.value,
            "price_provider": "coingecko",
            "price_age_seconds": market_age,
            "block_number": block_number,
        },
        missing_data=sorted(set(missing)),
        provider_status=statuses,
        assumptions=assumptions,
    )


def _fail(
    message: str, status: AnalysisStatus = AnalysisStatus.INSUFFICIENT_DATA
) -> EngineResult:
    return EngineResult(
        engine_id=EngineId.F1,
        engine_version="1.2.0",
        status=status,
        risk_score=0,
        data_confidence=0,
        engine_confidence=0,
        severity=Severity.UNKNOWN,
        summary=message,
        warnings=["No portfolio metric was fabricated."],
        missing_data=["valid F1 portfolio input"],
        provider_consensus="UNAVAILABLE",
    )
