from __future__ import annotations

from copy import deepcopy
from typing import Any

REGISTRY_VERSION = "2026-09-11-p10"

# Release-reviewed upstream source attestations. GitHub-backed official sources are
# pinned to immutable blob SHAs observed during the Rivexis release review. Official
# documentation that does not expose an immutable revision remains a reviewed
# content snapshot and is not upgraded to cryptographic upstream attestation.
SOURCE_ATTESTATIONS: dict[str, dict[str, Any]] = {
    "aave-v3-ethereum": {
        "attestation_status": "PINNED_UPSTREAM_REVISION",
        "revision_kind": "github_blob_sha",
        "revision": "0e3a3bc385e001d4713d533c9891f3f787df7a67",
        "upstream_files": [{"repository": "aave-dao/aave-address-book", "path": "src/AaveV3Ethereum.sol", "sha": "0e3a3bc385e001d4713d533c9891f3f787df7a67"}],
        "reviewed_at": "2026-09-11",
    },
    "aave-v3-base": {
        "attestation_status": "PINNED_UPSTREAM_REVISION",
        "revision_kind": "github_blob_sha",
        "revision": "704c4f9f7e6acddb6367ebf567a156ec3df0dd0d",
        "upstream_files": [{"repository": "aave-dao/aave-address-book", "path": "src/AaveV3Base.sol", "sha": "704c4f9f7e6acddb6367ebf567a156ec3df0dd0d"}],
        "reviewed_at": "2026-09-11",
    },
    "compound-v3-ethereum-usdc": {
        "attestation_status": "PINNED_UPSTREAM_REVISION",
        "revision_kind": "github_blob_sha_set",
        "revision": {
            "roots.json": "8cdf987c178cd0ba8af8286a4089b70c11bbcf24",
            "configuration.json": "433a0e052c035cbf1979bf645660b4ae31d54549",
        },
        "upstream_files": [
            {"repository": "compound-finance/comet", "path": "deployments/mainnet/usdc/roots.json", "sha": "8cdf987c178cd0ba8af8286a4089b70c11bbcf24"},
            {"repository": "compound-finance/comet", "path": "deployments/mainnet/usdc/configuration.json", "sha": "433a0e052c035cbf1979bf645660b4ae31d54549"},
        ],
        "reviewed_at": "2026-09-11",
    },
    "compound-v3-base-usdc": {
        "attestation_status": "PINNED_UPSTREAM_REVISION",
        "revision_kind": "github_blob_sha_set",
        "revision": {
            "roots.json": "8cbb342769cdf50b2e45b4f757e71e8c65589dfc",
            "configuration.json": "a063b1d99836bc9fd39d9822a8390eeb814600d1",
        },
        "upstream_files": [
            {"repository": "compound-finance/comet", "path": "deployments/base/usdc/roots.json", "sha": "8cbb342769cdf50b2e45b4f757e71e8c65589dfc"},
            {"repository": "compound-finance/comet", "path": "deployments/base/usdc/configuration.json", "sha": "a063b1d99836bc9fd39d9822a8390eeb814600d1"},
        ],
        "reviewed_at": "2026-09-11",
    },
}

