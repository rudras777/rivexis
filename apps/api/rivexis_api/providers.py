from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any

from rivexis_api.chains import ChainConfig, normalize_chain
from rivexis_api.core.config import settings
from rivexis_api.models.provider import ProviderHealth, ProviderMetadata
from rivexis_api.provider_clients import ProviderError, RpcClientFactory


PROVIDER_DEFS = [
    ("alchemy", "Alchemy", "rpc", ["B1", "B3", "B4"], ["ALCHEMY_API_KEY"], 10),
    ("quicknode", "QuickNode", "rpc", ["B1", "B3", "B4"], ["QUICKNODE_URL"], 20),
    ("direct_rpc", "Direct RPC", "rpc", ["B1", "B3", "B4"], [], 30),
    ("tenderly", "Tenderly", "simulation", ["B1"], ["TENDERLY_ACCESS_KEY", "TENDERLY_ACCOUNT", "TENDERLY_PROJECT"], 10),
    # Retained in the registry for existing deployments, but intentionally not selected by the
    # B1 live path because Alchemy has announced deprecation of this Simulation API on 2026-09-30.
    ("alchemy_sim", "Alchemy Simulation (deprecated 2026-09-30)", "simulation", ["B1"], ["ALCHEMY_API_KEY"], 90),
    ("blockaid", "Blockaid", "security", ["B2", "B3"], ["BLOCKAID_API_KEY"], 10),
    ("hypernative", "Hypernative", "security", ["B2", "B3"], ["HYPERNATIVE_API_KEY"], 20),
    ("dune", "Dune Analytics", "indexer", ["B4"], ["DUNE_API_KEY"], 20),
    ("etherscan", "Etherscan", "explorer", ["B1", "B2", "B4"], ["ETHERSCAN_API_KEY"], 20),
    ("thegraph", "The Graph", "indexer", ["B1", "B4"], ["THEGRAPH_API_KEY"], 30),
    ("nansen", "Nansen", "entity_intelligence", ["B4", "F1", "F5"], ["NANSEN_API_KEY"], 10),
    ("arkham", "Arkham", "entity_intelligence", ["B4", "F1", "F5"], ["ARKHAM_API_KEY"], 20),
    ("lifi", "LI.FI", "route", ["B5"], [], 10),
    ("chainlink", "Chainlink", "oracle", ["B3", "F2", "F3", "F5"], [], 10),
    ("defillama", "DeFiLlama", "protocol_data", ["F1", "F2", "F5"], [], 10),
    ("defillama_yields", "DeFiLlama Yields", "yield_data", ["F4"], [], 10),
    ("coingecko", "CoinGecko", "market_data", ["F1", "F3", "F4", "F5"], [], 20),
    ("coinmarketcap", "CoinMarketCap", "market_data", ["F1", "F3", "F4", "F5"], ["COINMARKETCAP_API_KEY"], 30),
    ("kaiko", "Kaiko", "market_data", ["F1", "F2", "F3", "F5"], ["KAIKO_API_KEY"], 10),
    ("glassnode", "Glassnode", "market_data", ["B4", "F1", "F5"], ["GLASSNODE_API_KEY"], 40),
    ("tokenterminal", "Token Terminal", "protocol_data", ["F2", "F4", "F5"], ["TOKEN_TERMINAL_API_KEY"], 20),
    ("messari", "Messari", "research", ["F2", "F5"], ["MESSARI_API_KEY"], 30),
    ("gauntlet", "Gauntlet", "external_risk", ["F2", "F3", "F5"], ["GAUNTLET_API_KEY"], 10),
    ("chaoslabs", "Chaos Labs", "external_risk", ["F2", "F3", "F5"], ["CHAOS_LABS_API_KEY"], 20),
    ("mock", "Rivexis Demo Adapter", "demo", ["B1", "B2", "B3", "B4", "B5", "F1", "F2", "F3", "F4", "F5"], [], 999),
]


