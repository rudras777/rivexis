from __future__ import annotations

from datetime import datetime, timezone
from math import isfinite
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
        calculation_version="f1-live-1.3.0",
        engine_version="1.2.0",
        confidence=confidence,
        freshness=freshness,
        license_classification="external-provider-evidence",
    )


def _finite_number(value: object) -> float | None:
    if value in (None, "") or isinstance(value, bool):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if isfinite(parsed) else None


def _rpc_quantity(value: object) -> int | None:
    if value in (None, "") or isinstance(value, bool):
        return None
    try:
        parsed = hex_to_int(value)
    except (TypeError, ValueError):
        return None
    if parsed is None or parsed < 0:
        return None
    return parsed


def _block_tag(block_number: int) -> str:
    return hex(block_number)


def _market_freshness(prices: dict[str, Any], ids: list[str]):
    now = datetime.now(timezone.utc)
    now_ts = now.timestamp()
    stamps: list[float] = []
    for cid in ids:
        row = prices.get(cid)
        raw = row.get("last_updated_at") if isinstance(row, dict) else None
        parsed = _finite_number(raw)
        # Freshness is an all-requested-assets contract. One missing/corrupt or
        # materially future observation timestamp means the aggregate is UNKNOWN.
        if parsed is None or parsed <= 0 or parsed > now_ts + 300:
            return FreshnessStatus.UNKNOWN, None, now
        stamps.append(parsed)
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
    """Aggregate one economic exposure before concentration scoring."""

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
        row["quantity"] += float(position["quantity"])
        source = str(position.get("source") or "unknown")
        if source not in row["sources"]:
            row["sources"].append(source)
    return [row for row in grouped.values() if row["quantity"] > 0]


def _erc20_specs(input_data: dict[str, Any]) -> tuple[list[dict[str, Any]], str | None]:
    raw = input_data.get("erc20_tokens") or input_data.get("token_contracts") or []
    if raw and not isinstance(raw, list):
        return [], "erc20_tokens must be a list"
    specs: list[dict[str, Any]] = []
    seen_contracts: dict[str, tuple[str, int]] = {}
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            return [], f"ERC-20 token descriptor at index {index} must be an object"
        contract = _address(item.get("contract_address") or item.get("contract"))
        asset_id = str(item.get("coingecko_id") or item.get("asset_id") or "").strip()
        decimals = item.get("decimals")
        if contract is None or not asset_id or decimals is None:
            return [], f"ERC-20 descriptor {index} requires contract_address, coingecko_id, and decimals"
        if isinstance(decimals, bool):
            return [], f"ERC-20 decimals for {asset_id} must be an integer"
        try:
            decimals = int(decimals)
        except (TypeError, ValueError):
            return [], f"ERC-20 decimals for {asset_id} must be an integer"
        if decimals < 0 or decimals > 36:
            return [], f"ERC-20 decimals for {asset_id} must be between 0 and 36"
        identity = (asset_id, decimals)
        previous = seen_contracts.get(contract)
        if previous is not None:
            if previous != identity:
                return [], f"ERC-20 contract {contract} has conflicting asset identity/decimals descriptors"
            continue
        seen_contracts[contract] = identity
        specs.append(
            {
                "contract": contract,
                "id": asset_id,
                "label": str(item.get("symbol") or asset_id),
                "decimals": decimals,
            }
        )
    return specs, None


def _requested_wallets(input_data: dict[str, Any]) -> tuple[list[str], str | None]:
    raw = input_data.get("wallets")
    if raw is None:
        raw = [] if input_data.get("wallet") in (None, "") else [input_data.get("wallet")]
    if not isinstance(raw, list):
        return [], "wallets must be a list"
    wallets: list[str] = []
    for index, value in enumerate(raw):
        wallet = _address(value)
        if wallet is None:
            return [], f"wallet at index {index} must be a valid EVM address"
        if wallet not in wallets:
            wallets.append(wallet)
    return wallets, None