# Versioned Rivexis snapshots of official protocol-owned deployment registries.
# These records are evidence of deployment identity only; runtime contract state is
# still read directly from the selected chain RPC at the requested block.
_DEPLOYMENTS: list[dict[str, Any]] = [
    {
        "adapter": "aave_v3", "chain_id": 1, "chain": "ethereum", "deployment_id": "aave-v3-ethereum",
        "contracts": {
            "pool_addresses_provider": "0x2f39d218133afab8f2b819b1066c7e434ad94e9e",
            "pool": "0x87870bca3f3fd6335c3f4ce8392d69350b4fa4e2",
            "pool_configurator": "0x64b761d848206f447fe2dd461b0c635ec39ebb27",
            "oracle": "0x54586be62e3c3580375ae3723c145253060ca0c2",
            "data_provider": "0x0a16f2fcc0d44fae41cc54e079281d84a363becd",
        },
        "source": "Aave DAO address book", "source_kind": "official_protocol_registry",
        "source_ref": "https://github.com/aave-dao/aave-address-book/blob/main/src/AaveV3Ethereum.sol",
    },
    {
        "adapter": "aave_v3", "chain_id": 8453, "chain": "base", "deployment_id": "aave-v3-base",
        "contracts": {
            "pool_addresses_provider": "0xe20fcbd bffc4dd138ce8b2e6fbb6cb49777ad64d".replace(" ", ""),
            "pool": "0xa238dd80c259a72e81d7e4664a9801593f98d1c5",
            "pool_configurator": "0x5731a04b1e775f0fdd454bf70f3335886e9a96be",
            "oracle": "0x2cc0fc26ed4563a5ce5e8bdcfe1a2878676ae156",
            "data_provider": "0x0f43731eb8d45a581f4a36dd74f5f358bc90c73a",
        },
        "source": "Aave DAO address book", "source_kind": "official_protocol_registry",
        "source_ref": "https://github.com/aave-dao/aave-address-book/blob/main/src/AaveV3Base.sol",
    },
    {
        "adapter": "compound_v3", "chain_id": 1, "chain": "ethereum", "deployment_id": "compound-v3-ethereum-usdc", "market": "usdc",
        "contracts": {
            "comet": "0xc3d688b66703497daa19211eedff47f25384cdc3",
            "configurator": "0x316f9708bb98af7da9c68c1c3b5e79039cd336e3",
            "rewards": "0x1b0e765f6224c21223aea2af16c1c46e38885a40",
            "bulker": "0xa397a8c2086c554b531c02e29f3291c9704b00c7",
            "base_token": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
            "base_token_price_feed": "0x8fffffd4afb6115b954bd326cbe7b4ba576818f6",
            "governor": "0x6d903f6003cca6255d85cca4d3b5e5146dc33925",
            "pause_guardian": "0xbbf3f1421d886e9b2c5d716b5192ac998af2012c",
        },
        "source": "Compound Comet deployments", "source_kind": "official_protocol_repository",
        "source_ref": "https://github.com/compound-finance/comet/tree/main/deployments/mainnet/usdc",
    },
    {
        "adapter": "compound_v3", "chain_id": 8453, "chain": "base", "deployment_id": "compound-v3-base-usdc", "market": "usdc",
        "contracts": {
            "comet": "0xb125e6687d4313864e53df431d5425969c15eb2f",
            "configurator": "0x45939657d1ca34a8fa39a924b71d28fe8431e581",
            "rewards": "0x123964802e6ababbe1bc9547d72ef1b69b00a6b1",
            "bulker": "0x78d0677032a35c63d142a48a2037048871212a8c",
        },
        "source": "Compound Comet deployments", "source_kind": "official_protocol_repository",
        "source_ref": "https://github.com/compound-finance/comet/tree/main/deployments/base/usdc",
    },
    {
        "adapter": "morpho_blue", "chain_id": 1, "chain": "ethereum", "deployment_id": "morpho-blue-ethereum",
        "contracts": {"morpho": "0xbbbbbbbbbb9cc5e90e3b3af64bdaf62c37eeffcb", "adaptive_curve_irm": "0x870ac11d48b15db9a138cf899d20f13f79ba00bc", "chainlink_oracle_v2_factory": "0x3a7bb36ee3f3ee32a60e9f2b33c1e5f2e83ad766"},
        "source": "Morpho Docs contract addresses", "source_kind": "official_protocol_documentation", "source_ref": "https://docs.morpho.org/developers/contracts/addresses/",
    },
    {
        "adapter": "morpho_blue", "chain_id": 8453, "chain": "base", "deployment_id": "morpho-blue-base",
        "contracts": {"morpho": "0xbbbbbbbbbb9cc5e90e3b3af64bdaf62c37eeffcb", "adaptive_curve_irm": "0x46415998764c29ab2a25cbea6254146d50d22687", "chainlink_oracle_v2_factory": "0x2dc205f24bcb6b311e5cdf0745b0741648aebd3d"},
        "source": "Morpho Docs contract addresses", "source_kind": "official_protocol_documentation", "source_ref": "https://docs.morpho.org/developers/contracts/addresses/",
    },
    {
        "adapter": "morpho_blue", "chain_id": 42161, "chain": "arbitrum", "deployment_id": "morpho-blue-arbitrum",
        "contracts": {"morpho": "0x6c247b1f6182318877311737bac0844baa518f5e", "adaptive_curve_irm": "0x66f30587fb8d4206918deb78eca7d5ebbafd06da", "chainlink_oracle_v2_factory": "0x98ce5d183dc0c176f54d37162f87e7ed7f2e41b5"},
        "source": "Morpho Docs contract addresses", "source_kind": "official_protocol_documentation", "source_ref": "https://docs.morpho.org/developers/contracts/addresses/",
    },
    {
        "adapter": "morpho_blue", "chain_id": 10, "chain": "optimism", "deployment_id": "morpho-blue-optimism",
        "contracts": {"morpho": "0xce95afbb8ea029495c66020883f87aae8864af92", "adaptive_curve_irm": "0x8cd70a8f399428456b29546bc5dbe10ab6a06ef6", "chainlink_oracle_v2_factory": "0x1ec408d4131686f727f3fd6245cf85bc5c9dad70"},
        "source": "Morpho Docs contract addresses", "source_kind": "official_protocol_documentation", "source_ref": "https://docs.morpho.org/developers/contracts/addresses/",
    },
]