@dataclass
class Adapter:
    metadata: ProviderMetadata

    def configured(self, chain: ChainConfig | None = None) -> bool:
        if self.metadata.provider_id == "mock":
            return settings.enable_demo_adapter
        if self.metadata.provider_id in {"alchemy", "quicknode", "direct_rpc"}:
            target = chain or normalize_chain("ethereum")
            return RpcClientFactory.url(self.metadata.provider_id, target) is not None
        if self.metadata.provider_id == "blockaid":
            return bool(os.getenv("BLOCKAID_API_KEY", "").strip() or os.getenv("BLOCKAID_CLIENT_API_KEY", "").strip())
        if self.metadata.provider_id == "arkham":
            key = bool(os.getenv("ARKHAM_API_KEY", "").strip())
            approved = os.getenv("RIVEXIS_ARKHAM_LICENSE_APPROVED", "false").strip().lower() in {"1", "true", "yes", "on"}
            return key and approved
        return all(bool(os.getenv(k, "").strip()) for k in self.metadata.env_keys) if self.metadata.env_keys else True

    def health(self, deep: bool = False, chain: str | int | None = None) -> ProviderHealth:
        target: ChainConfig | None = None
        if self.metadata.category == "rpc":
            try:
                target = normalize_chain(chain)
            except ValueError as exc:
                return ProviderHealth(provider_id=self.metadata.provider_id, status="UNSUPPORTED", configured=False, detail=str(exc))
        configured = self.configured(target)
        if self.metadata.provider_id == "mock":
            status = "DEMO" if configured else "DISABLED"
            return ProviderHealth(provider_id=self.metadata.provider_id, status=status, configured=configured, detail="Synthetic data only; never live.")
        if not configured:
            if self.metadata.provider_id == "arkham" and os.getenv("ARKHAM_API_KEY", "").strip():
                return ProviderHealth(
                    provider_id=self.metadata.provider_id,
                    status="LICENSE_APPROVAL_REQUIRED",
                    configured=False,
                    detail="API credentials are present, but Rivexis requires explicit operator approval of Arkham API/commercial terms before enabling this adapter.",
                )
            return ProviderHealth(provider_id=self.metadata.provider_id, status="CREDENTIALS_REQUIRED", configured=False)
        if not deep:
            return ProviderHealth(provider_id=self.metadata.provider_id, status="CONFIGURED", configured=True)
        if self.metadata.category != "rpc":
            return ProviderHealth(
                provider_id=self.metadata.provider_id,
                status="CONFIGURED_UNPROBED",
                configured=True,
                detail="No generic network probe is performed for this provider category.",
            )
        assert target is not None
        started = time.perf_counter()
        try:
            rpc = RpcClientFactory.client(self.metadata.provider_id, target)
            chain_call = rpc.call("eth_chainId")
            block_call = rpc.call("eth_blockNumber")
            observed_chain_id = int(chain_call.result, 16)
            block_number = int(block_call.result, 16)
            latency_ms = (time.perf_counter() - started) * 1000
            if observed_chain_id != target.chain_id:
                return ProviderHealth(
                    provider_id=self.metadata.provider_id,
                    status="CHAIN_MISMATCH",
                    configured=True,
                    detail=f"Expected chain_id={target.chain_id}; provider returned {observed_chain_id}.",
                    latency_ms=round(latency_ms, 2),
                    chain_id=observed_chain_id,
                    block_number=block_number,
                )
            return ProviderHealth(
                provider_id=self.metadata.provider_id,
                status="HEALTHY",
                configured=True,
                detail=f"Live JSON-RPC probe succeeded for {target.name}.",
                latency_ms=round(latency_ms, 2),
                chain_id=observed_chain_id,
                block_number=block_number,
            )
        except ProviderError as exc:
            return ProviderHealth(
                provider_id=self.metadata.provider_id,
                status="UNHEALTHY",
                configured=True,
                detail=f"{exc.code}: {exc}",
                latency_ms=round((time.perf_counter() - started) * 1000, 2),
                error_code=exc.code,
            )


