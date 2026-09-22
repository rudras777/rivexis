from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ChainConfig:
    key: str
    chain_id: int
    name: str
    native_symbol: str
    alchemy_network: str
    direct_rpc_env: str


CHAINS: dict[str, ChainConfig] = {
    "ethereum": ChainConfig("ethereum", 1, "Ethereum", "ETH", "eth-mainnet", "ETHEREUM_RPC_URL"),
    "base": ChainConfig("base", 8453, "Base", "ETH", "base-mainnet", "BASE_RPC_URL"),
    "arbitrum": ChainConfig("arbitrum", 42161, "Arbitrum One", "ETH", "arb-mainnet", "ARBITRUM_RPC_URL"),
    "optimism": ChainConfig("optimism", 10, "OP Mainnet", "ETH", "opt-mainnet", "OPTIMISM_RPC_URL"),
    "polygon": ChainConfig("polygon", 137, "Polygon PoS", "POL", "polygon-mainnet", "POLYGON_RPC_URL"),
}

ALIASES = {
    "eth": "ethereum",
    "mainnet": "ethereum",
    "ethereum-mainnet": "ethereum",
    "arb": "arbitrum",
    "arbitrum-one": "arbitrum",
    "op": "optimism",
    "op-mainnet": "optimism",
    "matic": "polygon",
}


def normalize_chain(value: str | int | None) -> ChainConfig:
    if value is None:
        return CHAINS["ethereum"]
    if isinstance(value, int):
        for chain in CHAINS.values():
            if chain.chain_id == value:
                return chain
        raise ValueError(f"Unsupported EVM chain id: {value}")
    raw = str(value).strip().lower()
    if raw.isdigit():
        return normalize_chain(int(raw))
    raw = ALIASES.get(raw, raw)
    if raw not in CHAINS:
        raise ValueError(f"Unsupported EVM chain: {value}")
    return CHAINS[raw]
