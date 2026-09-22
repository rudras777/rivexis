#!/usr/bin/env python3
"""Non-mutating staging certification for credentialed P5 provider adapters.

No provider is contacted unless credentials are configured. Address-based providers also
require RIVEXIS_CERTIFICATION_ADDRESS, preventing the script from inventing a target.
Set RIVEXIS_REQUIRE_LIVE_PROVIDER_CERTIFICATION=true to fail when a configured integration
cannot be certified.
"""
from __future__ import annotations

import os
import sys

from rivexis_api.provider_clients import ArkhamClient, BlockaidClient, NansenClient, ProviderError


def main() -> None:
    address = os.getenv("RIVEXIS_CERTIFICATION_ADDRESS", "").strip().lower()
    chain = os.getenv("RIVEXIS_CERTIFICATION_CHAIN", "ethereum").strip().lower()
    required = os.getenv("RIVEXIS_REQUIRE_LIVE_PROVIDER_CERTIFICATION", "false").lower() in {"1", "true", "yes", "on"}
    failures: list[str] = []
    checks = 0

    blockaid = BlockaidClient()
    if blockaid.configured:
        if not address:
            print("Blockaid certification: SKIP - set RIVEXIS_CERTIFICATION_ADDRESS")
            if required: failures.append("blockaid target missing")
        else:
            checks += 1
            try:
                call = blockaid.scan_address(chain=chain, address=address)
                if not isinstance(call.result, dict): raise AssertionError("response is not an object")
                print("Blockaid certification: PASS")
            except (ProviderError, AssertionError) as exc:
                failures.append(f"Blockaid: {exc}")

    nansen = NansenClient()
    if nansen.configured:
        if not address:
            print("Nansen certification: SKIP - set RIVEXIS_CERTIFICATION_ADDRESS")
            if required: failures.append("nansen target missing")
        else:
            checks += 1
            try:
                call = nansen.address_labels(address=address, chain=chain)
                if not isinstance(call.result, dict): raise AssertionError("response is not an object")
                print("Nansen certification: PASS")
            except (ProviderError, AssertionError) as exc:
                failures.append(f"Nansen: {exc}")

    arkham = ArkhamClient()
    if arkham.credentialed and not arkham.license_approved:
        print("Arkham certification: BLOCKED - set RIVEXIS_ARKHAM_LICENSE_APPROVED=true only after terms are approved")
        if required: failures.append("arkham license approval missing")
    elif arkham.configured:
        if not address:
            print("Arkham certification: SKIP - set RIVEXIS_CERTIFICATION_ADDRESS")
            if required: failures.append("arkham target missing")
        else:
            checks += 1
            try:
                call = arkham.address_intelligence(address)
                if not isinstance(call.result, dict): raise AssertionError("response is not an object")
                print("Arkham certification: PASS")
            except (ProviderError, AssertionError) as exc:
                failures.append(f"Arkham: {exc}")

    if os.getenv("HYPERNATIVE_API_KEY", "").strip():
        print("Hypernative certification: SCHEMA_REQUIRED - customer endpoint/schema must be certified from the deployment's licensed Hypernative documentation")
        if required: failures.append("hypernative certified customer adapter not configured")

    if failures:
        print("Live provider certification: FAIL - " + "; ".join(failures), file=sys.stderr)
        raise SystemExit(1)
    if checks == 0:
        print("SKIP live provider certification: no certifiable credentialed P5 provider + target configured")
    else:
        print(f"Live provider certification: PASS ({checks} provider probe(s))")


if __name__ == "__main__":
    main()