ADAPTERS: dict[str, Adapter] = {}
for pid, name, category, engines, keys, priority in PROVIDER_DEFS:
    license_notes = "Review commercial terms before production use."
    if pid == "alchemy_sim":
        license_notes = "Deprecated by provider effective 2026-09-30; retained only for migration visibility."
    if pid == "arkham":
        license_notes = "Disabled until RIVEXIS_ARKHAM_LICENSE_APPROVED=true; review Arkham API/commercial terms for Rivexis use before production enablement."
    meta = ProviderMetadata(
        provider_id=pid,
        provider_name=name,
        category=category,
        supported_engines=engines,
        env_keys=keys,
        provider_priority=priority,
        enabled=True if pid != "mock" else settings.enable_demo_adapter,
        license_notes=license_notes,
    )
    ADAPTERS[pid] = Adapter(meta)


FALLBACKS = {
    "rpc": ["alchemy", "quicknode", "direct_rpc"],
    "simulation": ["tenderly"],
    "security": ["blockaid", "hypernative"],
    "threat": ["hypernative", "blockaid"],
    "indexer": ["dune", "thegraph", "etherscan"],
    "entity_intelligence": ["nansen", "arkham"],
    "route": ["lifi"],
    "protocol_data": ["defillama", "tokenterminal", "messari"],
    "yield_data": ["defillama_yields", "tokenterminal"],
    "market_data": ["kaiko", "coingecko", "coinmarketcap", "glassnode"],
    "external_risk": ["gauntlet", "chaoslabs"],
    "oracle": ["chainlink"],
}


@dataclass
class Resolution:
    category: str
    provider_id: str | None
    status: str
    attempted: list[str]
    detail: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "provider_id": self.provider_id,
            "status": self.status,
            "attempted": self.attempted,
            "detail": self.detail,
        }


def provider_metadata() -> list[ProviderMetadata]:
    return [a.metadata for a in ADAPTERS.values()]


def resolve_provider(category: str, deep: bool = False, allow_demo: bool = False, chain: str | int | None = None) -> Resolution:
    attempted: list[str] = []
    for pid in FALLBACKS.get(category, []):
        attempted.append(pid)
        health = ADAPTERS[pid].health(deep=deep, chain=chain)
        acceptable = health.status in {"CONFIGURED", "CONFIGURED_UNPROBED", "HEALTHY"}
        if acceptable:
            return Resolution(category, pid, "RESOLVED", attempted, health.detail)
    if allow_demo and settings.enable_demo_adapter:
        attempted.append("mock")
        return Resolution(category, "mock", "DEMO", attempted, "Explicit demo fallback selected by caller.")
    return Resolution(category, None, "PROVIDER_UNAVAILABLE", attempted)


def select_rpc_client(chain: str | int | None = None):
    """Select a *working* RPC endpoint, not merely a configured one.

    Returns (provider_id, JsonRpcClient, probe_call, attempted_errors). Demo is never selected.
    """
    target = normalize_chain(chain)
    attempted_errors: list[dict[str, str]] = []
    for pid in FALLBACKS["rpc"]:
        adapter = ADAPTERS[pid]
        if not adapter.configured(target):
            attempted_errors.append({"provider_id": pid, "error": "NOT_CONFIGURED"})
            continue
        try:
            client = RpcClientFactory.client(pid, target)
            probe = client.call("eth_chainId")
            observed = int(probe.result, 16)
            if observed != target.chain_id:
                attempted_errors.append({"provider_id": pid, "error": f"CHAIN_MISMATCH:{observed}"})
                continue
            return pid, client, probe, attempted_errors
        except ProviderError as exc:
            attempted_errors.append({"provider_id": pid, "error": f"{exc.code}:{exc}"})
    raise ProviderError(
        f"No healthy RPC provider is available for {target.name}",
        provider_id="rpc-fallback",
        code="PROVIDER_UNAVAILABLE",
        retryable=True,
    )
