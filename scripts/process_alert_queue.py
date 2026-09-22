#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
from rivexis_api.services.alert_delivery import delivery_error_type, delivery_log_summary, process_due_alerts


def main(argv=None):
    parser=argparse.ArgumentParser(description="Process Rivexis durable alert deliveries for one workspace without logging tenant payloads")
    parser.add_argument("workspace_id")
    parser.add_argument("--limit",type=int,default=50)
    args=parser.parse_args(argv)
    try:
        result=process_due_alerts(args.workspace_id,args.limit)
        print(json.dumps({"event":"alert_queue_process","summary":delivery_log_summary([result])},sort_keys=True))
        return 0
    except Exception as exc:
        print(json.dumps({"event":"alert_queue_error","error_type":delivery_error_type(exc)},sort_keys=True))
        return 1


if __name__=="__main__":
    raise SystemExit(main())
