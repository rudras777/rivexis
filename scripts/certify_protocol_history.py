#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'apps'/'api'))

from rivexis_api.services.protocol_history import compare_protocol_configuration, protocol_event_timeline  # noqa:E402


def env(name:str)->str:
    return os.getenv(name,"").strip()


def main()->int:
    required=env("RIVEXIS_REQUIRE_PROTOCOL_HISTORY_CERTIFICATION").lower() in {"1","true","yes"}
    adapter=env("RIVEXIS_CERT_HISTORY_ADAPTER")
    chain=env("RIVEXIS_CERT_HISTORY_CHAIN")
    from_block=env("RIVEXIS_CERT_HISTORY_FROM_BLOCK")
    to_block=env("RIVEXIS_CERT_HISTORY_TO_BLOCK")
    if not all([adapter,chain,from_block,to_block]):
        msg="SKIP protocol history certification: configure RIVEXIS_CERT_HISTORY_ADAPTER/CHAIN/FROM_BLOCK/TO_BLOCK"
        if required:
            print(msg.replace("SKIP","FAIL"),file=sys.stderr);return 2
        print(msg);return 0
    data={"protocol_adapter":adapter,"chain":chain,"from_block":from_block,"to_block":to_block}
    subject=env("RIVEXIS_CERT_HISTORY_SUBJECT")
    market=env("RIVEXIS_CERT_HISTORY_MARKET")
    if adapter in {"aave","aave_v3","aave-v3"} and subject:data["asset_address"]=subject
    elif adapter in {"compound_v3","compound_iii","compound-iii","comet"}:
        if subject:data["collateral_asset"]=subject
        data["compound_market"]=market or "usdc"
    elif adapter in {"morpho","morpho_blue","morpho-blue"} and subject:data["morpho_market_id"]=subject
    try:
        timeline=protocol_event_timeline(data)
        comparison=compare_protocol_configuration(data)
    except Exception as exc:
        print(f"FAIL protocol history certification: {exc}",file=sys.stderr);return 1
    print(json.dumps({
        "status":"PASS","adapter":timeline.get("adapter"),"chain":timeline.get("chain"),
        "from_block":timeline.get("from_block"),"to_block":timeline.get("to_block"),
        "event_count":timeline.get("event_count"),"configuration_change_count":comparison.get("change_count"),
        "materiality_counts":comparison.get("materiality_counts"),
    },indent=2))
    return 0

if __name__=="__main__":raise SystemExit(main())