def _provider_unavailable(
    *,
    summary: str,
    warnings: list[str],
    missing: list[str],
    evidence: list[EvidenceRecord],
    statuses: list[dict[str, Any]],
    provider_id: str,
    code: str,
) -> EngineResult:
    return EngineResult(
        engine_id=EngineId.F1,
        engine_version="1.2.0",
        status=AnalysisStatus.PROVIDER_UNAVAILABLE,
        risk_score=0,
        data_confidence=0,
        engine_confidence=0,
        severity=Severity.UNKNOWN,
        summary=summary,
        warnings=warnings,
        evidence=evidence,
        missing_data=sorted(set(missing)),
        provider_consensus="UNAVAILABLE",
        provider_status=statuses + [{"provider_id": provider_id, "status": code}],
        demo=False,
    )


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
    for index, pos in enumerate(manual):
        if not isinstance(pos, dict):
            return _fail(f"manual position at index {index} must be an object")
        gid = str(pos.get("coingecko_id") or pos.get("asset_id") or "").strip()
        qty = _finite_number(pos.get("quantity"))
        if not gid:
            return _fail(f"manual position at index {index} requires coingecko_id/asset_id")
        if qty is None:
            return _fail(f"manual position quantity for {gid} must be a finite number")
        if qty < 0:
            return _fail(f"manual position quantity for {gid} cannot be negative")
        manual_used = True
        if qty == 0:
            continue
        positions.append(
            {
                "id": gid,
                "label": str(pos.get("symbol") or gid),
                "quantity": qty,
                "source": "manual",
            }
        )

    token_specs, token_spec_error = _erc20_specs(input_data)
    if token_spec_error:
        return _fail(token_spec_error)
    wallets, wallet_error = _requested_wallets(input_data)
    if wallet_error:
        return _fail(wallet_error)
    if token_specs and not wallets:
        return _fail("wallet address is required for explicitly requested ERC-20 balance reads")

    chain = None
    block_number = None
    if wallets:
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
            block_number = _rpc_quantity(block.result)
            if block_number is None:
                raise ProviderError(
                    "RPC returned a malformed block number",
                    provider_id=pid,
                    code="MALFORMED_RESPONSE",
                )
            block_tag = _block_tag(block_number)
            evidence.append(
                ev(
                    block,
                    pid,
                    "direct_state",
                    {"block_number": block_number, "block_tag": block_tag},
                    chain.chain_id,
                    block_number,
                    99,
                    "eth_blockNumber",
                )
            )

            total_native = 0.0
            for wallet in wallets:
                bal = rpc.call("eth_getBalance", [wallet, block_tag])
                wei = _rpc_quantity(bal.result)
                if wei is None:
                    raise ProviderError(
                        "RPC returned a malformed native balance",
                        provider_id=pid,
                        code="MALFORMED_RESPONSE",
                    )
                native = wei / 1e18
                total_native += native
                evidence.append(
                    ev(
                        bal,
                        pid,
                        "direct_state",
                        {
                            "wallet": wallet,
                            "native_balance": native,
                            "native_symbol": chain.native_symbol,
                            "block_tag": block_tag,
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
                for wallet in wallets:
                    token_call = rpc.call(
                        "eth_call",
                        [
                            {
                                "to": spec["contract"],
                                "data": _balance_of_calldata(wallet),
                            },
                            block_tag,
                        ],
                    )
                    raw_balance = _rpc_quantity(token_call.result)
                    if raw_balance is None:
                        raise ProviderError(
                            "ERC-20 balanceOf returned a malformed quantity",
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
                                "block_tag": block_tag,
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

            statuses.append(
                {
                    "provider_id": pid,
                    "status": "HEALTHY",
                    "latency_ms": round(probe.latency_ms, 2),
                }
            )
            assumptions.append(
                f"All direct wallet and ERC-20 balance reads were pinned to captured RPC block {block_tag} ({block_number})."
            )
            missing.extend(
                [
                    "automatic ERC-20 token discovery outside explicitly supplied contracts",
                    "NFT positions for wallet ingestion",
                    "DeFi protocol positions for wallet ingestion",
                ]
            )
        except ProviderError as exc:
            return _provider_unavailable(
                summary="One or more explicitly requested wallet/token holdings could not be observed; Rivexis did not score an incomplete portfolio.",
                warnings=[f"{exc.code}: {exc}"],
                missing=[*missing, "complete explicitly requested wallet/token balance evidence"],
                evidence=evidence,
                statuses=statuses,
                provider_id=exc.provider_id,
                code=exc.code,
            )

    if not positions:
        return EngineResult(
            engine_id=EngineId.F1,
            engine_version="1.2.0",
            status=AnalysisStatus.INSUFFICIENT_DATA,
            risk_score=0,
            data_confidence=0,
            engine_confidence=0,
            severity=Severity.UNKNOWN,
            summary="No positive portfolio positions were available.",
            warnings=["No portfolio value was fabricated."],
            missing_data=sorted(set(missing + ["positive manual positions or wallet balances"])),
            provider_consensus="UNAVAILABLE",
            provider_status=statuses,
            demo=False,
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
            demo=False,
        )

    if not isinstance(price_call.result, dict):
        return EngineResult(
            engine_id=EngineId.F1,
            engine_version="1.2.0",
            status=AnalysisStatus.PROVIDER_UNAVAILABLE,
            risk_score=0,
            data_confidence=0,
            engine_confidence=0,
            severity=Severity.UNKNOWN,
            summary="Market-reference provider returned an unusable payload; no portfolio valuation was produced.",
            warnings=["CoinGecko response was not an object."],
            evidence=evidence,
            missing_data=sorted(set(missing + ["usable market-reference payload"])),
            provider_consensus="UNAVAILABLE",
            provider_status=statuses + [{"provider_id": "coingecko", "status": "MALFORMED_RESPONSE"}],
            demo=False,
        )
    prices = price_call.result

    normalized_prices: dict[str, dict[str, Any]] = {}
    invalid_price_ids: list[str] = []
    for cid in ids:
        row = prices.get(cid)
        px = _finite_number(row.get("usd")) if isinstance(row, dict) else None
        if px is None or px <= 0:
            invalid_price_ids.append(cid)
        normalized_prices[cid] = {
            "usd": px,
            "last_updated_at": _finite_number(row.get("last_updated_at")) if isinstance(row, dict) else None,
            "usd_24h_change": _finite_number(row.get("usd_24h_change")) if isinstance(row, dict) else None,
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
            "status": "HEALTHY" if not invalid_price_ids else "INCOMPLETE_RESPONSE",
            "latency_ms": round(price_call.latency_ms, 2),
        }
    )

    if invalid_price_ids:
        return EngineResult(
            engine_id=EngineId.F1,
            engine_version="1.2.0",
            status=AnalysisStatus.INSUFFICIENT_DATA,
            risk_score=0,
            data_confidence=30,
            engine_confidence=0,
            severity=Severity.UNKNOWN,
            summary="Portfolio concentration cannot be scored because one or more observed exposures lack a positive finite market price.",
            warnings=["Rivexis did not silently exclude an unvalued exposure from portfolio weights."],
            evidence=evidence,
            missing_data=sorted(set(missing + [f"positive finite market price for: {', '.join(invalid_price_ids)}"])),
            provider_consensus=("MULTI_SOURCE" if len({e.provider for e in evidence}) > 1 else "SINGLE_SOURCE"),
            provider_status=statuses,
            data_freshness={
                "status": market_freshness.value,
                "price_provider": "coingecko",
                "price_age_seconds": market_age,
                "block_number": block_number,
            },
            demo=False,
        )

    valued = []
    total = 0.0
    for position in positions:
        px = normalized_prices[position["id"]]["usd"]
        value = float(px) * position["quantity"]
        # px and quantity have already passed finite/positive validation, so this
        # is defensive against unexpected floating-point overflow.
        if not isfinite(value) or value <= 0:
            return _fail(f"Position value for {position['id']} is not a positive finite number")
        total += value
        valued.append(
            {
                **position,
                "price_usd": float(px),
                "value_usd": round(value, 6),
            }
        )
    if not isfinite(total) or total <= 0:
        return _fail("Positions were found, but no positive finite USD portfolio value could be calculated")

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
    elif market_freshness == FreshnessStatus.UNKNOWN:
        warnings.append(
            "One or more market-reference observation timestamps are missing, invalid or materially future-dated; freshness is UNKNOWN."
        )
        assumptions.append(
            "HTTP retrieval time is not treated as proof that all market-reference observations are current."
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
            "F1 valued aggregated manual and fully observed requested native/ERC-20 wallet holdings with provider market references; automatic token discovery, NFT and DeFi positions remain partial."
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
        demo=False,
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
        demo=False,
    )
