from __future__ import annotations
import json
import os
import time
from rivexis_api.services.db import init_db, validate_alert_worker_database_role
from rivexis_api.services.alert_delivery import delivery_error_type, delivery_log_summary, process_due_alerts
from rivexis_api.services.store import due_alert_workspace_ids


def run_once():
    limit=int(os.getenv("RIVEXIS_ALERT_WORKER_WORKSPACE_LIMIT","100"))
    batch=int(os.getenv("RIVEXIS_ALERT_WORKER_BATCH_SIZE","50"))
    results=[]
    for workspace_id in due_alert_workspace_ids(limit):
        result=process_due_alerts(workspace_id,batch)
        results.append(result)
    return results


def _emit_cycle_log(results):
    print(json.dumps({"event":"alert_worker_cycle","summary":delivery_log_summary(results)},sort_keys=True),flush=True)


def _emit_error_log(exc):
    print(json.dumps({"event":"alert_worker_error","error_type":delivery_error_type(exc)},sort_keys=True),flush=True)


def main():
    init_db()
    validation=validate_alert_worker_database_role()
    print(json.dumps({"event":"alert_worker_database_role_validated","validation":validation},default=str),flush=True)
    poll=max(1.0,float(os.getenv("RIVEXIS_ALERT_WORKER_POLL_SECONDS","5")))
    while True:
        try:
            results=run_once()
            summary=delivery_log_summary(results)
            if summary["processed"] or summary["configuration_degraded"]:
                _emit_cycle_log(results)
        except Exception as exc:
            _emit_error_log(exc)
        time.sleep(poll)

if __name__=="__main__": main()
