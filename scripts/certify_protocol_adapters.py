#!/usr/bin/env python3
"""Non-mutating certification of Rivexis protocol-native adapters against live RPC.

The script only executes an adapter when its required environment variables are present.
Set RIVEXIS_REQUIRE_PROTOCOL_ADAPTER_CERTIFICATION=true to fail when no adapter is configured
or when any configured adapter cannot be read successfully.
"""
from __future__ import annotations

import os
import sys

from rivexis_api.chains import normalize_chain
from rivexis_api.provider_clients import ProviderError, hex_to_int
from rivexis_api.providers import select_rpc_client
from rivexis_api.services.protocol_adapters import collect_protocol_adapter


def env(name: str) -> str:
    return os.getenv(name, "").strip()


def certify(label: str, data: dict) -> tuple[bool, str]:
    try:
        chain = normalize_chain(data.get("chain") or "ethereum")
        pid, rpc, _, _ = select_rpc_client(chain.key)
        block = hex_to_int(rpc.call("eth_blockNumber").result)
        result = collect_protocol_adapter(data, rpc=rpc, chain_id=chain.chain_id, block_number=block)
        if not result.evidence:
            raise AssertionError("adapter returned no direct evidence")
        if result.adapter == "morpho_blue":
            dep = result.metrics.get("dependency_provenance") or {}
            for key in ("oracle_runtime_code", "irm_runtime_code"):
                value = dep.get(key)
                if value and not value.get("code_present"):
                    raise AssertionError(f"Morpho dependency {key} has no runtime bytecode")
            if result.metrics.get("irm_classification") == "official_adaptive_curve":
                binding = dep.get("irm_morpho_binding") or {}
                if binding.get("matches") is not True:
                    raise AssertionError("Morpho Adaptive Curve IRM binding did not match Morpho core")
                if dep.get("borrow_rate_per_second_wad") is None:
                    raise AssertionError("Morpho Adaptive Curve borrowRateView was unavailable")
        return True, f"{label}: PASS ({pid}; block={block}; evidence={len(result.evidence)}; confidence={result.confidence:.0f})"
    except (ProviderError, ValueError, AssertionError) as exc:
        return False, f"{label}: FAIL - {exc}"


def main() -> None:
    required = env("RIVEXIS_REQUIRE_PROTOCOL_ADAPTER_CERTIFICATION").lower() in {"1", "true", "yes", "on"}
    common_chain = env("RIVEXIS_CERTIFICATION_CHAIN") or "ethereum"
    targets: list[tuple[str, dict]] = []

    if env("RIVEXIS_CERT_AAVE_ASSET"):
        row = {
            "chain": env("RIVEXIS_CERT_AAVE_CHAIN") or common_chain,
            "protocol_adapter": "aave_v3",
            "asset_address": env("RIVEXIS_CERT_AAVE_ASSET"),
        }
        if env("RIVEXIS_CERT_AAVE_DATA_PROVIDER"): row["aave_data_provider"] = env("RIVEXIS_CERT_AAVE_DATA_PROVIDER")
        if env("RIVEXIS_CERT_AAVE_POOL"): row["aave_pool"] = env("RIVEXIS_CERT_AAVE_POOL")
        if env("RIVEXIS_CERT_AAVE_USER"): row["user_address"] = env("RIVEXIS_CERT_AAVE_USER")
        targets.append(("Aave V3", row))

    if env("RIVEXIS_CERT_COMPOUND_ASSET"):
        row = {
            "chain": env("RIVEXIS_CERT_COMPOUND_CHAIN") or common_chain,
            "protocol_adapter": "compound_v3",
            "compound_market": env("RIVEXIS_CERT_COMPOUND_MARKET") or "usdc",
            "collateral_asset": env("RIVEXIS_CERT_COMPOUND_ASSET"),
        }
        if env("RIVEXIS_CERT_COMPOUND_COMET"): row["comet_address"] = env("RIVEXIS_CERT_COMPOUND_COMET")
        if env("RIVEXIS_CERT_COMPOUND_USER"): row["user_address"] = env("RIVEXIS_CERT_COMPOUND_USER")
        targets.append(("Compound III", row))

    if env("RIVEXIS_CERT_MORPHO_MARKET_ID"):
        row = {
            "chain": env("RIVEXIS_CERT_MORPHO_CHAIN") or common_chain,
            "protocol_adapter": "morpho_blue",
            "morpho_market_id": env("RIVEXIS_CERT_MORPHO_MARKET_ID"),
        }
        if env("RIVEXIS_CERT_MORPHO_CONTRACT"): row["morpho_contract"] = env("RIVEXIS_CERT_MORPHO_CONTRACT")
        if env("RIVEXIS_CERT_MORPHO_USER"): row["user_address"] = env("RIVEXIS_CERT_MORPHO_USER")
        targets.append(("Morpho Blue", row))

    cert_at_block = env("RIVEXIS_CERT_AT_BLOCK")
    if cert_at_block:
        for _, target in targets:
            target["at_block"] = cert_at_block

    if not targets:
        if required:
            print("Protocol adapter certification: FAIL - no adapter target configured", file=sys.stderr)
            raise SystemExit(1)
        print("SKIP protocol adapter certification: configure RIVEXIS_CERT_AAVE_*, RIVEXIS_CERT_COMPOUND_*, or RIVEXIS_CERT_MORPHO_*")
        return

    failed = False
    for label, data in targets:
        ok, message = certify(label, data)
        print(message, file=sys.stdout if ok else sys.stderr)
        failed |= not ok
    if failed:
        raise SystemExit(1)
    print(f"Protocol adapter certification: PASS ({len(targets)} adapter target(s))")


if __name__ == "__main__":
    main()