ALIASES = {
    "aave": "aave_v3", "aave-v3": "aave_v3", "aave_v3": "aave_v3",
    "comet": "compound_v3", "compound-iii": "compound_v3", "compound_iii": "compound_v3", "compound_v3": "compound_v3",
    "morpho": "morpho_blue", "morpho-blue": "morpho_blue", "morpho_blue": "morpho_blue",
}


def canonical_adapter(value: Any) -> str:
    return ALIASES.get(str(value or "").strip().lower(), str(value or "").strip().lower())


def list_protocol_deployments(adapter: str | None = None, chain_id: int | None = None) -> list[dict[str, Any]]:
    wanted = canonical_adapter(adapter) if adapter else None
    out = []
    for row in _DEPLOYMENTS:
        if wanted and row["adapter"] != wanted:
            continue
        if chain_id is not None and int(row["chain_id"]) != int(chain_id):
            continue
        item = deepcopy(row)
        item["registry_version"] = REGISTRY_VERSION
        item["verified_on"] = "2026-09-11"
        item["source_attestation"] = deepcopy(SOURCE_ATTESTATIONS.get(
            item["deployment_id"],
            {
                "attestation_status": "REVIEWED_CONTENT_SNAPSHOT",
                "revision_kind": "official_documentation_snapshot",
                "revision": None,
                "reviewed_at": "2026-09-11",
            },
        ))
        out.append(item)
    return out


def _select(adapter: str, chain_id: int, market: str | None = None) -> dict[str, Any] | None:
    rows = list_protocol_deployments(adapter, chain_id)
    if market:
        market = market.strip().lower()
        rows = [r for r in rows if str(r.get("market") or "").lower() == market]
    if len(rows) == 1:
        return rows[0]
    return None


def enrich_protocol_adapter_input(data: dict[str, Any], chain_id: int) -> tuple[dict[str, Any], dict[str, Any]]:
    enriched = dict(data)
    adapter = canonical_adapter(data.get("protocol_adapter") or data.get("protocol_type"))
    market = str(data.get("compound_market") or data.get("market_symbol") or "").strip().lower() or None
    row = _select(adapter, chain_id, market)
    if row is None:
        return enriched, {
            "status": "UNVERIFIED", "adapter": adapter, "chain_id": chain_id,
            "registry_version": REGISTRY_VERSION, "reason": "No unique built-in official deployment record matched this adapter/chain/market.",
        }

    c = row["contracts"]
    key_name = ""
    expected = ""
    supplied = ""
    if adapter == "aave_v3":
        enriched.setdefault("aave_data_provider", c["data_provider"])
        enriched.setdefault("aave_pool", c["pool"])
        enriched.setdefault("aave_oracle", c["oracle"])
        enriched.setdefault("aave_addresses_provider", c["pool_addresses_provider"])
        key_name, expected = "aave_data_provider", c["data_provider"]
        supplied = str(data.get("aave_data_provider") or data.get("pool_data_provider") or expected).lower()
    elif adapter == "compound_v3":
        enriched.setdefault("comet_address", c["comet"])
        enriched.setdefault("compound_configurator", c.get("configurator"))
        enriched.setdefault("compound_governor_expected", c.get("governor"))
        enriched.setdefault("compound_pause_guardian_expected", c.get("pause_guardian"))
        key_name, expected = "comet_address", c["comet"]
        supplied = str(data.get("comet_address") or data.get("market_address") or expected).lower()
    elif adapter == "morpho_blue":
        enriched.setdefault("morpho_contract", c["morpho"])
        enriched.setdefault("morpho_adaptive_curve_irm", c.get("adaptive_curve_irm"))
        enriched.setdefault("morpho_oracle_factory", c.get("chainlink_oracle_v2_factory"))
        key_name, expected = "morpho_contract", c["morpho"]
        supplied = str(data.get("morpho_contract") or expected).lower()

    status = "VERIFIED" if supplied == str(expected).lower() else "MISMATCH"
    return enriched, {
        "status": status, "adapter": adapter, "chain_id": chain_id, "chain": row.get("chain"),
        "deployment_id": row["deployment_id"], "market": row.get("market"),
        "identity_field": key_name, "supplied": supplied, "expected": expected,
        "contracts": c, "source": row["source"], "source_kind": row["source_kind"],
        "source_ref": row["source_ref"], "source_attestation": row.get("source_attestation"),
        "registry_version": REGISTRY_VERSION, "verified_on": row.get("verified_on"),
    }
